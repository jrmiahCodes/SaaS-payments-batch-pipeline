CREATE OR REPLACE TABLE invoices AS
SELECT
  CAST(data.id AS VARCHAR) AS id,
  CAST(data.created AS BIGINT) AS created,
  to_timestamp(CAST(data.created AS BIGINT)) AS created_ts,
  CAST(data.due_date AS BIGINT) AS due_date,
  CAST(data.period_start AS BIGINT) AS period_start,
  CAST(data.period_end AS BIGINT) AS period_end,
  CAST(data.status AS VARCHAR) AS status,
  CAST(data.total AS BIGINT) AS total,
  CAST(data.amount_due AS BIGINT) AS amount_due,
  CAST(data.customer AS VARCHAR) AS customer_id,
  CAST(substr(meta.ingested_at, 1, 10) AS DATE) AS dt
FROM read_json_auto(
  '{{LOCAL_DATA_DIR}}/bronze/source=stripe/entity=invoices/dt=*/run_id=*/part-*.jsonl',
  format = 'newline_delimited',
  union_by_name = true
);
