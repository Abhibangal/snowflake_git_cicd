"""
Author  : Abhijit Bangal
Project : Snowflake CI/CD Framework

Build Jinja variables injected at deploy time.
"""

DEFAULT_LAYER_CODES = {
    "RAW": "RAW",
    "TRANSFORM": "TRF",
    "CONSUMPTION": "CON",
}

DEFAULT_SCHEMA_CODES = {
    "CUSTOMER_HUB": "CUSTOMERHUB",
    "HUBSPOT": "HUBSPOT",
    "QUICKBOOKS": "QUICKBOOKS",
    "ASANA": "ASANA",
    "UTILS": "SDT",
}

ACCESS_PRIVILEGES = ("ALL", "RO", "RW")


def get_database_layers(deployment_config: dict) -> list[str]:
    """Return configured database layer names (RAW, TRANSFORM, etc.)."""

    configured_layers = deployment_config.get("database_layers")

    if configured_layers:
        return [layer.upper() for layer in configured_layers]

    layer_codes = deployment_config.get("access_roles", {}).get("layer_codes")

    if layer_codes:
        return sorted(layer.upper() for layer in layer_codes.keys())

    return ["RAW", "TRANSFORM", "CONSUMPTION"]


def build_databases(environment: str, layers: list[str]) -> dict[str, str]:
    """
    Map layer folder names to Snowflake database names for the environment.

    Example (DEV): RAW -> DEV_RAW, TRANSFORM -> DEV_TRANSFORM
    Example (PROD): RAW -> PROD_RAW, TRANSFORM -> PROD_TRANSFORM
    """

    env = environment.upper()
    return {layer.upper(): f"{env}_{layer.upper()}" for layer in layers}


def get_layer_codes(deployment_config: dict) -> dict[str, str]:
    configured = deployment_config.get("access_roles", {}).get("layer_codes", {})
    layer_codes = configured or DEFAULT_LAYER_CODES
    return {layer.upper(): code.upper() for layer, code in layer_codes.items()}


def get_schema_codes(deployment_config: dict) -> dict[str, str]:
    configured = deployment_config.get("access_roles", {}).get("schema_codes", {})
    schema_codes = configured or DEFAULT_SCHEMA_CODES
    return {schema.upper(): code.upper() for schema, code in schema_codes.items()}


def resolve_schema_code(schema_folder: str, schema_codes: dict[str, str]) -> str:
    normalized = schema_folder.upper()

    if normalized in schema_codes:
        return schema_codes[normalized]

    return normalized.replace("_", "")


def build_access_role(
    environment: str,
    layer: str,
    schema: str,
    privilege: str,
    deployment_config: dict,
) -> str:
    """
    Build AR role name: AR_{ENV}_{LAYER}_{SCHEMA}_{PRIVILEGE}

    Example: AR_DEV_RAW_CUSTOMERHUB_RW
    """

    layer_codes = get_layer_codes(deployment_config)
    schema_codes = get_schema_codes(deployment_config)

    layer_key = layer.upper()
    if layer_key not in layer_codes:
        raise ValueError(
            f"Unknown database layer '{layer}' for access role resolution."
        )

    layer_code = layer_codes[layer_key]
    schema_code = resolve_schema_code(schema, schema_codes)
    env = environment.upper()
    priv = privilege.upper()

    return f"AR_{env}_{layer_code}_{schema_code}_{priv}"


def build_access_roles_for_target(
    environment: str,
    layer: str,
    schema: str,
    deployment_config: dict,
) -> dict[str, str]:
    """Return ALL, RO, and RW access roles for one deploy target."""

    return {
        privilege: build_access_role(
            environment,
            layer,
            schema,
            privilege,
            deployment_config,
        )
        for privilege in ACCESS_PRIVILEGES
    }


def default_grant_privilege(deployment_config: dict) -> str:
    privilege = deployment_config.get("access_roles", {}).get(
        "default_privilege",
        "RW",
    )
    return privilege.upper()
