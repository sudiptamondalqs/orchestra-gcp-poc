"""Summarize the native and Python BigQuery loads for the selected slice."""
import json
import os

from google.cloud import bigquery
from google.oauth2 import service_account
from orchestra_sdk.orchestra import OrchestraSDK


def main() -> None:
    dataset = os.environ["BQ_DATASET"]
    country = os.environ["SOURCE_COUNTRY"]
    year = int(os.environ["SOURCE_YEAR"])

    orchestra = OrchestraSDK(api_key=os.environ["ORCHESTRA_API_KEY"])
    bq_connection = orchestra.get_linked_connection(
        "gcp_big_query", connection_id=os.environ["BQ_CONNECTION_ID"]
    )
    service_account_info = bq_connection["service_account_json"]
    if isinstance(service_account_info, str):
        service_account_info = json.loads(service_account_info)

    client = bigquery.Client(
        project=service_account_info["project_id"],
        credentials=service_account.Credentials.from_service_account_info(
            service_account_info
        ),
        location=bq_connection.get("location"),
    )

    job = client.query(
        f"""
        SELECT
          'native' AS implementation,
          COUNT(*) AS rows_loaded,
          COUNTIF(qty_kg IS NULL) AS null_qty_rows,
          SUM(qty_kg) AS total_qty_kg
        FROM `{dataset}.reported_volumes_raw`
        WHERE source_country = @country AND source_year = @year
        UNION ALL
        SELECT
          'python' AS implementation,
          COUNT(*) AS rows_loaded,
          COUNTIF(qty_kg IS NULL) AS null_qty_rows,
          SUM(qty_kg) AS total_qty_kg
        FROM `{dataset}.reported_volumes_raw_py`
        WHERE source_country = @country AND source_year = @year
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("country", "STRING", country),
                bigquery.ScalarQueryParameter("year", "INT64", year),
            ]
        ),
    )
    rows_by_implementation = {
        row.implementation: row for row in job.result()
    }
    for implementation in ("native", "python"):
        row = rows_by_implementation[implementation]
        print(
            f"{implementation} {country} {year}: "
            f"rows={row.rows_loaded} nulls={row.null_qty_rows} "
            f"kg={row.total_qty_kg}"
        )
        orchestra.set_output(
            f"{implementation}_rows_loaded", int(row.rows_loaded)
        )
        orchestra.set_output(
            f"{implementation}_null_qty_rows", int(row.null_qty_rows)
        )

        if row.rows_loaded == 0:
            raise SystemExit(
                f"No {implementation} rows loaded for {country} {year} - "
                "check the source CSV and load task."
            )


if __name__ == "__main__":
    main()