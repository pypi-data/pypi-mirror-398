"""
Shared mixins for Lightsail stacks.
"""

import json
import os

from cdktf import TerraformOutput

from cdktf_cdktf_provider_aws import (
    lightsail_container_service,
    lightsail_database,
    s3_bucket,
)
from cdktf_cdktf_provider_aws.secretsmanager_secret import SecretsmanagerSecret
from cdktf_cdktf_provider_aws.secretsmanager_secret_version import SecretsmanagerSecretVersion
from cdktf_cdktf_provider_aws.data_aws_secretsmanager_secret_version import (
    DataAwsSecretsmanagerSecretVersion,
)
from cdktf_cdktf_provider_null.resource import Resource as NullResource
from cdktf_cdktf_provider_random import password

from .LightsailFlags import (
    BaseLightsailArchitectureFlags,
    ContainerArchitectureFlags,
    DatabaseArchitectureFlags,
)


class LightsailBaseMixin:
    """
    Shared helpers for Lightsail base stacks.
    """

    def get_extra_secret_env(self, env_var_name=None):
        if env_var_name is None:
            env_var_name = self.default_extra_secret_env

        extra_secret_env = os.environ.get(env_var_name, None)

        if extra_secret_env:
            try:
                extra_secret_json = json.loads(extra_secret_env)
                for key, value in extra_secret_json.items():
                    if key not in self.secrets:
                        self.secrets[key] = value
            except json.JSONDecodeError:
                pass

    def create_security_resources(self):
        self.secrets_manager_secret = SecretsmanagerSecret(
            self, self.secret_name, name=f"{self.secret_name}"
        )
        self.resources["secretsmanager_secret"] = self.secrets_manager_secret

        self.secrets.update(
            {
                "service_user_access_key": self.service_key.id,
                "service_user_secret_key": self.service_key.secret,
                "access_key": self.service_key.id,
                "secret_access_key": self.service_key.secret,
                "region_name": self.region,
                "signature_version": self.default_signature_version,
            }
        )

        self.get_extra_secret_env()

        if self.has_flag(BaseLightsailArchitectureFlags.PRESERVE_EXISTING_SECRETS.value):
            self._create_secret_version_conditionally()
        elif self.has_flag(BaseLightsailArchitectureFlags.IGNORE_SECRET_CHANGES.value):
            self._create_secret_version_with_lifecycle_ignore()
        else:
            SecretsmanagerSecretVersion(
                self,
                self.secret_name + "_version",
                secret_id=self.secrets_manager_secret.id,
                secret_string=(
                    json.dumps(self.secrets, indent=2, sort_keys=True)
                    if self.secrets
                    else None
                ),
            )

    def _create_secret_version_conditionally(self):
        try:
            DataAwsSecretsmanagerSecretVersion(
                self,
                self.secret_name + "_existing_check",
                secret_id=self.secrets_manager_secret.id,
                version_stage="AWSCURRENT",
            )

            conditional_secret = SecretsmanagerSecretVersion(
                self,
                self.secret_name + "_version_conditional",
                secret_id=self.secrets_manager_secret.id,
                secret_string=json.dumps(self.secrets, indent=2, sort_keys=True)
                if self.secrets
                else None,
                lifecycle={"ignore_changes": ["secret_string"], "create_before_destroy": False},
            )

            conditional_secret.add_override(
                "count",
                "${length(try(jsondecode(data.aws_secretsmanager_secret_version."
                + self.secret_name.replace("/", "_").replace("-", "_")
                + "_existing_check.secret_string), {})) == 0 ? 1 : 0}",
            )

        except Exception:
            SecretsmanagerSecretVersion(
                self,
                self.secret_name + "_version_fallback",
                secret_id=self.secrets_manager_secret.id,
                secret_string=json.dumps(self.secrets, indent=2, sort_keys=True)
                if self.secrets
                else None,
            )

    def _create_secret_version_with_lifecycle_ignore(self):
        secret_version = SecretsmanagerSecretVersion(
            self,
            self.secret_name + "_version_ignored",
            secret_id=self.secrets_manager_secret.id,
            secret_string=json.dumps(self.secrets, indent=2, sort_keys=True)
            if self.secrets
            else None,
        )

        secret_version.add_override("lifecycle", {"ignore_changes": ["secret_string"]})

    def execute_post_apply_scripts(self):
        if not self.post_apply_scripts:
            return

        dependencies = []
        if hasattr(self, "secrets_manager_secret"):
            dependencies.append(self.secrets_manager_secret)

        for i, script in enumerate(self.post_apply_scripts):
            script_resource = NullResource(
                self, f"post_apply_script_{i}", depends_on=dependencies if dependencies else None
            )

            script_resource.add_override(
                "provisioner",
                [{"local-exec": {"command": script, "on_failure": "continue"}}],
            )

    def has_flag(self, flag_value):
        return flag_value in self.flags

    def clean_hyphens(self, text):
        return text.replace("-", "_")

    def properize_s3_bucketname(self, bucket_name):
        clean_name = bucket_name.lower().replace("_", "-")
        clean_name = clean_name.strip("-.")
        return clean_name

    def create_iam_outputs(self):
        TerraformOutput(
            self,
            "iam_user_access_key",
            value=self.service_key.id,
            sensitive=True,
            description="IAM user access key ID (sensitive)",
        )

        TerraformOutput(
            self,
            "iam_user_secret_key",
            value=self.service_key.secret,
            sensitive=True,
            description="IAM user secret access key (sensitive)",
        )

        TerraformOutput(
            self,
            "secrets_manager_secret_name",
            value=self.secret_name,
            description="AWS Secrets Manager secret name containing all credentials",
        )


