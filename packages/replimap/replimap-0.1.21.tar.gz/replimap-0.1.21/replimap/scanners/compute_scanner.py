"""
Compute Scanner for RepliMap Phase 2.

Scans Launch Templates, Auto Scaling Groups, Load Balancers, and Target Groups.
These resources provide scalable compute infrastructure.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import DependencyType, ResourceNode, ResourceType

from .base import BaseScanner, ScannerRegistry

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


@ScannerRegistry.register
class ComputeScanner(BaseScanner):
    """
    Scans compute scaling resources.

    Dependency chain:
        Launch Template <- ASG
        VPC <- ALB/NLB
        Subnet <- ALB/NLB
        ALB/NLB <- Listener -> Target Group
        Security Group <- ALB/NLB
    """

    resource_types: ClassVar[list[str]] = [
        "aws_launch_template",
        "aws_autoscaling_group",
        "aws_lb",
        "aws_lb_listener",
        "aws_lb_target_group",
    ]

    # LBs and ASGs reference VPC resources for dependency edges
    depends_on_types: ClassVar[list[str]] = [
        "aws_vpc",
        "aws_subnet",
        "aws_security_group",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all compute resources and add to graph.

        Each resource type is scanned independently with its own error handling.
        This ensures partial success - if one resource type fails (e.g., due to
        IAM permissions), others will still be scanned.
        """
        logger.info(f"Scanning compute resources in {self.region}...")

        # Define scan steps - each wrapped independently for resilience
        scan_steps = [
            (self._scan_launch_templates, "Launch Templates"),
            (self._scan_target_groups, "Target Groups"),
            (self._scan_load_balancers, "Load Balancers"),
            (self._scan_listeners, "Listeners"),
            (self._scan_autoscaling_groups, "Auto Scaling Groups"),
        ]

        for scan_func, resource_name in scan_steps:
            try:
                scan_func(graph)
            except ClientError as e:
                # Log error but continue to next resource type
                self._handle_aws_error(e, resource_name)
                logger.warning(f"Continuing scan despite {resource_name} failure")

    def _scan_launch_templates(self, graph: GraphEngine) -> None:
        """Scan all Launch Templates in the region."""
        logger.debug("Scanning Launch Templates...")
        ec2 = self.get_client("ec2")

        paginator = ec2.get_paginator("describe_launch_templates")
        for page in paginator.paginate():
            for lt in page.get("LaunchTemplates", []):
                lt_id = lt["LaunchTemplateId"]
                lt_name = lt["LaunchTemplateName"]
                tags = self._extract_tags(lt.get("Tags"))

                # Get latest version details
                version_resp = ec2.describe_launch_template_versions(
                    LaunchTemplateId=lt_id,
                    Versions=["$Latest"],
                )
                versions = version_resp.get("LaunchTemplateVersions", [])
                lt_data = versions[0].get("LaunchTemplateData", {}) if versions else {}

                # Extract security group IDs
                sg_ids = lt_data.get("SecurityGroupIds", [])
                network_interfaces = lt_data.get("NetworkInterfaces", [])
                for ni in network_interfaces:
                    sg_ids.extend(ni.get("Groups", []))

                node = ResourceNode(
                    id=lt_id,
                    resource_type=ResourceType.LAUNCH_TEMPLATE,
                    region=self.region,
                    config={
                        "name": lt_name,
                        "default_version": lt.get("DefaultVersionNumber"),
                        "latest_version": lt.get("LatestVersionNumber"),
                        "instance_type": lt_data.get("InstanceType"),
                        "image_id": lt_data.get("ImageId"),
                        "key_name": lt_data.get("KeyName"),
                        "security_group_ids": list(set(sg_ids)),
                        "iam_instance_profile": lt_data.get("IamInstanceProfile", {}),
                        "user_data": lt_data.get("UserData"),
                        "block_device_mappings": lt_data.get("BlockDeviceMappings", []),
                        "network_interfaces": network_interfaces,
                        "monitoring": lt_data.get("Monitoring", {}),
                    },
                    arn=f"arn:aws:ec2:{self.region}::launch-template/{lt_id}",
                    tags=tags,
                )

                graph.add_resource(node)

                # Add dependencies on security groups
                for sg_id in sg_ids:
                    if graph.get_resource(sg_id):
                        graph.add_dependency(lt_id, sg_id, DependencyType.USES)

                logger.debug(f"Added Launch Template: {lt_name}")

    def _scan_target_groups(self, graph: GraphEngine) -> None:
        """Scan all Target Groups in the region."""
        logger.debug("Scanning Target Groups...")
        elbv2 = self.get_client("elbv2")

        paginator = elbv2.get_paginator("describe_target_groups")
        for page in paginator.paginate():
            for tg in page.get("TargetGroups", []):
                tg_arn = tg["TargetGroupArn"]
                tg_name = tg["TargetGroupName"]
                vpc_id = tg.get("VpcId")

                # Get tags
                tags_resp = elbv2.describe_tags(ResourceArns=[tg_arn])
                tags = {}
                for tag_desc in tags_resp.get("TagDescriptions", []):
                    if tag_desc["ResourceArn"] == tg_arn:
                        tags = self._extract_tags(tag_desc.get("Tags"))

                # Get registered targets for this target group
                targets: list[dict[str, Any]] = []
                try:
                    target_health_resp = elbv2.describe_target_health(
                        TargetGroupArn=tg_arn
                    )
                    for th in target_health_resp.get("TargetHealthDescriptions", []):
                        target = th.get("Target", {})
                        targets.append(
                            {
                                "id": target.get("Id"),
                                "port": target.get("Port"),
                                "availability_zone": target.get("AvailabilityZone"),
                                "health_state": th.get("TargetHealth", {}).get("State"),
                            }
                        )
                except ClientError as e:
                    logger.debug(f"Could not get targets for {tg_name}: {e}")

                node = ResourceNode(
                    id=tg_arn,
                    resource_type=ResourceType.LB_TARGET_GROUP,
                    region=self.region,
                    config={
                        "name": tg_name,
                        "vpc_id": vpc_id,
                        "protocol": tg.get("Protocol"),
                        "port": tg.get("Port"),
                        "target_type": tg.get("TargetType"),
                        "targets": targets,
                        "health_check": {
                            "enabled": tg.get("HealthCheckEnabled"),
                            "protocol": tg.get("HealthCheckProtocol"),
                            "port": tg.get("HealthCheckPort"),
                            "path": tg.get("HealthCheckPath"),
                            "interval_seconds": tg.get("HealthCheckIntervalSeconds"),
                            "timeout_seconds": tg.get("HealthCheckTimeoutSeconds"),
                            "healthy_threshold": tg.get("HealthyThresholdCount"),
                            "unhealthy_threshold": tg.get("UnhealthyThresholdCount"),
                            "matcher": tg.get("Matcher"),
                        },
                        "load_balancing_algorithm_type": tg.get(
                            "LoadBalancingAlgorithmType"
                        ),
                    },
                    arn=tg_arn,
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependency: Target Group -> VPC
                if vpc_id and graph.get_resource(vpc_id):
                    graph.add_dependency(tg_arn, vpc_id, DependencyType.BELONGS_TO)

                logger.debug(f"Added Target Group: {tg_name}")

    def _scan_load_balancers(self, graph: GraphEngine) -> None:
        """Scan all Application and Network Load Balancers in the region."""
        logger.debug("Scanning Load Balancers...")
        elbv2 = self.get_client("elbv2")

        paginator = elbv2.get_paginator("describe_load_balancers")
        for page in paginator.paginate():
            for lb in page.get("LoadBalancers", []):
                lb_arn = lb["LoadBalancerArn"]
                lb_name = lb["LoadBalancerName"]
                vpc_id = lb.get("VpcId")

                # Get tags
                tags_resp = elbv2.describe_tags(ResourceArns=[lb_arn])
                tags = {}
                for tag_desc in tags_resp.get("TagDescriptions", []):
                    if tag_desc["ResourceArn"] == lb_arn:
                        tags = self._extract_tags(tag_desc.get("Tags"))

                # Extract subnet IDs and security groups
                subnet_ids = [az["SubnetId"] for az in lb.get("AvailabilityZones", [])]
                sg_ids = lb.get("SecurityGroups", [])

                node = ResourceNode(
                    id=lb_arn,
                    resource_type=ResourceType.LB,
                    region=self.region,
                    config={
                        "name": lb_name,
                        "vpc_id": vpc_id,
                        "type": lb.get("Type"),
                        "scheme": lb.get("Scheme"),
                        "dns_name": lb.get("DNSName"),
                        "ip_address_type": lb.get("IpAddressType"),
                        "subnet_ids": subnet_ids,
                        "security_group_ids": sg_ids,
                        "availability_zones": [
                            {
                                "zone_name": az["ZoneName"],
                                "subnet_id": az["SubnetId"],
                            }
                            for az in lb.get("AvailabilityZones", [])
                        ],
                    },
                    arn=lb_arn,
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependencies
                if vpc_id and graph.get_resource(vpc_id):
                    graph.add_dependency(lb_arn, vpc_id, DependencyType.BELONGS_TO)

                for subnet_id in subnet_ids:
                    if graph.get_resource(subnet_id):
                        graph.add_dependency(
                            lb_arn, subnet_id, DependencyType.BELONGS_TO
                        )

                for sg_id in sg_ids:
                    if graph.get_resource(sg_id):
                        graph.add_dependency(lb_arn, sg_id, DependencyType.USES)

                logger.debug(f"Added Load Balancer: {lb_name} ({lb.get('Type')})")

    def _scan_listeners(self, graph: GraphEngine) -> None:
        """Scan all Load Balancer Listeners in the region."""
        logger.debug("Scanning LB Listeners...")
        elbv2 = self.get_client("elbv2")

        # Get all LBs first
        lb_arns = [r.id for r in graph.get_resources_by_type(ResourceType.LB)]

        for lb_arn in lb_arns:
            try:
                paginator = elbv2.get_paginator("describe_listeners")
                for page in paginator.paginate(LoadBalancerArn=lb_arn):
                    for listener in page.get("Listeners", []):
                        listener_arn = listener["ListenerArn"]

                        # Process default actions
                        default_actions = []
                        for action in listener.get("DefaultActions", []):
                            action_config: dict[str, Any] = {
                                "type": action.get("Type"),
                                "order": action.get("Order"),
                            }
                            if action.get("TargetGroupArn"):
                                action_config["target_group_arn"] = action[
                                    "TargetGroupArn"
                                ]
                            if action.get("RedirectConfig"):
                                action_config["redirect"] = action["RedirectConfig"]
                            if action.get("FixedResponseConfig"):
                                action_config["fixed_response"] = action[
                                    "FixedResponseConfig"
                                ]
                            if action.get("ForwardConfig"):
                                action_config["forward"] = action["ForwardConfig"]
                            default_actions.append(action_config)

                        node = ResourceNode(
                            id=listener_arn,
                            resource_type=ResourceType.LB_LISTENER,
                            region=self.region,
                            config={
                                "load_balancer_arn": lb_arn,
                                "port": listener.get("Port"),
                                "protocol": listener.get("Protocol"),
                                "ssl_policy": listener.get("SslPolicy"),
                                "certificate_arn": (
                                    listener.get("Certificates", [{}])[0].get(
                                        "CertificateArn"
                                    )
                                    if listener.get("Certificates")
                                    else None
                                ),
                                "default_actions": default_actions,
                            },
                            arn=listener_arn,
                            tags={},  # Listeners don't have tags directly
                        )

                        graph.add_resource(node)

                        # Establish dependency: Listener -> LB
                        graph.add_dependency(
                            listener_arn, lb_arn, DependencyType.BELONGS_TO
                        )

                        # Add dependencies on target groups
                        for action in default_actions:
                            tg_arn = action.get("target_group_arn")
                            if tg_arn and graph.get_resource(tg_arn):
                                graph.add_dependency(
                                    listener_arn, tg_arn, DependencyType.REFERENCES
                                )

                        logger.debug(
                            f"Added Listener: {listener.get('Protocol')}:{listener.get('Port')}"
                        )
            except ClientError as e:
                if e.response["Error"]["Code"] == "LoadBalancerNotFound":
                    continue
                raise

    def _scan_autoscaling_groups(self, graph: GraphEngine) -> None:
        """Scan all Auto Scaling Groups in the region."""
        logger.debug("Scanning Auto Scaling Groups...")
        autoscaling = self.get_client("autoscaling")

        paginator = autoscaling.get_paginator("describe_auto_scaling_groups")
        for page in paginator.paginate():
            for asg in page.get("AutoScalingGroups", []):
                asg_name = asg["AutoScalingGroupName"]
                asg_arn = asg["AutoScalingGroupARN"]

                # Extract launch template info
                lt_info = asg.get("LaunchTemplate", {})
                mixed_policy = asg.get("MixedInstancesPolicy", {})
                if mixed_policy:
                    lt_spec = mixed_policy.get("LaunchTemplate", {})
                    lt_info = lt_spec.get("LaunchTemplateSpecification", {})

                # Get subnet IDs from VPC zone identifier
                vpc_zone_id = asg.get("VPCZoneIdentifier", "")
                subnet_ids = vpc_zone_id.split(",") if vpc_zone_id else []

                # Get target group ARNs
                target_group_arns = asg.get("TargetGroupARNs", [])

                tags = {tag["Key"]: tag["Value"] for tag in asg.get("Tags", [])}

                node = ResourceNode(
                    id=asg_arn,
                    resource_type=ResourceType.AUTOSCALING_GROUP,
                    region=self.region,
                    config={
                        "name": asg_name,
                        "launch_template": {
                            "id": lt_info.get("LaunchTemplateId"),
                            "name": lt_info.get("LaunchTemplateName"),
                            "version": lt_info.get("Version"),
                        },
                        "min_size": asg.get("MinSize"),
                        "max_size": asg.get("MaxSize"),
                        "desired_capacity": asg.get("DesiredCapacity"),
                        "default_cooldown": asg.get("DefaultCooldown"),
                        "availability_zones": asg.get("AvailabilityZones", []),
                        "subnet_ids": subnet_ids,
                        "health_check_type": asg.get("HealthCheckType"),
                        "health_check_grace_period": asg.get("HealthCheckGracePeriod"),
                        "target_group_arns": target_group_arns,
                        "termination_policies": asg.get("TerminationPolicies", []),
                        "new_instances_protected_from_scale_in": asg.get(
                            "NewInstancesProtectedFromScaleIn"
                        ),
                        "service_linked_role_arn": asg.get("ServiceLinkedRoleARN"),
                    },
                    arn=asg_arn,
                    tags=tags,
                )

                graph.add_resource(node)

                # Establish dependencies
                lt_id = lt_info.get("LaunchTemplateId")
                if lt_id and graph.get_resource(lt_id):
                    graph.add_dependency(asg_arn, lt_id, DependencyType.USES)

                for subnet_id in subnet_ids:
                    if subnet_id and graph.get_resource(subnet_id):
                        graph.add_dependency(
                            asg_arn, subnet_id, DependencyType.BELONGS_TO
                        )

                for tg_arn in target_group_arns:
                    if graph.get_resource(tg_arn):
                        graph.add_dependency(asg_arn, tg_arn, DependencyType.REFERENCES)

                logger.debug(f"Added Auto Scaling Group: {asg_name}")
