"""
AWS Lightsail Base Infrastructure Stack
======================================

This module provides an abstract base class for AWS Lightsail infrastructure deployment stacks
using CDKTF (Cloud Development Kit for Terraform) with Python.

The abstract base class includes:
    * Common IAM resources for service access
    * AWS Secrets Manager for credential storage
    * Shared configuration and initialization patterns
    * Common utility methods and secret management strategies
    * Template methods for infrastructure creation workflow

This class should be extended by specific Lightsail implementations such as:
    * LightsailContainerStack - For container services
    * LightsailDatabaseStack - For database instances

:author: Generated with GitHub Copilot
:version: 1.0.0
:license: MIT
"""

#region specific imports

import os
from abc import ABC, abstractmethod
from constructs import Construct

# Import from the correct base architecture package
import sys
sys.path.append('/Repos/AWSArchitectureBase')
from AWSArchitectureBase.AWSArchitectureBaseStack.AWSArchitectureBase import AWSArchitectureBase

#endregion

#region AWS Provider and Resources
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws import iam_access_key, iam_user, iam_user_policy
#endregion

from .LightsailFlags import BaseLightsailArchitectureFlags
from .LightsailMixins import LightsailBaseMixin


class LightsailBase(LightsailBaseMixin, AWSArchitectureBase):
    """
    Abstract base class for AWS Lightsail Infrastructure Stacks.

    This abstract class provides common functionality for Lightsail-based
    infrastructure deployments including:
        * IAM resources for service access
        * AWS Secrets Manager for credential storage
        * Common configuration patterns and initialization
        * Shared utility methods and helper functions
        * Template methods for infrastructure creation workflow

    Subclasses must implement abstract methods to define their specific
    infrastructure components while leveraging the shared functionality.

    :param scope: The construct scope
    :param id: The construct ID
    :param kwargs: Configuration parameters

    **Common Configuration Parameters:**

    :param region: AWS region (default: "us-east-1")
    :param environment: Environment name (default: "dev")
    :param project_name: Project identifier (required)
    :param flags: List of ArchitectureFlags to modify behavior
    :param profile: AWS profile to use (default: "default")
    :param postApplyScripts: List of shell commands to execute after deployment
    :param secret_name: Custom secret name (default: "{project_name}/{environment}/credentials")
    :param default_signature_version: AWS signature version (default: "s3v4")
    :param default_extra_secret_env: Environment variable for additional secrets (default: "SECRET_STRING")

    Example:
        >>> class MyLightsailStack(LightsailBase):
        ...     def create_lightsail_resources(self):
        ...         # Implement specific Lightsail resources
        ...         pass
        ...     
        ...     def get_architecture_flags(self):
        ...         return MyArchitectureFlags
    """

    # Class-level resource registry
    resources = {}

    # Default post-apply scripts executed after deployment
    default_post_apply_scripts = []

    def get_architecture_flags(self):
        """
        Get the ArchitectureFlags enum for configuration.

        :returns: ArchitectureFlags enum class
        :rtype: type[ArchitectureFlags]
        """
        super_flags = super.get_architecture_flags()
        this_flags = ArchitectureFlags
        for flag in super_flags:
            this_flags[flag.name] = flag.value

        return this_flags

    def __init__(self, scope, id, **kwargs):
        """
        Initialize the AWS Lightsail Base Infrastructure Stack.

        :param scope: The construct scope
        :param id: Unique identifier for this stack
        :param kwargs: Configuration parameters
        """
        # Initialize configuration before parent class to ensure proper state bucket setup
        self.region = kwargs.get("region", "us-east-1")
        self.environment = kwargs.get("environment", "dev")
        self.project_name = kwargs.get("project_name")
        self.profile = kwargs.get("profile", "default")
        
        if not self.project_name:
            raise ValueError("project_name is required and cannot be empty")
        
        # Ensure we pass all kwargs to parent class
        super().__init__(scope, id, **kwargs)

        # ===== Stack Configuration =====
        self.flags = kwargs.get("flags", [])
        self.post_apply_scripts = kwargs.get("postApplyScripts", []) or []

        # ===== Security Configuration =====
        default_secret_name = f"{self.project_name}/{self.environment}/credentials"
        self.secret_name = kwargs.get("secret_name", default_secret_name)
        self.default_signature_version = kwargs.get("default_signature_version", "s3v4")
        self.default_extra_secret_env = kwargs.get("default_extra_secret_env", "SECRET_STRING")

        # ===== Storage Configuration =====
        default_bucket_name = self.properize_s3_bucketname(f"{self.region}-{self.project_name}-tfstate")
        self.state_bucket_name = kwargs.get("state_bucket_name", default_bucket_name)

        # ===== Internal State =====
        self.secrets = {}
        self.post_terraform_messages = []
        self._post_plan_guidance: list[str] = []

        # ===== Infrastructure Setup =====
        # Base infrastructure is already set up by parent class
        # Initialize our specific components using template method pattern
        self._set_default_post_apply_scripts()
        self._create_infrastructure_components()

    def _initialize_providers(self):
        """
        Initialize all required Terraform providers.
        
        Calls the parent class to initialize base providers and can be
        extended by subclasses to add additional provider configurations.
        """
        # Call parent class to initialize base providers (AWS, Random, Null)
        super()._initialize_providers()

    def _set_default_post_apply_scripts(self):
        """
        Set default post-apply scripts and merge with user-provided scripts.

        This method configures the default post-apply scripts that provide
        deployment status information and basic verification. These scripts
        are automatically added to the post_apply_scripts list unless the
        SKIP_DEFAULT_POST_APPLY_SCRIPTS flag is set.

        Subclasses can override this method to provide their own default scripts
        while optionally calling the parent method.

        **Default Scripts Include:**

        * Deployment completion notification
        * Infrastructure summary information
        * Environment and project details
        * Basic system information

        **Script Merging:**

        * Default scripts are prepended to user-provided scripts
        * User scripts execute after default scripts
        * Duplicates are not automatically removed

        .. note::
           Default scripts can be skipped by including the SKIP_DEFAULT_POST_APPLY_SCRIPTS
           flag in the flags parameter during stack initialization.

        .. warning::
           Default scripts use environment variables and command substitution.
           Ensure the execution environment supports bash-style commands.
        """
        # Define base default post-apply scripts
        self.default_post_apply_scripts = [
            "echo '============================================='",
            "echo '🎉 AWS Lightsail Infrastructure Deployment Complete!'",
            "echo '============================================='",
            f"echo '📦 Project: {self.project_name}'",
            f"echo '🌍 Environment: {self.environment}'",
            f"echo '📍 Region: {self.region}'",
            "echo '⏰ Deployment Time: '$(date)",
            "echo '============================================='",
            "echo '💻 System Information:'",
            "echo '   - OS: '$(uname -s)",
            "echo '   - Architecture: '$(uname -m)",
            "echo '   - User: '$(whoami)",
            "echo '   - Working Directory: '$(pwd)",
            "echo '============================================='",
            "echo '✅ Post-deployment scripts execution started'",
        ]

        # Skip default scripts if flag is set
        if BaseLightsailArchitectureFlags.SKIP_DEFAULT_POST_APPLY_SCRIPTS.value in self.flags:
            return

        # Merge default scripts with user-provided scripts
        # Default scripts execute first, then user scripts
        self.post_apply_scripts = self.default_post_apply_scripts + self.post_apply_scripts

    def _create_infrastructure_components(self):
        """
        Template method for creating all infrastructure components in the correct order.
        
        This method defines the overall workflow for infrastructure creation
        and calls abstract methods that must be implemented by subclasses.
        The order of operations is:
        
        1. Create IAM resources (concrete implementation provided)
        2. Create Lightsail-specific resources (abstract - implemented by subclasses)
        3. Create security resources (concrete implementation provided)
        4. Execute post-apply scripts (concrete implementation provided)
        5. Create outputs (abstract - implemented by subclasses)
        """
        # Core infrastructure - provided by base class
        self.create_iam_resources()
        
        # Lightsail-specific resources - implemented by subclasses
        self.create_lightsail_resources()
        
        # Security and storage - provided by base class
        self.create_security_resources()

        # Post-apply scripts - provided by base class
        self.execute_post_apply_scripts()

        # Output generation - implemented by subclasses
        self.create_outputs()

    # ==================== ABSTRACT METHODS ====================

    @abstractmethod
    def create_lightsail_resources(self):
        """
        Create Lightsail-specific resources.
        
        This method must be implemented by subclasses to create their
        specific Lightsail resources such as:
        * Container services
        * Database instances
        * Storage volumes
        * Networking components
        
        The method should populate the self.secrets dictionary with
        any credentials or connection information that should be stored
        in AWS Secrets Manager.
        """
        pass

    @abstractmethod
    def create_outputs(self):
        """
        Create Terraform outputs for important resource information.
        
        This method must be implemented by subclasses to create
        appropriate Terraform outputs for their specific resources.
        
        Common patterns include:
        * Resource endpoints and URLs
        * Connection information
        * Sensitive credentials (marked as sensitive=True)
        * Resource identifiers and names
        """
        pass

    # ==================== CONCRETE SHARED METHODS ====================

    def create_iam_resources(self):
        """
        Create IAM resources for service access.

        Creates:
            * IAM user for programmatic access to AWS services
            * Access key pair for the IAM user
            * IAM policy loaded from external JSON file (if exists)

        The IAM user follows the naming pattern: {project_name}-service-user
        """
        # Create IAM User and Access Key 
        user_name = f"{self.project_name}-service-user"
        self.service_user = iam_user.IamUser(
            self, "service_user", name=user_name
        )

        # Create IAM Access Key
        self.service_key = iam_access_key.IamAccessKey(
            self, "service_key", user=self.service_user.name
        )

        # IAM Policy from external file (optional)
        try:
            self.service_policy = self.create_iam_policy_from_file()
            self.resources["iam_policy"] = self.service_policy
        except FileNotFoundError:
            # Policy file doesn't exist, skip policy creation
            pass

    def create_iam_policy_from_file(self, file_path="iam_policy.json"):
        """
        Create IAM policy from JSON file.

        :param file_path: Path to IAM policy JSON file relative to this module
        :type file_path: str
        :returns: IAM user policy resource
        :rtype: IamUserPolicy
        :raises FileNotFoundError: If policy file doesn't exist

        .. note::
           The policy file should be located in the same directory as this module.
        """
        file_to_open = os.path.join(os.path.dirname(__file__), file_path)

        with open(file_to_open, "r") as f:
            policy = f.read()

        return iam_user_policy.IamUserPolicy(
            self,
            f"{self.project_name}-{self.environment}-service-policy",
            name=f"{self.project_name}-{self.environment}-service-policy",
            user=self.service_user.name,
            policy=policy,
        )