class LightsailContainerMixin:
    """
    Shared container stack behavior.
    """

    def _set_default_post_apply_scripts(self):
        super()._set_default_post_apply_scripts()

        if BaseLightsailArchitectureFlags.SKIP_DEFAULT_POST_APPLY_SCRIPTS.value in self.flags:
            return

        container_scripts = [
            f"echo '🚀 Container Service URL: https://{self.project_name}.{self.region}.cs.amazonlightsail.com'",
        ]

        if self.post_apply_scripts:
            insert_index = len(self.post_apply_scripts) - 1
            for script in reversed(container_scripts):
                self.post_apply_scripts.insert(insert_index, script)

    def create_lightsail_resources(self):
        self.container_service = lightsail_container_service.LightsailContainerService(
            self,
            "app_container",
            name=f"{self.project_name}",
            power="nano",
            region=self.region,
            scale=1,
            is_disabled=False,
            tags={
                "Environment": self.environment,
                "Project": self.project_name,
                "Stack": self.__class__.__name__,
            },
        )
        self.container_service_url = self.get_lightsail_container_service_domain()

        if not self.has_flag(ContainerArchitectureFlags.SKIP_DATABASE.value):
            self.create_lightsail_database()

        self.create_s3_bucket()
        self.resources["lightsail_container_service"] = self.container_service

    def create_lightsail_database(self):
        self.db_password = password.Password(
            self,
            "db_password",
            length=16,
            special=True,
            override_special="!#$%&*()-_=+[]{}<>:?",
        )

        self.database = lightsail_database.LightsailDatabase(
            self,
            "app_database",
            relational_database_name=f"{self.project_name}-db",
            blueprint_id="postgres_14",
            bundle_id="micro_2_0",
            master_database_name=self.clean_hyphens(f"{self.project_name}"),
            master_username=self.default_db_username,
            master_password=self.db_password.result,
            skip_final_snapshot=True,
            tags={
                "Environment": self.environment,
                "Project": self.project_name,
                "Stack": self.__class__.__name__,
            },
        )

        self.secrets.update(
            {
                "password": self.db_password.result,
                "username": self.default_db_username,
                "dbname": self.default_db_name,
                "host": self.database.master_endpoint_address,
                "port": self.database.master_endpoint_port,
            }
        )

    def create_s3_bucket(self, bucket_name=None):
        if bucket_name is None:
            bucket_name = self.properize_s3_bucketname(f"{self.project_name}-s3")

        self.s3_bucket = s3_bucket.S3Bucket(
            self,
            "app_data_bucket",
            bucket=bucket_name,
            acl="private",
            versioning={"enabled": True},
            server_side_encryption_configuration={
                "rule": {
                    "apply_server_side_encryption_by_default": {"sse_algorithm": "AES256"},
                    "bucket_key_enabled": True,
                }
            },
            tags={
                "Environment": self.environment,
                "Project": self.project_name,
                "Stack": self.__class__.__name__,
            },
        )

        self.resources["s3_bucket"] = self.s3_bucket
        self.bucket_name = bucket_name

    def get_lightsail_container_service_domain(self):
        return f"{self.project_name}.{self.region}.cs.amazonlightsail.com"

    def create_outputs(self):
        TerraformOutput(
            self,
            "container_service_url",
            value=self.container_service_url,
            description="Public URL of the Lightsail container service",
        )

        if not self.has_flag(ContainerArchitectureFlags.SKIP_DATABASE.value) and hasattr(
            self, "database"
        ):
            TerraformOutput(
                self,
                "database_endpoint",
                value=f"{self.database.master_endpoint_address}:{self.database.master_endpoint_port}",
                description="Database connection endpoint",
            )
            TerraformOutput(
                self,
                "database_password",
                value=self.database.master_password,
                sensitive=True,
                description="Database master password (sensitive)",
            )

        self.create_iam_outputs()


