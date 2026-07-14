-- Grants for EMP_DEPT_SP in RAW layer.
-- grant_role is resolved from deployment/config/deployment.yml:
--   snowflake/grants/RAW/... -> grant_roles.RAW (e.g. FR_dev_elt_role on DEV)

GRANT OWNERSHIP ON PROCEDURE EMP_DEPT_SP()
    TO ROLE {{ grant_role }}
    COPY CURRENT GRANTS;
