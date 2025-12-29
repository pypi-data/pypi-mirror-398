"""
AWS Lightsail Base Standalone Infrastructure Stack
==================================================

This module provides a standalone base class for AWS Lightsail infrastructure
stacks using CDKTF. It avoids AWSArchitectureBase and its compliance bootstrap
resources, while keeping IAM/Secrets/post-apply helpers used by Lightsail stacks.
"""

import os
from cdktf import TerraformStack

from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws import (
    iam_group,
    iam_user,
    iam_access_key,
    iam_user_group_membership,
    iam_group_policy,
)

from cdktf_cdktf_provider_random.provider import RandomProvider

from cdktf_cdktf_provider_null.provider import NullProvider

from .LightsailFlags import BaseLightsailArchitectureFlags
from .LightsailMixins import LightsailBaseMixin


class LightsailBaseStandalone(LightsailBaseMixin, TerraformStack):
    """
    Standalone base class for Lightsail stacks without AWSArchitectureBase.
    """

    resources = {}
    default_post_apply_scripts = []

    @staticmethod
    def get_architecture_flags():
        return BaseLightsailArchitectureFlags

    def __init__(self, scope, id, **kwargs):
        self.region = kwargs.get("region", "us-east-1")
        self.environment = kwargs.get("environment", "dev")
        self.project_name = kwargs.get("project_name")
        self.profile = kwargs.get("profile", "default")

        if not self.project_name:
            raise ValueError("project_name is required and cannot be empty")

        super().__init__(scope, id)

        self.flags = kwargs.get("flags", [])
        self.post_apply_scripts = kwargs.get("postApplyScripts", []) or []

        default_secret_name = f"{self.project_name}/{self.environment}/credentials"
        self.secret_name = kwargs.get("secret_name", default_secret_name)
        self.default_signature_version = kwargs.get("default_signature_version", "s3v4")
        self.default_extra_secret_env = kwargs.get("default_extra_secret_env", "SECRET_STRING")

        default_bucket_name = self.properize_s3_bucketname(f"{self.region}-{self.project_name}-tfstate")
        self.state_bucket_name = kwargs.get("state_bucket_name", default_bucket_name)

        self.secrets = {}
        self.post_terraform_messages = []
        self._post_plan_guidance: list[str] = []

        self._initialize_providers()
        self._set_default_post_apply_scripts()
        self._create_infrastructure_components()

    def _initialize_providers(self):
        aws = AwsProvider(self, "aws", region=self.region, profile=self.profile)
        self.resources["aws"] = aws

        RandomProvider(self, "random")
        self.resources["random"] = RandomProvider

        NullProvider(self, "null")
        self.resources["null"] = NullProvider

    def _set_default_post_apply_scripts(self):
        self.default_post_apply_scripts = [
            "echo '============================================='",
            "echo '✅ Deployment Completed Successfully'",
            "echo '============================================='",
            f"echo '🏗️  Project: {self.project_name}'",
            f"echo '🌍 Environment: {self.environment}'",
            f"echo '📍 Region: {self.region}'",
            "echo '============================================='",
            "echo '💻 System Information:'",
            "echo '   - OS: '$(uname -s)",
            "echo '   - Architecture: '$(uname -m)",
            "echo '   - User: '$(whoami)",
            "echo '   - Working Directory: '$(pwd)",
            "echo '============================================='",
            "echo '✅ Post-deployment scripts execution started'",
        ]

        if BaseLightsailArchitectureFlags.SKIP_DEFAULT_POST_APPLY_SCRIPTS.value in self.flags:
            return

        self.post_apply_scripts = self.default_post_apply_scripts + self.post_apply_scripts

    def _create_infrastructure_components(self):
        self.create_iam_resources()
        self.create_lightsail_resources()
        self.create_security_resources()
        self.execute_post_apply_scripts()
        self.create_outputs()

    def create_lightsail_resources(self):
        raise NotImplementedError("create_lightsail_resources must be implemented by subclasses")

    def create_outputs(self):
        raise NotImplementedError("create_outputs must be implemented by subclasses")

    def create_iam_resources(self):
        user_name = f"{self.project_name}-service-user"
        group_name = f"{self.project_name}-group"

        self.service_group = iam_group.IamGroup(self, "service_group", name=group_name)
        self.service_user = iam_user.IamUser(self, "service_user", name=user_name)

        iam_user_group_membership.IamUserGroupMembership(
            self,
            "service_user_group_membership",
            user=self.service_user.name,
            groups=[self.service_group.name],
        )

        self.service_key = iam_access_key.IamAccessKey(
            self, "service_key", user=self.service_user.name
        )

        try:
            self.service_policy = self.create_iam_policy_from_file()
            self.resources["iam_policy"] = self.service_policy
        except FileNotFoundError:
            pass

    def create_iam_policy_from_file(self, file_path="iam_policy.json"):
        file_to_open = os.path.join(os.path.dirname(__file__), file_path)

        with open(file_to_open, "r") as f:
            policy = f.read()

        return iam_group_policy.IamGroupPolicy(
            self,
            f"{self.project_name}-{self.environment}-service-policy",
            name=f"{self.project_name}-{self.environment}-service-policy",
            group=self.service_group.name,
            policy=policy,
        )
