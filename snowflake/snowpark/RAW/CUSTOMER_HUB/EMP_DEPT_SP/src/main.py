from snowflake.snowpark import Session


def run(session: Session) -> str:
    """Placeholder Snowpark handler for EMP / DEPARTMENT logic."""

    employee_count = session.table("EMP").count()
    department_count = session.table("DEPARTMENT").count()

    return (
        "Placeholder Snowpark SP - "
        f"EMP rows: {employee_count}, DEPARTMENT rows: {department_count}"
    )
