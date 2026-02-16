CREATE OR REPLACE TABLE payment_intents AS
SELECT
  CAST(data.id AS VARCHAR) AS id,
  CAST(data.created AS BIGINT) AS created,
  to_timestamp(CAST(data.created AS BIGINT)) AS created_ts,
  CAST(data.amount AS BIGINT) AS amount,
  CAST(data.currency AS VARCHAR) AS currency,
  CAST(data.status AS VARCHAR) AS status,
  CAST(data.customer AS VARCHAR) AS customer_id,
  CAST(data.invoice AS VARCHAR) AS invoice_id,
  CAST(data.latest_charge AS VARCHAR) AS latest_charge_id,
  CAST(substr(meta.ingested_at, 1, 10) AS DATE) AS dt
FROM read_json_auto(
  '{{LOCAL_DATA_DIR}}/bronze/source=stripe/entity=payment_intents/dt=*/run_id=*/part-*.jsonl',
  format = 'newline_delimited',
  union_by_name = true
);
