"""
Shared Lightsail architecture flags.
"""

from enum import Enum


class BaseLightsailArchitectureFlags(Enum):
    """
    Base architecture configuration flags for optional components.
    """

    SKIP_DEFAULT_POST_APPLY_SCRIPTS = "skip_default_post_apply_scripts"
    PRESERVE_EXISTING_SECRETS = "preserve_existing_secrets"
    IGNORE_SECRET_CHANGES = "ignore_secret_changes"


class ContainerArchitectureFlags(Enum):
    """
    Architecture configuration flags for container stacks.
    """

    SKIP_DEFAULT_POST_APPLY_SCRIPTS = "skip_default_post_apply_scripts"
    PRESERVE_EXISTING_SECRETS = "preserve_existing_secrets"
    IGNORE_SECRET_CHANGES = "ignore_secret_changes"
    SKIP_DATABASE = "skip_database"
    SKIP_DOMAIN = "skip_domain"


class DatabaseArchitectureFlags(Enum):
    """
    Architecture configuration flags for database stacks.
    """

    SKIP_DEFAULT_POST_APPLY_SCRIPTS = "skip_default_post_apply_scripts"
    PRESERVE_EXISTING_SECRETS = "preserve_existing_secrets"
    IGNORE_SECRET_CHANGES = "ignore_secret_changes"
    SKIP_DATABASE_USERS = "skip_database_users"
