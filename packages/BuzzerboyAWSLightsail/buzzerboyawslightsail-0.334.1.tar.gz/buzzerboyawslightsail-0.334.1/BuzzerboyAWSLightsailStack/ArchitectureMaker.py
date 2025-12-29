"""
ArchitectureMaker
=================

Helper routines to build common Lightsail architectures using CDKTF.
"""

from typing import Any, Dict, List

from cdktf import App

from BuzzerboyAWSLightsailStack.LightsailDatabase import (
    LightsailDatabaseStack,
)
from BuzzerboyAWSLightsailStack.LightsailDatabaseStandalone import (
    LightsailDatabaseStandaloneStack,
)
from BuzzerboyAWSLightsailStack.LightsailContainer import (
    LightsailContainerStack,
)
from BuzzerboyAWSLightsailStack.LightsailContainerStandalone import (
    LightsailContainerStandaloneStack,
)
from BuzzerboyArchetypeStack.BuzzerboyArchetype import BuzzerboyArchetype


class ArchitectureMaker:
    """
    Factory utilities for building Lightsail architectures from a definition dict.
    """

    @staticmethod
    def auto_stack_db_only(definition: Dict[str, Any], include_compliance: bool = False) -> App:
        """
        Create a DB-only Lightsail stack from a definition dictionary.

        Expected keys in definition:
            - product (str)
            - name or app (str)
            - tier (str)
            - organization (str)
            - region (str)
            - databases (list[str])
        Optional keys:
            - profile (str)
            - db_instance_size (str)
            - master_username (str)
            - flags (list[str])
        """
        if not isinstance(definition, dict):
            raise ValueError("definition must be a dictionary")

        product = definition.get("product")
        app_name = definition.get("name") or definition.get("app")
        tier = definition.get("tier")
        organization = definition.get("organization")
        region = definition.get("region")
        databases = definition.get("databases", [])

        missing = [key for key, value in {
            "product": product,
            "name/app": app_name,
            "tier": tier,
            "organization": organization,
            "region": region,
            "databases": databases,
        }.items() if not value]
        if missing:
            raise ValueError(f"definition is missing required keys: {', '.join(missing)}")

        archetype = BuzzerboyArchetype(
            product=product,
            app=app_name,
            tier=tier,
            organization=organization,
            region=region,
        )

        flags: List[str] = list(definition.get("flags", []))
        flags = list(dict.fromkeys(flags))

        app = App()

        stack_class = LightsailDatabaseStack if include_compliance else LightsailDatabaseStandaloneStack
        stack_class(
            app,
            f"{archetype.get_project_name()}-db-stack",
            project_name=archetype.get_project_name(),
            environment=archetype.get_tier(),
            region=archetype.get_region(),
            secret_name=archetype.get_secret_name(),
            databases=databases,
            profile=definition.get("profile", "default"),
            db_instance_size=definition.get("db_instance_size", "micro_2_0"),
            master_username=definition.get("master_username", "dbmasteruser"),
            flags=flags,
        )

        app.synth()
        return app

    @staticmethod
    def auto_main_container_only(definition: Dict[str, Any], include_compliance: bool = False) -> App:
        """
        Create a container-only Lightsail stack from a definition dictionary.

        Expected keys in definition:
            - product (str)
            - name or app (str)
            - tier (str)
            - organization (str)
            - region (str)
        Optional keys:
            - profile (str)
            - flags (list[str])
        """
        if not isinstance(definition, dict):
            raise ValueError("definition must be a dictionary")

        product = definition.get("product")
        app_name = definition.get("name") or definition.get("app")
        tier = definition.get("tier")
        organization = definition.get("organization")
        region = definition.get("region")

        missing = [key for key, value in {
            "product": product,
            "name/app": app_name,
            "tier": tier,
            "organization": organization,
            "region": region,
        }.items() if not value]
        if missing:
            raise ValueError(f"definition is missing required keys: {', '.join(missing)}")

        archetype = BuzzerboyArchetype(
            product=product,
            app=app_name,
            tier=tier,
            organization=organization,
            region=region,
        )

        flags: List[str] = list(definition.get("flags", []))
        flags.extend([
            "skip_database",
            "skip_domain",
        ])
        flags = list(dict.fromkeys(flags))

        app = App()

        stack_class = LightsailContainerStack if include_compliance else LightsailContainerStandaloneStack
        stack_class(
            app,
            f"{archetype.get_project_name()}-stack",
            project_name=archetype.get_project_name(),
            environment=archetype.get_tier(),
            region=archetype.get_region(),
            secret_name=archetype.get_secret_name(),
            profile=definition.get("profile", "default"),
            flags=flags,
        )

        app.synth()
        return app

    @staticmethod
    def auto_main(definition: Dict[str, Any], include_compliance: bool = False) -> App:
        """
        Create a container + database Lightsail stack from a definition dictionary.

        Expected keys in definition:
            - product (str)
            - name or app (str)
            - tier (str)
            - organization (str)
            - region (str)
        Optional keys:
            - profile (str)
            - flags (list[str])
        """
        if not isinstance(definition, dict):
            raise ValueError("definition must be a dictionary")

        product = definition.get("product")
        app_name = definition.get("name") or definition.get("app")
        tier = definition.get("tier")
        organization = definition.get("organization")
        region = definition.get("region")

        missing = [key for key, value in {
            "product": product,
            "name/app": app_name,
            "tier": tier,
            "organization": organization,
            "region": region,
        }.items() if not value]
        if missing:
            raise ValueError(f"definition is missing required keys: {', '.join(missing)}")

        archetype = BuzzerboyArchetype(
            product=product,
            app=app_name,
            tier=tier,
            organization=organization,
            region=region,
        )

        flags: List[str] = list(definition.get("flags", []))
        flags.append("skip_domain")
        flags = list(dict.fromkeys(flags))

        app = App()

        stack_class = LightsailContainerStack if include_compliance else LightsailContainerStandaloneStack
        stack_class(
            app,
            f"{archetype.get_project_name()}-stack",
            project_name=archetype.get_project_name(),
            environment=archetype.get_tier(),
            region=archetype.get_region(),
            secret_name=archetype.get_secret_name(),
            profile=definition.get("profile", "default"),
            flags=flags,
        )

        app.synth()
        return app
