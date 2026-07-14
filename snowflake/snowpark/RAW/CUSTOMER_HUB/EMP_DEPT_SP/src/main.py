from snowflake.snowpark import Session
from snowflake.snowpark.functions import col


def run(session: Session) -> str:
    """Read employee data from EMP table using current DB/schema context."""

    # Get the database and schema where this SP resides
    current_db = session.get_current_database().replace('"', '')
    current_schema = session.get_current_schema().replace('"', '')

    # Fully qualified table reference based on SP's own context
    table_fqn = f"{current_db}.{current_schema}.EMP"

    emp_df = session.table(table_fqn)
    emp_df = emp_df.select(
        col("ID"),
        col("NAME"),
        col("EMAIL"),
        col("DEPT_ID"),
        col("CREATED_AT")
    )

    row_count = emp_df.count()
    results = emp_df.collect()

    output = f"Database: {current_db} | Schema: {current_schema}\n"
    output += f"Total Employees: {row_count}\n"
    output += "-" * 50 + "\n"
    for row in results:
        output += (
            f"ID: {row['ID']} | Name: {row['NAME']} | "
            f"Email: {row['EMAIL']} | Dept: {row['DEPT_ID']}\n"
        )

    return output