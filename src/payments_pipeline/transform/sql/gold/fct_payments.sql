CREATE OR REPLACE TABLE fct_payments AS
SELECT
  c.id AS id,
  c.id AS charge_id,
  c.payment_intent_id,
  p.customer_id,
  c.invoice_id,
  c.amount AS charge_amount,
  p.amount AS intent_amount,
  c.currency,
  c.status AS charge_status,
  p.status AS intent_status,
  coalesce(c.created_ts, p.created_ts) AS event_ts,
  coalesce(c.dt, p.dt) AS dt
FROM charges c
LEFT JOIN payment_intents p
  ON c.payment_intent_id = p.id;
