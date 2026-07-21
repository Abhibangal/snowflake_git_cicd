"""
Handler for SP_PRODUCT_REPORT stored procedure.
This file should be committed to your Git repo at: handlers/product_handler.py
"""
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col


def run(session: Session, p_category: str = None):
    products_df = session.table("PRODUCTS")

    if p_category:
        products_df = products_df.filter(col("CATEGORY") == p_category)

    result = products_df.select(
        "PRODUCT_NAME", "CATEGORY", "PRICE", "STOCK_QUANTITY", "IS_ACTIVE"
    ).sort("PRICE", ascending=False)

    return result
