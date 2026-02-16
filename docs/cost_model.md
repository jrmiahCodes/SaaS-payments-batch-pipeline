# Cost Model

## Cost Drivers In AWS Deployments

1. Storage (S3): Bronze + Silver + Gold + state artifacts.
2. Query scans (Athena, optional): bytes scanned per query and partition pruning quality.
3. Compute (if migrated from Actions): ECS/Lambda runtime and memory.
4. Data transfer and API overhead (usually secondary for this footprint).

## Back-Of-Napkin Sizing

Assumptions:

- `R` = records per day
- Bronze JSONL average size = `B_json` bytes/record
- Silver/Gold Parquet compression ratio ~ 4:1 vs raw JSON
- Retention: Bronze `D_b` days, Silver `D_s` days, Gold `D_g` days

Approx monthly storage:

- Bronze GB = `(R * B_json * D_b) / 1e9`
- Silver GB = `(R * B_json / 4 * D_s) / 1e9`
- Gold GB = `(R * B_json / 6 * D_g) / 1e9` (curated, fewer cols)

Example:

- `R=200,000`, `B_json=900`, `D_b=14`, `D_s=90`, `D_g=365`
- Bronze ~ 2.52 GB
- Silver ~ 4.05 GB
- Gold ~ 10.95 GB

The main cost risk is query scan inefficiency, not raw storage, at this scale.

## Cost Control Levers

- Use Parquet for Silver/Gold.
- Partition by `dt` and always filter by `dt` in queries.
- Apply lifecycle expiration for Bronze aggressively.
- Keep Gold compact and purpose-built.
- Avoid tiny files; batch records into fewer larger objects.

## Suggested Lifecycle Defaults

- Bronze: transition or expire after 14-30 days.
- Silver: retain 90-180 days.
- Gold: retain 365+ days based on analytics requirements.
- State/manifests: retain long-term for lineage/debugging.

## Budget Guardrails

Suggested AWS Budgets alarms (monthly):

- Warning: $10
- Critical: $25
- Hard review threshold: $50

If alerts trigger:

1. Inspect Athena scan bytes and top queries.
2. Validate partition filters are applied.
3. Reduce Bronze retention.
4. Revisit file sizing and compaction patterns.
