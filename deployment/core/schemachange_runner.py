"""
Author  : Abhijit Bangal
Project : Snowflake CI/CD Framework

Execute SchemaChange per database/schema folder target.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from deployment.core.schema_discovery import SchemaDiscovery


def _schemachange_executable() -> str:
    """Return the schemachange CLI path installed in the current environment."""

    executable = shutil.which("schemachange")

    if executable:
        return executable

    venv_executable = Path(sys.executable).parent / "schemachange"

    if venv_executable.exists():
        return str(venv_executable)

    raise RuntimeError(
        "schemachange CLI not found. Install requirements.txt before deploying."
    )


class SchemaChangeRunner:
    """Run schemachange deploy for each discovered schema target."""

    CONNECTIONS_FILE = "connections.toml"
    CONNECTION_NAME = "cicd"

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
        self.connections_file = None

    def execute(self):
        """Deploy all pending migrations grouped by folder-derived database/schema."""

        self.connections_file = self._write_connections_toml()

        try:
            self._execute_deployments()
        finally:
            if self.connections_file and self.connections_file.exists():
                self.connections_file.unlink()

    def _execute_deployments(self):
        """Run schemachange for all discovered schema targets."""

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

    def _git_branch(self) -> str:
        branch_map = self.deployment_config.get("git", {}).get(
            "branch",
            {"DEV": "dev", "PROD": "main"},
        )

        if self.environment not in branch_map:
            raise ValueError(
                f"No Git branch configured for environment: {self.environment}"
            )

        return branch_map[self.environment]

    def _schemachange_vars(self) -> dict:
        git_config = self.deployment_config.get("git", {})

        return {
            "git_repository": git_config["repository_name"],
            "git_branch": self._git_branch(),
        }

    def _write_connections_toml(self) -> Path:
        """Write a Snowflake connections file for schemachange 4.x."""

        snowflake_settings = self.deployment_config["snowflake"]
        connections_path = Path(self.CONNECTIONS_FILE)
        passphrase = snowflake_settings.get("private_key_passphrase", "")
        passphrase = passphrase.strip() if isinstance(passphrase, str) else ""

        lines = [
            f"[{self.CONNECTION_NAME}]",
            f'account = "{snowflake_settings["account"]}"',
            f'user = "{snowflake_settings["user"]}"',
            f'role = "{snowflake_settings["role"]}"',
            f'warehouse = "{snowflake_settings["warehouse"]}"',
            'authenticator = "snowflake_jwt"',
            f'private_key_file = "{snowflake_settings["private_key_path"]}"',
        ]

        if passphrase:
            lines.append(f'private_key_file_pwd = "{passphrase}"')

        connections_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        connections_path.chmod(0o600)

        self.logger.info(
            f"Created SchemaChange connections file: {connections_path}"
        )

        return connections_path

    def _build_subprocess_env(self, database, schema, snowflake_settings):
        """Build environment variables for the schemachange subprocess."""

        env = os.environ.copy()
        env.update(
            {
                "SNOWFLAKE_ACCOUNT": snowflake_settings["account"],
                "SNOWFLAKE_USER": snowflake_settings["user"],
                "SNOWFLAKE_ROLE": snowflake_settings["role"],
                "SNOWFLAKE_WAREHOUSE": snowflake_settings["warehouse"],
                "SNOWFLAKE_DATABASE": database,
                "SNOWFLAKE_SCHEMA": schema,
                "SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt",
                "SNOWFLAKE_PRIVATE_KEY_FILE": snowflake_settings[
                    "private_key_path"
                ],
            }
        )

        passphrase = snowflake_settings.get("private_key_passphrase", "")
        passphrase = passphrase.strip() if isinstance(passphrase, str) else ""

        if passphrase:
            env["SNOWFLAKE_PRIVATE_KEY_FILE_PWD"] = passphrase

        return env

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

        schemachange_vars = self._schemachange_vars()

        command = [
            _schemachange_executable(),
            "deploy",
            "--config-folder",
            "deployment/config",
            "-f",
            root_folder,
            "-c",
            history_table,
            "-d",
            database,
            "-s",
            schema,
            "-V",
            json.dumps(schemachange_vars),
            "-C",
            self.CONNECTION_NAME,
            "--schemachange-connections-file-path",
            str(self.connections_file),
            "-L",
            self.schemachange_config.get("log_level", "INFO"),
        ]

        self.logger.info(
            f"SchemaChange vars: git_branch={schemachange_vars['git_branch']}, "
            f"git_repository={schemachange_vars['git_repository']}"
        )

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

        env = self._build_subprocess_env(database, schema, snowflake_settings)

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
