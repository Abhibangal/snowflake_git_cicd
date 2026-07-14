"""
Author  : Abhijit Bangal
Project : Snowflake CI/CD Framework

Validate grant_roles configuration for DEV and PROD environments.
"""

from pathlib import Path


class GrantRolesValidator:

    def __init__(self, logger, deployment_config, root_folder="snowflake"):
        self.logger = logger
        self.deployment_config = deployment_config
        self.grants_root = Path(root_folder) / "grants"

    def validate(self):

        if not self._has_grant_scripts():
            self.logger.info(
                "Skipping grant role validation (no grant SQL scripts found)."
            )
            return

        grant_roles = self.deployment_config.get("grant_roles")

        if not grant_roles:
            raise ValueError(
                "Grant SQL scripts exist but grant_roles is missing from "
                "deployment/config/deployment.yml."
            )

        missing = [
            environment
            for environment in ("DEV", "PROD")
            if environment not in grant_roles or not grant_roles[environment]
        ]

        if missing:
            raise ValueError(
                "grant_roles must define non-empty role maps for: "
                + ", ".join(missing)
            )

        required_layers = ("RAW", "TRANSFORM", "CONSUMPTION")
        for environment in ("DEV", "PROD"):
            layer_map = grant_roles[environment]
            missing_layers = [
                layer
                for layer in required_layers
                if layer not in layer_map or not str(layer_map[layer]).strip()
            ]
            if missing_layers:
                raise ValueError(
                    f"grant_roles.{environment} must define: "
                    + ", ".join(missing_layers)
                )

        self.logger.info("Grant role configuration validation successful.")

    def _has_grant_scripts(self) -> bool:
        if not self.grants_root.is_dir():
            return False

        return any(self.grants_root.rglob("*.sql"))
