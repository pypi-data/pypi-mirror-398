from django.db import migrations

# https://wiki.postgresql.org/wiki/Count_estimate
CREATE_ESTIMATE_COUNT_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION django_pbx_admin_count_estimate(query text)
  RETURNS integer
  LANGUAGE plpgsql AS
$func$
DECLARE
    rec   record;
    rows  integer;
BEGIN
    FOR rec IN EXECUTE 'EXPLAIN ' || query LOOP
        rows := substring(rec."QUERY PLAN" FROM ' rows=([[:digit:]]+)');
        EXIT WHEN rows IS NOT NULL;
    END LOOP;

    RETURN rows;
END
$func$;
"""

DROP_ESTIMATE_COUNT_FUNCTION_SQL = (
    "DROP FUNCTION IF EXISTS django_pbx_admin_count_estimate(query text);"
)


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            CREATE_ESTIMATE_COUNT_FUNCTION_SQL, reverse_sql=DROP_ESTIMATE_COUNT_FUNCTION_SQL
        )
    ]
