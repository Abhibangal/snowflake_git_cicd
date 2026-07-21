"""
Author  : Abhijit Bangal
Project : Snowflake CI/CD Framework

Build Jinja variables injected at deploy time.
"""


def get_database_layers(deployment_config: dict) -> list[str]:
    """Return configured database layer names (RAW, TRANSFORM, etc.)."""

    configured_layers = deployment_config.get("database_layers")

    if configured_layers:
        return [layer.upper() for layer in configured_layers]

    grant_roles = deployment_config.get("grant_roles", {})
    layers: set[str] = set()

    for environment_roles in grant_roles.values():
        if isinstance(environment_roles, dict):
            layers.update(environment_roles.keys())

    if layers:
        return sorted(layer.upper() for layer in layers)

    return ["RAW", "TRANSFORM", "CONSUMPTION"]


def build_databases(environment: str, layers: list[str]) -> dict[str, str]:
    """
    Map layer folder names to Snowflake database names for the environment.

    Example (DEV): RAW -> DEV_RAW, TRANSFORM -> DEV_TRANSFORM
    Example (PROD): RAW -> PROD_RAW, TRANSFORM -> PROD_TRANSFORM
    """

    env = environment.upper()
    return {layer.upper(): f"{env}_{layer.upper()}" for layer in layers}
