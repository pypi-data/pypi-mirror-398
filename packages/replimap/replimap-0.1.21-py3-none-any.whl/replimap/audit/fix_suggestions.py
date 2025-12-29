"""
Terraform Fix Suggestions for Common Checkov Findings.

Provides remediation code snippets for security misconfigurations.
"""

from __future__ import annotations

# Fix suggestions for common Checkov checks
FIX_SUGGESTIONS: dict[str, str] = {
    # S3 Bucket Security
    "CKV_AWS_19": """# Enable S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}""",
    "CKV_AWS_18": """# Enable S3 bucket versioning
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}""",
    "CKV_AWS_21": """# Enable S3 bucket logging
resource "aws_s3_bucket_logging" "this" {
  bucket        = aws_s3_bucket.this.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/"
}""",
    "CKV_AWS_20": """# Enforce SSL-only access to S3 bucket
resource "aws_s3_bucket_policy" "ssl_only" {
  bucket = aws_s3_bucket.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceSSL"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.this.arn,
          "${aws_s3_bucket.this.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}""",
    "CKV_AWS_53": """# Block public access to S3 bucket
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}""",
    # EBS/EC2 Security
    "CKV_AWS_3": """# Enable EBS volume encryption
resource "aws_ebs_volume" "this" {
  availability_zone = var.availability_zone
  size              = var.size

  encrypted  = true
  kms_key_id = var.kms_key_id  # Optional: Use CMK instead of AWS-managed key

  tags = {
    Name = var.name
  }
}""",
    "CKV_AWS_8": """# Enable EC2 launch configuration encryption
resource "aws_launch_configuration" "this" {
  name_prefix   = var.name_prefix
  image_id      = var.ami_id
  instance_type = var.instance_type

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
  }

  ebs_block_device {
    device_name = "/dev/sdf"
    encrypted   = true
    volume_type = "gp3"
  }
}""",
    "CKV_AWS_79": """# Enable IMDSv2 for EC2 instances
resource "aws_instance" "this" {
  ami           = var.ami_id
  instance_type = var.instance_type

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Enforce IMDSv2
    http_put_response_hop_limit = 1
  }
}""",
    # Security Groups
    "CKV_AWS_23": """# Restrict security group ingress - avoid 0.0.0.0/0
resource "aws_security_group" "this" {
  name        = var.name
  description = var.description
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from internal"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # Internal networks only
  }

  # Avoid rules like:
  # cidr_blocks = ["0.0.0.0/0"]  # DANGEROUS: Open to internet
}""",
    "CKV_AWS_24": """# Restrict SSH access
ingress {
  description = "SSH from bastion only"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = [var.bastion_cidr]  # Bastion host CIDR only
  # Or use security_groups = [aws_security_group.bastion.id]
}""",
    "CKV_AWS_25": """# Restrict RDP access
ingress {
  description = "RDP from VPN only"
  from_port   = 3389
  to_port     = 3389
  protocol    = "tcp"
  cidr_blocks = [var.vpn_cidr]  # VPN CIDR only
}""",
    # RDS Security
    "CKV_AWS_16": """# Enable RDS encryption
resource "aws_db_instance" "this" {
  identifier     = var.identifier
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class

  storage_encrypted = true
  kms_key_id        = var.kms_key_arn  # Optional: Use CMK

  # Other required attributes...
}""",
    "CKV_AWS_17": """# RDS snapshots inherit encryption from the source DB
# Ensure the source RDS instance has encryption enabled
resource "aws_db_instance" "this" {
  storage_encrypted = true
  # Snapshots will automatically be encrypted
}""",
    "CKV_AWS_157": """# Enable Multi-AZ for high availability
resource "aws_db_instance" "this" {
  identifier     = var.identifier
  engine         = var.engine
  instance_class = var.instance_class

  multi_az = true  # Enable Multi-AZ deployment

  # Other required attributes...
}""",
    "CKV_AWS_128": """# Enable deletion protection
resource "aws_db_instance" "this" {
  identifier = var.identifier

  deletion_protection = true  # Prevent accidental deletion

  # Other required attributes...
}""",
    # ALB/ELB Security
    "CKV_AWS_2": """# Use HTTPS listener with TLS
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# Redirect HTTP to HTTPS
resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}""",
    "CKV_AWS_103": """# Use TLS 1.2+ security policy
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"

  # Use a policy that enforces TLS 1.2 minimum
  ssl_policy = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  # Or: "ELBSecurityPolicy-TLS-1-2-2017-01"

  certificate_arn = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}""",
    "CKV_AWS_104": """# Enable ALB access logging
resource "aws_lb" "this" {
  name               = var.name
  internal           = var.internal
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids

  access_logs {
    bucket  = aws_s3_bucket.lb_logs.id
    prefix  = "alb-logs"
    enabled = true
  }
}""",
    # VPC/Network Security
    "CKV_AWS_48": """# Enable VPC Flow Logs
resource "aws_flow_log" "this" {
  vpc_id          = aws_vpc.this.id
  traffic_type    = "ALL"
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn

  tags = {
    Name = "${var.name}-flow-logs"
  }
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/flow-logs/${var.name}"
  retention_in_days = 30
}""",
    # CloudTrail
    "CKV_AWS_67": """# Enable CloudTrail
resource "aws_cloudtrail" "this" {
  name                          = var.name
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }
}""",
    "CKV_AWS_35": """# Enable CloudTrail log file validation
resource "aws_cloudtrail" "this" {
  name           = var.name
  s3_bucket_name = aws_s3_bucket.cloudtrail.id

  enable_log_file_validation = true  # Enable log integrity validation
}""",
    # SQS/SNS Security
    "CKV_AWS_27": """# Enable SQS queue encryption
resource "aws_sqs_queue" "this" {
  name = var.name

  sqs_managed_sse_enabled = true
  # Or use KMS:
  # kms_master_key_id = var.kms_key_id
}""",
    "CKV_AWS_26": """# Enable SNS topic encryption
resource "aws_sns_topic" "this" {
  name              = var.name
  kms_master_key_id = var.kms_key_id  # Required for encryption
}""",
    # ElastiCache Security
    "CKV_AWS_83": """# Enable ElastiCache encryption in transit
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.name
  description          = var.description

  transit_encryption_enabled = true  # Enable TLS
  auth_token                 = var.auth_token  # Optional but recommended

  # Other required attributes...
}""",
    "CKV_AWS_84": """# Enable ElastiCache encryption at rest
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.name
  description          = var.description

  at_rest_encryption_enabled = true
  kms_key_id                 = var.kms_key_id  # Optional: Use CMK

  # Other required attributes...
}""",
    # KMS
    "CKV_AWS_7": """# Enable KMS key rotation
resource "aws_kms_key" "this" {
  description             = var.description
  deletion_window_in_days = 30

  enable_key_rotation = true  # Enable automatic annual rotation
}""",
    "CKV_AWS_33": """# Restrict KMS key policy to specific principals
resource "aws_kms_key" "this" {
  description             = var.description
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Key Administrators"
        Effect = "Allow"
        Principal = {
          AWS = var.admin_role_arns
        }
        Action = [
          "kms:Create*",
          "kms:Describe*",
          "kms:Enable*",
          "kms:List*",
          "kms:Put*",
          "kms:Update*",
          "kms:Revoke*",
          "kms:Disable*",
          "kms:Get*",
          "kms:Delete*",
          "kms:ScheduleKeyDeletion",
          "kms:CancelKeyDeletion"
        ]
        Resource = "*"
      }
    ]
  })
}""",
    # IAM Security
    "CKV_AWS_40": """# Enable strong password policy
resource "aws_iam_account_password_policy" "strict" {
  minimum_password_length        = 14
  require_lowercase_characters   = true
  require_uppercase_characters   = true
  require_numbers                = true
  require_symbols                = true
  allow_users_to_change_password = true
  max_password_age               = 90
  password_reuse_prevention      = 24
}""",
    "CKV_AWS_41": """# Enable MFA for root account (manual step required)
# 1. Go to AWS Console → IAM → Dashboard
# 2. Click "Activate MFA on your root account"
# 3. Follow the wizard to set up virtual or hardware MFA

# To enforce MFA via policy:
resource "aws_iam_policy" "require_mfa" {
  name = "require-mfa"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyAllExceptListedIfNoMFA"
      Effect    = "Deny"
      NotAction = ["iam:CreateVirtualMFADevice", "iam:EnableMFADevice"]
      Resource  = "*"
      Condition = {
        BoolIfExists = { "aws:MultiFactorAuthPresent" = "false" }
      }
    }]
  })
}""",
    "CKV_AWS_49": """# Follow IAM least privilege principle
# Avoid using wildcard (*) in Actions and Resources
resource "aws_iam_policy" "least_privilege" {
  name = "specific-permissions"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::my-bucket/*"  # Specific bucket
        ]
      }
    ]
  })
}

# AVOID patterns like:
# Action   = "*"           # Too broad
# Resource = "*"           # Too broad
# Action   = "s3:*"        # All S3 actions""",
    # Lambda Security
    "CKV_AWS_62": """# Ensure Lambda function is not publicly accessible
resource "aws_lambda_permission" "allow_specific" {
  statement_id  = "AllowSpecificInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = aws_api_gateway_rest_api.this.execution_arn

  # Never use:
  # principal = "*"  # DANGEROUS: Allows anyone to invoke
}""",
    "CKV_AWS_50": """# Enable Lambda X-Ray tracing
resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = aws_iam_role.lambda.arn
  handler       = var.handler
  runtime       = var.runtime

  tracing_config {
    mode = "Active"  # Enable X-Ray tracing
  }
}""",
    "CKV_AWS_115": """# Configure Lambda reserved concurrency
resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = aws_iam_role.lambda.arn
  handler       = var.handler
  runtime       = var.runtime

  reserved_concurrent_executions = 100  # Adjust based on needs
}""",
    "CKV_AWS_116": """# Enable Lambda Dead Letter Queue
resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = aws_iam_role.lambda.arn
  handler       = var.handler
  runtime       = var.runtime

  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }
}

resource "aws_sqs_queue" "dlq" {
  name = "${var.function_name}-dlq"
}""",
    "CKV_AWS_117": """# Run Lambda inside VPC
resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = aws_iam_role.lambda.arn
  handler       = var.handler
  runtime       = var.runtime

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}""",
    # CloudTrail Additional
    "CKV_AWS_36": """# Enable CloudTrail S3 bucket access logging
resource "aws_s3_bucket" "cloudtrail" {
  bucket = var.cloudtrail_bucket_name
}

resource "aws_s3_bucket_logging" "cloudtrail" {
  bucket        = aws_s3_bucket.cloudtrail.id
  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "cloudtrail-bucket-logs/"
}""",
    # API Gateway
    "CKV_AWS_76": """# Enable API Gateway access logging
resource "aws_api_gateway_stage" "this" {
  stage_name    = var.stage_name
  rest_api_id   = aws_api_gateway_rest_api.this.id
  deployment_id = aws_api_gateway_deployment.this.id

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn
    format = jsonencode({
      requestId         = "$context.requestId"
      ip                = "$context.identity.sourceIp"
      requestTime       = "$context.requestTime"
      httpMethod        = "$context.httpMethod"
      resourcePath      = "$context.resourcePath"
      status            = "$context.status"
      responseLength    = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/apigateway/${var.api_name}"
  retention_in_days = 30
}""",
    # RDS Additional
    "CKV_AWS_15": """# Enable Multi-AZ for RDS high availability
resource "aws_db_instance" "this" {
  identifier     = var.identifier
  engine         = var.engine
  instance_class = var.instance_class

  multi_az = true  # Enable Multi-AZ deployment
}""",
    "CKV_AWS_91": """# Enable RDS Enhanced Monitoring
resource "aws_db_instance" "this" {
  identifier     = var.identifier
  engine         = var.engine
  instance_class = var.instance_class

  monitoring_interval = 60  # Seconds (0 to disable)
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn
}

resource "aws_iam_role" "rds_monitoring" {
  name = "rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}""",
    "CKV_AWS_118": """# Enable RDS IAM authentication
resource "aws_db_instance" "this" {
  identifier     = var.identifier
  engine         = var.engine
  instance_class = var.instance_class

  iam_database_authentication_enabled = true
}""",
    # S3 Additional
    "CKV_AWS_145": """# Enable S3 bucket KMS encryption (instead of AES256)
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}""",
    "CKV_AWS_144": """# Enable S3 cross-region replication
resource "aws_s3_bucket_replication_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  role   = aws_iam_role.replication.arn

  rule {
    id     = "replicate-all"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.replica.arn
      storage_class = "STANDARD"
    }
  }
}""",
    # EC2 Additional
    "CKV_AWS_135": """# Enable EBS optimization for EC2
resource "aws_instance" "this" {
  ami           = var.ami_id
  instance_type = var.instance_type

  ebs_optimized = true
}""",
    "CKV_AWS_126": """# Enable detailed monitoring for EC2
resource "aws_instance" "this" {
  ami           = var.ami_id
  instance_type = var.instance_type

  monitoring = true  # Enable detailed monitoring
}""",
    # EBS Additional
    "CKV_AWS_4": """# Enable EBS snapshot encryption
# Note: Snapshots inherit encryption from source volume
# Ensure source volume is encrypted first
resource "aws_ebs_volume" "this" {
  availability_zone = var.availability_zone
  size              = var.size
  encrypted         = true  # Snapshots will be encrypted
  kms_key_id        = var.kms_key_id
}

# For existing unencrypted snapshots, create encrypted copy:
resource "aws_ebs_snapshot_copy" "encrypted" {
  source_snapshot_id = var.source_snapshot_id
  source_region      = var.region
  encrypted          = true
  kms_key_id         = var.kms_key_id
}""",
    # ElastiCache Additional
    "CKV_AWS_31": """# Enable ElastiCache encryption at rest and in transit
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.name
  description          = var.description

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = aws_kms_key.elasticache.arn
}""",
    # GuardDuty
    "CKV_AWS_52": """# Enable GuardDuty
resource "aws_guardduty_detector" "this" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }
}""",
    # AWS Config
    "CKV_AWS_78": """# Enable AWS Config
resource "aws_config_configuration_recorder" "this" {
  name     = "default"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported = true
  }
}

resource "aws_config_configuration_recorder_status" "this" {
  name       = aws_config_configuration_recorder.this.name
  is_enabled = true
  depends_on = [aws_config_delivery_channel.this]
}

resource "aws_config_delivery_channel" "this" {
  name           = "default"
  s3_bucket_name = aws_s3_bucket.config.id
  depends_on     = [aws_config_configuration_recorder.this]
}""",
    # Redshift
    "CKV_AWS_64": """# Enable Redshift cluster encryption
resource "aws_redshift_cluster" "this" {
  cluster_identifier = var.cluster_identifier
  database_name      = var.database_name
  master_username    = var.master_username
  master_password    = var.master_password
  node_type          = var.node_type

  encrypted  = true
  kms_key_id = var.kms_key_id
}""",
    # ECR
    "CKV_AWS_65": """# Enable ECR repository encryption
resource "aws_ecr_repository" "this" {
  name                 = var.name
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = var.kms_key_arn
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}""",
    # DocumentDB
    "CKV_AWS_5": """# Enable DocumentDB backup retention
resource "aws_docdb_cluster" "this" {
  cluster_identifier = var.cluster_identifier
  engine             = "docdb"
  master_username    = var.master_username
  master_password    = var.master_password

  backup_retention_period = 7  # Days (1-35)
  preferred_backup_window = "07:00-09:00"
}""",
    # DynamoDB
    "CKV_AWS_28": """# Enable DynamoDB point-in-time recovery
resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = var.hash_key

  point_in_time_recovery {
    enabled = true
  }
}""",
}


def get_fix_suggestion(check_id: str) -> str | None:
    """
    Get fix suggestion for a Checkov check ID.

    Args:
        check_id: Checkov check ID (e.g., "CKV_AWS_19")

    Returns:
        Terraform code suggestion if available, None otherwise
    """
    return FIX_SUGGESTIONS.get(check_id)
