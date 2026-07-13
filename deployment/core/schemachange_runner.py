"""
Author  : Abhijit Bangal
Project : Snowflake CI/CD Framework

Execute SchemaChange per database/schema folder target.
"""

import os
import subprocess
import sys

from deployment.core.schema_discovery import SchemaDiscovery


class SchemaChangeRunner:
    """Run schemachange deploy for each discovered schema target."""

    def __init__(
        self,
        deployment_config,
        schemachange_config,
        logger,
        environment,
        dry_run=False,
    ):
        self.deployment_config = deployment_config
        self.schemachange_config = schemachange_config
        self.logger = logger
        self.environment = environment
        self.dry_run = dry_run

    def execute(self):
        """Deploy all pending migrations grouped by folder-derived database/schema."""

        history_table = self._history_table()
        deployment_order = self.deployment_config["deployment_order"]
        root_folder = self.deployment_config["schemachange"]["root_folder"]

        discovery = SchemaDiscovery(root_folder, deployment_order)
        targets = discovery.discover_targets()

        if not targets:
            self.logger.warning(
                "No database/schema targets with SQL files were discovered."
            )
            return

        self.logger.info(
            f"Discovered {len(targets)} database/schema target(s) for deployment."
        )

        create_history_table = self.deployment_config["schemachange"].get(
            "create_change_history_table",
            True,
        )

        history_created = False
        total_runs = 0

        for target in targets:
            database = target.snowflake_database(self.environment)

            self.logger.info(
                f"Deploying target: {database}.{target.schema}"
            )

            for object_type in deployment_order:
                roots = discovery.deployment_roots(target, object_type)

                for root_folder_path in roots:
                    self._run_schemachange(
                        root_folder=str(root_folder_path),
                        database=database,
                        schema=target.schema,
                        history_table=history_table,
                        create_history_table=(
                            create_history_table and not history_created
                        ),
                        object_type=object_type,
                    )
                    history_created = True
                    total_runs += 1

        if total_runs == 0:
            self.logger.warning(
                "No SQL migration folders were found for deployment."
            )
            return

        self.logger.info(
            f"SchemaChange completed successfully across {total_runs} folder(s)."
        )

    def _history_table(self) -> str:
        history_tables = self.deployment_config["schemachange"]["history_table"]

        if self.environment not in history_tables:
            raise ValueError(
                f"No change history table configured for environment: "
                f"{self.environment}"
            )

        return history_tables[self.environment]

    def _run_schemachange(
        self,
        root_folder,
        database,
        schema,
        history_table,
        create_history_table,
        object_type,
    ):
        schemachange_settings = self.deployment_config["schemachange"]
        snowflake_settings = self.deployment_config["snowflake"]

        command = [
            sys.executable,
            "-m",
            "schemachange",
            "deploy",
            "-f",
            root_folder,
            "-c",
            history_table,
            "-d",
            database,
            "-s",
            schema,
            "-a",
            snowflake_settings["account"],
            "-u",
            snowflake_settings["user"],
            "-r",
            snowflake_settings["role"],
            "-w",
            snowflake_settings["warehouse"],
            "--snowflake-authenticator",
            "snowflake_jwt",
            "--snowflake-private-key-file",
            snowflake_settings["private_key_path"],
            "-L",
            self.schemachange_config.get("log_level", "INFO"),
        ]

        if schemachange_settings.get("autocommit", True):
            command.append("-ac")

        if create_history_table:
            command.append("--create-change-history-table")

        if self.dry_run:
            command.append("--dry-run")

        version_regex = self.schemachange_config.get(
            "version_number_validation_regex"
        )
        if version_regex:
            command.extend(
                ["--version-number-validation-regex", version_regex]
            )

        self.logger.info(
            f"Running SchemaChange for {object_type}: "
            f"{database}.{schema} -> {root_folder}"
        )

        env = os.environ.copy()
        passphrase = snowflake_settings.get("private_key_passphrase")

        if passphrase:
            env["SNOWFLAKE_PRIVATE_KEY_FILE_PWD"] = passphrase

        result = subprocess.run(
            command,
            text=True,
            env=env,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"SchemaChange failed for {database}.{schema} "
                f"({object_type}) in {root_folder}."
            )
