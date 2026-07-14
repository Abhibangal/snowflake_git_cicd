from snowflake.snowpark import functions as F


def run(session, min_order_count):
    """Read employee data from EMP table using current DB/schema context."""
    current_db = session.get_current_database().replace('"', '')
    current_schema = session.get_current_schema().replace('"', '')

    customers_tbl = session.table(f"{current_db}.{current_schema}.CUSTOMERS")
    orders_tbl = session.table(f"{current_db}.{current_schema}.ORDERS")

    result = (
        customers_tbl.join(orders_tbl, customers_tbl["CUSTOMER_ID"] == orders_tbl["CUSTOMER_ID"])
        .group_by(customers_tbl["CUSTOMER_ID"], customers_tbl["FIRST_NAME"], customers_tbl["LAST_NAME"])
        .agg(
            F.count(orders_tbl["ORDER_ID"]).alias("ORDER_COUNT"),
            F.sum(orders_tbl["TOTAL_AMOUNT"]).alias("TOTAL_SPENT")
        )
        .with_column("FULL_NAME", F.concat(F.col("FIRST_NAME"), F.lit(" "), F.col("LAST_NAME")))
        .filter(F.col("ORDER_COUNT") >= min_order_count)
        .select(customers_tbl["CUSTOMER_ID"], "FULL_NAME", "ORDER_COUNT", "TOTAL_SPENT")
    )

    return result