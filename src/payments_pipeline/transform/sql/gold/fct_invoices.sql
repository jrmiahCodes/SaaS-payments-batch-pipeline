CREATE OR REPLACE TABLE fct_invoices AS
SELECT
  i.id AS id,
  i.id AS invoice_id,
  i.customer_id,
  i.total,
  i.amount_due,
  i.status,
  i.period_start,
  i.period_end,
  i.created_ts,
  i.dt
FROM invoices i;
