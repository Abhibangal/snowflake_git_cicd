-- Snowpark stored procedure sourced from the Snowflake Git Repository.
-- Python source lives under snowflake/snowpark/.../src/
-- git_branch is injected at deploy time: dev for DEV, main for PROD.
-- Grants are managed under snowflake/grants/ (not in this file).

CREATE OR REPLACE PROCEDURE EMP_DEPT_SP()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
IMPORTS = (
    '@{{ git_repository }}/branches/{{ git_branch }}/snowflake/snowpark/RAW/CUSTOMER_HUB/EMP_DEPT_SP/src/main.py'
)
HANDLER = 'main.run'
EXECUTE AS OWNER;
