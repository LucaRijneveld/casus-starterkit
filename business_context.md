# Business context: Social Deal revenue data

## Which database to use

This project contains two SQLite databases:

- `socialdeal_casus.sqlite` is the source database. It contains the original, intentionally imperfect data and customer-identifying columns.
- `socialdeal_clean.sqlite` is the prepared copy for reporting. Use it for normal revenue answers. It excludes direct customer identifiers and adds normalized reporting fields.

Use the named tools in `revenue.py` as the supported interface for this case. `src_sql` is scoped to the source database and `clean_sql` to the clean database. Do not assume that a separate, general-purpose SQL tool or broader database access is available.

Use the query tools only for targeted, read-only inspection. Never submit modifying statements. Do not select or return direct identifiers from the source database.

## Evidence and grounding

All of Claude's reasoning, explanations, and conclusions must be grounded in the actual data available in these databases or returned by the named tools. Do not invent values or present assumptions as facts. If the available data does not answer a question, say so clearly and identify what evidence is missing.

## Source dataset

`socialdeal_casus.sqlite` contains fictional data from October 2024 through September 2026, with approximately 97,000 sales.

| Table | Approx. rows | Important columns |
| --- | ---: | --- |
| `steden` | 34 | `id`, `naam`, `land` (NL/BE), `regio` |
| `partners` | 613 | `id`, `naam`, `stad_id`, `is_test` |
| `deals` | 2,444 | `id`, `partner_id`, `titel`, `start_datum`, `eind_datum`, `prijs_cent`, `commissie_pct` |
| `verkopen` | 96,947 | `id`, `deal_id`, `aangemaakt_op`, `verwerkt_op`, `status`, `aantal`, `klantprijs_cent`, `commissie_cent`, `klant_email`, `betaalreferentie` |

Relationships:

- `verkopen.deal_id` → `deals.id`
- `deals.partner_id` → `partners.id`
- `partners.stad_id` → `steden.id`

`klant_email` and `betaalreferentie` are personal or payment-related data. Never include them in a query result, tool output, error message, or log. Prefer the clean database for analysis.

## Clean database

The clean database keeps the source names with a `clean_` prefix and adds reporting-oriented fields:

| Table or view | Contents |
| --- | --- |
| `clean_steden` | `id`, `naam`, `land`, `regio`; text encoding issues are repaired where possible. |
| `clean_partners` | `id`, `naam`, `stad_id`, `is_test`; partner names are repaired where possible. |
| `clean_deals` | Source deal fields plus `partner_is_test`, copied from the associated partner. |
| `clean_verkopen` | Sale fields excluding `klant_email` and `betaalreferentie`, plus the derived fields listed below. |
| `omzet_verkopen` | View of `clean_verkopen` containing only rows where `telt_mee_voor_omzet = 1`. |
| `dq_log` | Cleaning summary with `description`, `row_count`, `source_tz`, and `created_at`. |

Additional columns on `clean_verkopen`:

- `klant_id`: pseudonymous, salted hash derived from the email. It is not needed for revenue reporting; treat it as sensitive and do not expose it.
- `status_clean`: trimmed, lowercase status (`betaald`, `geannuleerd`, or `terugbetaald`).
- `partner_is_test`: whether the sale belongs to a test partner.
- `telt_mee_voor_omzet`: `1` only for paid sales from non-test partners; otherwise `0`.
- `aangemaakt_op_nl` and `verwerkt_op_nl`: purchase and processing timestamps converted to Europe/Amsterdam time (the build script defaults to UTC as the source timezone).

The build process repairs common broken text encoding, normalizes statuses, converts timestamps, omits direct customer identifiers, and records cleaning counts in `dq_log`. The clean database preserves the sale amounts as stored; it does not multiply them by voucher quantity.

## Reporting rules

- Revenue means Social Deal's commission: sum `commissie_cent`. `klantprijs_cent` is the customer's purchase amount, not revenue.
- Count only paid sales from non-test partners. In the clean database, use `telt_mee_voor_omzet = 1` or the `omzet_verkopen` view.
- Attribute a sale to its purchase time (`aangemaakt_op`), not its processing time (`verwerkt_op`).
- Use the Amsterdam-local purchase timestamp (`aangemaakt_op_nl`) for reporting dates.
- Date ranges are inclusive: include both the start date and the end date.
- A sale row can represent multiple vouchers (`aantal`). `commissie_cent` and `klantprijs_cent` are already totals for the row; do not multiply them by `aantal`.
- Attribute a sale to the city of its partner.
- Amounts are integer cents. Convert to euros only for presentation (divide by 100).

## Duplicate city names

