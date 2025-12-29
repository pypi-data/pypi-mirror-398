"""
AWS Lightsail Mini Infrastructure Stack
======================================

This module provides a comprehensive AWS Lightsail infrastructure deployment stack
using CDKTF (Cloud Development Kit for Terraform) with Python.

The stack includes:
    * Lightsail Container Service with automatic custom domain attachment
    * PostgreSQL Database (optional)
    * DNS management with CNAME records
    * SSL certificate management with automatic validation
    * IAM resources for service access
    * S3 bucket for application data
    * Secrets Manager for credential storage

:author: Generated with GitHub Copilot
:version: 1.0.0
:license: MIT
"""


#region specific imports

from constructs import Construct

# Import the base class
from .LightsailBaseStandalone import LightsailBaseStandalone
from .LightsailFlags import ContainerArchitectureFlags
from .LightsailMixins import LightsailContainerMixin

#endregion

#region AWS Provider and Resources
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws import (
    cloudfront_distribution,
)
#endregion

# AWS WAF (currently unused but imported for future use)
from cdktf_cdktf_provider_aws.wafv2_web_acl import (
    Wafv2WebAcl,
    Wafv2WebAclDefaultAction,
    Wafv2WebAclRule,
    Wafv2WebAclVisibilityConfig,
    Wafv2WebAclDefaultActionAllow,
    Wafv2WebAclRuleOverrideAction,
    Wafv2WebAclRuleOverrideActionNone,
    Wafv2WebAclRuleOverrideActionCount,
    Wafv2WebAclRuleVisibilityConfig,
)
from cdktf_cdktf_provider_aws.wafv2_web_acl_association import Wafv2WebAclAssociation
from cdktf_cdktf_provider_aws.wafv2_rule_group import Wafv2RuleGroupRuleVisibilityConfig

#endregion



ArchitectureFlags = ContainerArchitectureFlags


class LightsailContainerStandaloneStack(LightsailContainerMixin, LightsailBaseStandalone):
    """
    AWS Lightsail Mini Infrastructure Stack.

    A comprehensive infrastructure stack that deploys:
        * Lightsail Container Service with custom domain support
        * PostgreSQL database (optional)
        * IAM resources and S3 storage

    :param scope: The construct scope
    :param id: The construct ID
    :param kwargs: Configuration parameters including region, domains, flags, etc.

    Example:
        >>> stack = LightsailContainerStandaloneStack(
        ...     app, "my-stack",
        ...     region="ca-central-1",
        ...     domains=["app.example.com"],
        ...     project_name="my-app",
        ...     postApplyScripts=[
        ...         "echo 'Deployment completed'",
        ...         "curl -X POST https://webhook.example.com/notify"
        ...     ]
        ... )
    """

    @staticmethod
    def get_architecture_flags():
        """
        Get the ArchitectureFlags enum for configuration.

        :returns: ArchitectureFlags enum class
        :rtype: type[ArchitectureFlags]
        """
        return ContainerArchitectureFlags

    def __init__(self, scope, id, **kwargs):
        """
        Initialize the AWS Lightsail Mini Infrastructure Stack.

        :param scope: The construct scope
        :param id: Unique identifier for this stack
        :param kwargs: Configuration parameters

        **Configuration Parameters:**

        :param region: AWS region (default: "us-east-1")
        :param environment: Environment name (default: "dev")
        :param project_name: Project identifier (default: "bb-aws-lightsail-mini-v1a-app")
        :param domain_name: Primary domain name
        :param domains: List of custom domains to configure
        :param flags: List of ArchitectureFlags to modify behavior
        :param profile: AWS profile to use (default: "default")
        :param postApplyScripts: List of shell commands to execute after deployment

        .. warning::
           Lightsail domain operations must use us-east-1 region regardless of
           the main stack region.
        """
        # Set container-specific defaults
        if "project_name" not in kwargs:
            kwargs["project_name"] = "bb-aws-lightsail-mini-v1a-app"

        # Set database defaults before base initialization
        self.default_db_name = kwargs.get("default_db_name", kwargs["project_name"])
        self.default_db_username = kwargs.get("default_db_username", "dbadmin")
        
        # Call parent constructor which handles all the base initialization
        super().__init__(scope, id, **kwargs)

        # ===== Container-Specific Configuration =====
        self.domains = kwargs.get("domains", []) or []

        # ===== Database Configuration =====
        self.default_db_name = kwargs.get("default_db_name", self.project_name)
        self.default_db_username = kwargs.get("default_db_username", "dbadmin")

    def _initialize_providers(self):
        """Initialize all required Terraform providers."""
        # Call parent class to initialize base providers
        super()._initialize_providers()
        
        # Add Lightsail-specific provider for domain operations (must be us-east-1)
        self.aws_domain_provider = AwsProvider(
            self, "aws_domain", region="us-east-1", profile=self.profile, alias="domain"
        )
        self.resources["aws_domain"] = self.aws_domain_provider
