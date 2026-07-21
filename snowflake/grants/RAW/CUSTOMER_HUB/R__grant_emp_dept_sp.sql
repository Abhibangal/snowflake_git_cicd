-- Grants for EMP_DEPT_SP in RAW / CUSTOMER_HUB.
-- grant_role resolves from folder path + branch environment:
--   snowflake/grants/RAW/CUSTOMER_HUB/... -> AR_DEV_RAW_CUSTOMERHUB_RW on dev
--   same path on main                         -> AR_PROD_RAW_CUSTOMERHUB_RW

GRANT OWNERSHIP ON PROCEDURE EMP_DEPT_SP()
    TO ROLE {{ grant_role }}
    COPY CURRENT GRANTS;