Some different city records share a name, such as Bergen and Laren. `omzet_per_stad` groups by city ID, not just by name, and includes the city ID, name, country, and region in each row. This keeps same-named cities separate and makes their locations clear.

## Duplicate partner names

Partner names are not unique; the same name can occur under multiple partner IDs, including in the same city. The data does not establish whether those IDs represent one business or separate partner records.

`omzet_per_partner` and `top_partners` therefore return two views for the requested period, each sorted by revenue descending:

1. **Separate partners (by ID):** one row per partner ID, with its name and city. Use this view when identifying or comparing individual partner records.
2. **Combined by exact partner name and city:** sums rows that have the same name and city. This is a useful roll-up, but it is not proof that the IDs belong to one real-world business. Names in different cities are not combined.

Both tools limit each view separately. `omzet_per_partner` defaults to the top 5 rows per view and accepts an optional `n` to request more or fewer. `top_partners` also defaults to 5 per view. When discussing partner-level results, state which view is being used; prefer the ID-separated view when the distinction matters.

## Tools and when they are useful

Call `data_context` first to load these definitions before analyzing the data. Use the clean-data reporting tools for business answers; use source comparisons to investigate discrepancies, not as the authoritative finance total.

| Tool | Inputs | What it does and why it is useful |
| --- | --- | --- |
| `data_context` | none | Returns this document. It establishes the schema, definitions, and safe-use rules so that later queries use the right database and revenue logic. |
| `exploratory_data_analysis` | none | Reports source-table schemas, row counts, numeric distinct counts, null counts, and sample rows. Useful for initial schema and quality exploration. It omits `klant_email` and `betaalreferentie` from sample rows; use the clean database for further analysis. |
| `src_sql` | `query` | Runs a targeted, read-only query against the original source database and returns rows. Useful for investigating raw values or diagnosing how the source differs from the clean copy. Never select personal or payment data. |
| `clean_sql` | `query` | Runs a targeted, read-only query against the clean database and returns rows. Useful for checking cleaned values, validating a reporting calculation, or inspecting `dq_log`. Avoid `klant_id` unless an explicitly approved analysis requires it. |
| `omzet_per_stad` | `start_date`, `end_date` | Sums eligible commission by city ID for an inclusive Amsterdam-local date range. Includes city ID, name, country, and region so same-named cities remain separate and distinguishable. |
| `omzet_per_partner` | `start_date`, `end_date`, optional `n` (default 5) | Returns the top `n` partner-ID-separated totals and top `n` totals combined by exact name and city, sorted by revenue descending for an inclusive date range. Useful for comparing individual partner records with a concise name-based roll-up. |
| `zoek_stad` | `naam` | Searches city names by partial match and returns city ID, name, country, and region. Useful for resolving a city name before analyzing it. |
| `zoek_partner` | `naam` | Searches partner names by partial match and returns partner ID, name, city, and country. Useful for identifying a partner and its location. |
| `beschikbare_periode` | none | Returns the earliest and latest Amsterdam-local purchase timestamps in the clean sales table. Useful for checking whether a requested date range is covered by the data. |
| `omzet_per_maand` | `start_date`, `end_date` | Groups eligible commission into months within an inclusive date range. Useful for seeing trends and seasonality without querying every day separately. |
| `vergelijk_periode` | `start_date_1`, `end_date_1`, `start_date_2`, `end_date_2` | Calculates eligible commission for two independently specified inclusive date ranges. Useful for like-for-like period comparisons. |
| `top_partners` | `start_date`, `end_date`, optional `n` (default 5) | Returns the top `n` partner IDs and the top `n` exact name-and-city groups by eligible commission in an inclusive date range. Useful for finding leading contributors without silently merging duplicate names. |
| `reconciliate_clean` | `start_datum`, `eind_datum` | Calculates the clean-data baseline and the variance from several one-rule-at-a-time alternatives, such as using processing date, including test partners, using customer price, multiplying by voucher quantity, or excluding the end date. Useful for explaining a discrepancy and quantifying common reporting mistakes. |
| `reconciliate_rapport` | `start_datum`, `eind_datum`, `bedrag_cent`, optional `vouchers` | Tries all 128 combinations of purchase/processing date, Amsterdam/raw timestamp, test-partner inclusion, status inclusion, end-date handling, commission/customer price, and quantity multiplication. It returns every exact amount match (and requires the voucher count to match too, if supplied), ordered by fewest deviations from the reporting rules. If there is no exact match, it returns the three closest amounts, with voucher differences when a count was supplied. Useful when another team reports a discrepancy and you want to test combinations of mistakes. This is diagnostic only; use `reconciliate_clean` for the authoritative baseline. |

All date inputs should be ISO dates in `YYYY-MM-DD` form. If a tool reports no matching data, verify the date range and spelling before drawing a conclusion.
