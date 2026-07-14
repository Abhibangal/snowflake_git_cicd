from snowflake.snowpark import functions as F
def run(session, min_order_count):

        """Read employee data from EMP table using current DB/schema context."""

    # Get the database and schema where this SP resides
    current_db = session.get_current_database().replace('"', '')
    current_schema = session.get_current_schema().replace('"', '')

    # Fully qualified table reference based on SP's own context
    customers = f"{current_db}.{current_schema}.CUSTOMERS"
    orders = f"{current_db}.{current_schema}.ORDERS"

    result = (
        customers.join(orders, customers["CUSTOMER_ID"] == orders["CUSTOMER_ID"])
        .group_by(customers["CUSTOMER_ID"], customers["FIRST_NAME"], customers["LAST_NAME"])
        .agg(
            F.count(orders["ORDER_ID"]).alias("ORDER_COUNT"),
            F.sum(orders["TOTAL_AMOUNT"]).alias("TOTAL_SPENT")
        )
        .with_column("FULL_NAME", F.concat(F.col("FIRST_NAME"), F.lit(" "), F.col("LAST_NAME")))
        .filter(F.col("ORDER_COUNT") >= min_order_count)
        .select("CUSTOMER_ID", "FULL_NAME", "ORDER_COUNT", "TOTAL_SPENT")
    )

    return result

