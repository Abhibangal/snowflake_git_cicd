-- Snowpark stored procedure sourced from the Snowflake Git Repository.
-- Python source lives under snowflake/snowpark/.../src/
-- git_branch is injected at deploy time: dev for DEV, main for PROD.
-- Update GRANT OWNERSHIP role below per environment / object as needed.

CREATE OR REPLACE PROCEDURE EMP_DEPT_SP()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
IMPORTS = (
    '@{{ git_repository }}/branches/{{ git_branch }}/snowflake/snowpark/RAW/CUSTOMER_HUB/EMP_DEPT_SP/src/main.py'
)
HANDLER = 'run'
EXECUTE AS OWNER;

GRANT OWNERSHIP ON PROCEDURE EMP_DEPT_SP()
    TO ROLE FINANCE_CUSTOMER360_DEV_ADMIN
    COPY GRANTS;
