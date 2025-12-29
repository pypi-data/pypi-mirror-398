"""
RepliMap Audit Remediation Module.

Generates Terraform remediation code from Checkov security findings.

This module transforms RepliMap from "consultant mode" (showing issues)
to "surgeon mode" (providing fixes).

Usage:
    from replimap.audit.remediation import RemediationGenerator, RemediationPlan

    generator = RemediationGenerator(findings)
    plan = generator.generate()

    for file in plan.files:
        file.path.write_text(file.content)
"""

from replimap.audit.remediation.generator import RemediationGenerator
from replimap.audit.remediation.models import (
    RemediationFile,
    RemediationPlan,
    RemediationSeverity,
    RemediationType,
)

__all__ = [
    "RemediationFile",
    "RemediationGenerator",
    "RemediationPlan",
    "RemediationSeverity",
    "RemediationType",
]
