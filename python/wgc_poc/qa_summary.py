"""Post-load QA summary. Credentials come from the LINKED BigQuery connection."""
import json, os
from google.cloud import bigquery
from google.oauth2 import service_account
from orchestra_sdk.orchestra import OrchestraSDK


def main() -> None:
    dataset = os.environ["BQ_DATASET"]
    country = os.environ["SOURCE_COUNTRY"]
    year = int(os.environ["SOURCE_YEAR"])

    orchestra = OrchestraSDK(api_key=os.environ["ORCHESTRA_API_KEY"])
    bq = orchestra.get_linked_connection(
        "gcp_big_query", connection_id=os.environ["BQ_CONNECTION_ID"]
    )
    sa_info = bq.get("service_account_json")
    if isinstance(sa_info, str):
        sa_info = json.loads(sa_info)

    client = bigquery.Client(
        project=sa_info["project_id"],
        credentials=service_account.Credentials.from_service_account_info(sa_info),
        location=bq.get("location"),
    )

    job = client.query(
        f"""SELECT COUNT(*) AS rows_loaded,
                   COUNTIF(qty_kg IS NULL) AS null_qty_rows,
                   SUM(qty_kg) AS total_qty_kg
            FROM `{dataset}.reported_volumes_raw`
            WHERE source_country = @country AND source_year = @year""",
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("country", "STRING", country),
            bigquery.ScalarQueryParameter("year", "INT64", year),
        ]),
    )
    row = next(iter(job.result()))
    print(f"{country} {year}: rows={row.rows_loaded} nulls={row.null_qty_rows} kg={row.total_qty_kg}")

    orchestra.set_output("rows_loaded", int(row.rows_loaded))
    orchestra.set_output("null_qty_rows", int(row.null_qty_rows))

    if row.rows_loaded == 0:
        raise SystemExit(f"No rows loaded for {country} {year} - check the source CSV.")


if __name__ == "__main__":
    main()