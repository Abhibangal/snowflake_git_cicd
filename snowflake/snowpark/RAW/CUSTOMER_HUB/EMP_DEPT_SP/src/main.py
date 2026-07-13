from snowflake.snowpark import Session
from snowflake.snowpark.functions import col


def run(session: Session) -> str:
    """Read employee data from the EMP table and return summary."""
    emp_df = session.table("EMP")

    emp_df = emp_df.select(
        col("ID"),
        col("NAME"),
        col("EMAIL"),
        col("DEPT_ID"),
        col("CREATED_AT")
    )

    row_count = emp_df.count()
    results = emp_df.collect()

    output = f"Total Employees: {row_count}\n"
    output += "-" * 40 + "\n"
    for row in results:
        output += f"ID: {row['ID']} | Name: {row['NAME']} | Email: {row['EMAIL']} | Dept: {row['DEPT_ID']}\n"

    return output
