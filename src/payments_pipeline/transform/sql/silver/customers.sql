CREATE OR REPLACE TABLE customers AS
SELECT
  CAST(data.id AS VARCHAR) AS id,
  CAST(data.created AS BIGINT) AS created,
  to_timestamp(CAST(data.created AS BIGINT)) AS created_ts,
  CAST(data.email AS VARCHAR) AS email,
  CAST(data.name AS VARCHAR) AS name,
  CAST(substr(meta.ingested_at, 1, 10) AS DATE) AS dt
FROM read_json_auto(
  '{{LOCAL_DATA_DIR}}/bronze/source=stripe/entity=customers/dt=*/run_id=*/part-*.jsonl',
  format = 'newline_delimited',
  union_by_name = true
);
