"""
AWS Lightsail Database Infrastructure Stack
==========================================

This module provides a specialized AWS Lightsail database deployment stack
using CDKTF (Cloud Development Kit for Terraform) with Python.

The stack includes:
    * Lightsail Database instance (PostgreSQL)
    * Multiple databases within the instance
    * Individual database users with scoped permissions
    * Secrets Manager for credential storage per database
    * IAM resources for service access

:author: Generated with GitHub Copilot
:version: 1.0.0
:license: MIT
"""

#region specific imports

from constructs import Construct

# Import the base class
from .LightsailBase import LightsailBase
from .LightsailFlags import DatabaseArchitectureFlags
from .LightsailMixins import LightsailDatabaseMixin

#endregion

ArchitectureFlags = DatabaseArchitectureFlags


class LightsailDatabaseStack(LightsailDatabaseMixin, LightsailBase):
    """
    AWS Lightsail Database Infrastructure Stack.

    A comprehensive database stack that deploys:
        * Lightsail Database instance with PostgreSQL
        * Multiple databases within the instance (automated creation)
        * Individual database users with scoped permissions (automated creation)
        * Secrets Manager for storing all database credentials
        * IAM resources for programmatic access

    :param scope: The construct scope
    :param id: The construct ID
    :param kwargs: Configuration parameters including databases array

    Example:
        >>> stack = LightsailDatabaseStack(
        ...     app, "my-db-stack",
        ...     region="ca-central-1",
        ...     project_name="my-app",
        ...     databases=["app_db", "analytics_db", "logs_db"],
        ...     postApplyScripts=[
        ...         "echo 'Database deployment completed'",
        ...         "psql -h $DB_HOST -U master -d postgres -c '\\l'"
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
        return DatabaseArchitectureFlags

    def __init__(self, scope, id, **kwargs):
        """
        Initialize the AWS Lightsail Database Infrastructure Stack.

        :param scope: The construct scope
        :param id: Unique identifier for this stack
        :param kwargs: Configuration parameters

        **Configuration Parameters:**

        :param region: AWS region (default: "us-east-1")
        :param environment: Environment name (default: "dev")
        :param project_name: Project identifier (default: "bb-aws-lightsail-db")
        :param databases: List of database names to create (required)
        :param flags: List of ArchitectureFlags to modify behavior
        :param profile: AWS profile to use (default: "default")
        :param postApplyScripts: List of shell commands to execute after deployment
        :param secret_name: Custom secret name (default: "{project_name}/{environment}/database-credentials")
        :param db_instance_size: Database instance size (default: "micro_2_0")
        :param db_engine: Database engine version (default: "postgres_14")
        :param master_username: Master database username (default: "dbmasteruser")
        :param db_publicly_accessible: Enable public access to database (default: True, required for automated provisioning)
        """
        # Set database-specific defaults
        if "project_name" not in kwargs:
            kwargs["project_name"] = "bb-aws-lightsail-db"
        if "secret_name" not in kwargs:
            project_name = kwargs["project_name"]
            environment = kwargs.get("environment", "dev")
            kwargs["secret_name"] = f"{project_name}/{environment}/database-credentials"
        
        # ===== Database-Specific Configuration (MUST be set before super().__init__) =====
        self.databases = kwargs.get("databases", [])

        # Validate required parameters
        if not self.databases:
            raise ValueError("The 'databases' parameter is required and must contain at least one database name")

        # ===== Database Configuration =====
        self.master_username = kwargs.get("master_username", "dbmasteruser")
        self.db_instance_size = kwargs.get("db_instance_size", "micro_2_0")
        self.db_engine = kwargs.get("db_engine", "postgres_14")
        self.db_publicly_accessible = kwargs.get("db_publicly_accessible", True)

        # ===== Internal State =====
        self.database_users = {}
        self.database_passwords = {}
        
        # Call parent constructor (this will call _set_default_post_apply_scripts)
        super().__init__(scope, id, **kwargs)
