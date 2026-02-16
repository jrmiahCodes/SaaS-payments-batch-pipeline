CREATE OR REPLACE TABLE dim_customers AS
SELECT
  id,
  max(created_ts) AS created_ts,
  max(email) AS email,
  max(name) AS name,
  max(dt) AS dt
FROM customers
GROUP BY id;
