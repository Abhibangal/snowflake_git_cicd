"""
Handler for SP_PAYMENT_SUMMARY stored procedure.
This file should be committed to your Git repo at: handlers/payment_handler.py
"""
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, sum as sf_sum, count


def run(session: Session, p_status: str = None):
    payments_df = session.table("PAYMENTS")

    if p_status:
        payments_df = payments_df.filter(col("STATUS") == p_status)

    result = payments_df.group_by("PAYMENT_METHOD").agg(
        sf_sum("AMOUNT").alias("TOTAL_AMOUNT"),
        count("PAYMENT_ID").alias("TRANSACTION_COUNT")
    ).sort("TOTAL_AMOUNT", ascending=False)

    return result