class LightsailDatabaseMixin:
    """
    Shared database stack behavior.
    """

    def _set_default_post_apply_scripts(self):
        super()._set_default_post_apply_scripts()

        if BaseLightsailArchitectureFlags.SKIP_DEFAULT_POST_APPLY_SCRIPTS.value in self.flags:
            return

        databases_list = ", ".join(self.databases)
        database_scripts = [
            f"echo '️  Database Instance: {self.project_name}-db'",
            f"echo '📊 Databases Created: {databases_list}'",
            f"echo '👥 Database Users: {len(self.databases)} individual users created'",
            "echo '🔗 Connection Information:'",
            "echo '   - Instance Endpoint: Available in Terraform outputs'",
            f"echo '   - Master User: {self.master_username}'",
            "echo '   - Port: 5432 (PostgreSQL)'",
            "echo '   - Credentials: Stored in AWS Secrets Manager'",
        ]

        if self.post_apply_scripts:
            insert_index = len(self.post_apply_scripts) - 1
            for script in reversed(database_scripts):
                self.post_apply_scripts.insert(insert_index, script)

    def create_lightsail_resources(self):
        self.create_database_passwords()
        self.create_lightsail_database()
        self.create_database_users()

    def create_database_passwords(self):
        self.master_password = password.Password(
            self,
            "master_db_password",
            length=20,
            special=True,
            override_special="!#$%&*()-_=+[]{}<>:?",
        )

        for db_name in self.databases:
            db_password = password.Password(
                self,
                f"{db_name}_user_password",
                length=16,
                special=True,
                override_special="!#$%&*()-_=+[]{}<>:?",
            )
            self.database_passwords[db_name] = db_password

    def create_lightsail_database(self):
        master_db_name = self.clean_hyphens(self.databases[0])

        self.database = lightsail_database.LightsailDatabase(
            self,
            "database_instance",
            relational_database_name=f"{self.project_name}-db",
            blueprint_id=self.db_engine,
            bundle_id=self.db_instance_size,
            master_database_name=master_db_name,
            master_username=self.master_username,
            master_password=self.master_password.result,
            publicly_accessible=self.db_publicly_accessible,
            skip_final_snapshot=True,
            tags={
                "Environment": self.environment,
                "Project": self.project_name,
                "Stack": self.__class__.__name__,
                "DatabaseCount": str(len(self.databases)),
            },
        )

        self.resources["lightsail_database"] = self.database

        self.secrets.update(
            {
                "master_username": self.master_username,
                "master_password": self.master_password.result,
                "master_database": master_db_name,
                "host": self.database.master_endpoint_address,
                "port": self.database.master_endpoint_port,
                "engine": self.db_engine,
                "region": self.region,
            }
        )

    def create_database_users(self):
        if DatabaseArchitectureFlags.SKIP_DATABASE_USERS.value in self.flags:
            return

        for db_name in self.databases:
            clean_db_name = self.clean_hyphens(db_name)
            username = f"{clean_db_name}-dbuser"
            password_ref = self.database_passwords[db_name].result

            self.secrets[f"{clean_db_name}_username"] = username
            self.secrets[f"{clean_db_name}_password"] = password_ref
            self.secrets[f"{clean_db_name}_database"] = clean_db_name

            self.database_users[clean_db_name] = {
                "username": username,
                "password": password_ref,
                "database": clean_db_name,
            }

        databases_to_create = self.databases[1:] if len(self.databases) > 1 else []

        for db_name in databases_to_create:
            clean_db_name = self.clean_hyphens(db_name)
            username = f"{clean_db_name}-dbuser"
            password_ref = self.database_passwords[db_name].result

            sql_commands = f"""#!/bin/bash
set -e

echo "Creating database: {clean_db_name}"

for i in {{1..30}}; do
    if PGPASSWORD="$MASTER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT 1" > /dev/null 2>&1; then
        echo "Database is ready"
        break
    fi
    echo "Waiting for database to be ready... ($i/30)"
    sleep 10
done

PGPASSWORD="$MASTER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \\"{clean_db_name}\\";" || echo "Database {clean_db_name} may already exist"

PGPASSWORD="$MASTER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE USER \\"{username}\\" WITH PASSWORD '$USER_PASSWORD';" || echo "User {username} may already exist"

PGPASSWORD="$MASTER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE \\"{clean_db_name}\\" TO \\"{username}\\";"

PGPASSWORD="$MASTER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d {clean_db_name} -c "GRANT ALL ON SCHEMA public TO \\"{username}\\";"

echo "Successfully created database: {clean_db_name} with user: {username}"
"""

            db_resource = NullResource(
                self, f"create_database_{clean_db_name}", depends_on=[self.database]
            )

            db_resource.add_override(
                "provisioner",
                [
                    {
                        "local-exec": {
                            "command": sql_commands,
                            "environment": {
                                "DB_HOST": self.database.master_endpoint_address,
                                "DB_PORT": self.database.master_endpoint_port,
                                "DB_USER": self.master_username,
                                "MASTER_PASSWORD": self.master_password.result,
                                "USER_PASSWORD": password_ref,
                            },
                        }
                    }
                ],
            )

    def create_outputs(self):
        TerraformOutput(
            self,
            "database_endpoint",
            value=f"{self.database.master_endpoint_address}:{self.database.master_endpoint_port}",
            description="Database instance connection endpoint",
        )

        TerraformOutput(
            self,
            "database_instance_name",
            value=self.database.relational_database_name,
            description="Lightsail database instance name",
        )

        TerraformOutput(
            self,
            "master_username",
            value=self.master_username,
            description="Master database username",
        )

        TerraformOutput(
            self,
            "master_password",
            value=self.master_password.result,
            sensitive=True,
            description="Master database password (sensitive)",
        )

        TerraformOutput(
            self,
            "databases_created",
            value=json.dumps(self.databases),
            description="List of databases created in the instance",
        )

        if not self.has_flag(DatabaseArchitectureFlags.SKIP_DATABASE_USERS.value):
            for db_name in self.databases:
                clean_name = self.clean_hyphens(db_name)
                if clean_name in self.database_users:
                    user_info = self.database_users[clean_name]

                    TerraformOutput(
                        self,
                        f"{clean_name}_username",
                        value=user_info["username"],
                        description=f"Database user for {clean_name}",
                    )

                    TerraformOutput(
                        self,
                        f"{clean_name}_password",
                        value=user_info["password"],
                        sensitive=True,
                        description=f"Database password for {clean_name} (sensitive)",
                    )

        self.create_iam_outputs()
