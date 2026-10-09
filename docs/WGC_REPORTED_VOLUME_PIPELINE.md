# WGC Reported-Volume Pipeline Handoff

## Purpose

Load a country/year slice from
`gs://orchestra-gcp-poc/reported_volumes_inputs.csv` into BigQuery twice:
once using a native BigQuery task and once using a Python task. Store the
results separately, then check that they agree.

## Pipeline flow

```text
GCS CSV
  |
  v
Check that the source object exists
  |
  v
Prepare source and destinations
  |-- Create/replace BigQuery external table over the CSV
  |-- Ensure reported_volumes_raw exists
  `-- Ensure reported_volumes_raw_py exists
  |
  v
Load both implementations in parallel
  |-- Native BigQuery MERGE --> reported_volumes_raw
  `-- Python BigQuery MERGE --> reported_volumes_raw_py
  |
  v
Quality checks
  |-- Python QA summary reports row/null/quantity totals for both tables
  |-- Fail if either table has rows with a null qty_kg
  `-- Fail if the selected country/year rows differ between tables
```

The executable pipeline definition is
[`../orchestra/wgc-reported-volume-poc.yaml`](../orchestra/wgc-reported-volume-poc.yaml).

## Source and output

- **Source:** `gs://orchestra-gcp-poc/reported_volumes_inputs.csv`
- **External table:** `wgc_reported_volumes_poc.ext_reported_volumes_inputs`
- **Native output:** `wgc_reported_volumes_poc.reported_volumes_raw`
- **Python output:** `wgc_reported_volumes_poc.reported_volumes_raw_py`
- **Default inputs:** `country = Ghana`, `year = 2024`

The CSV must contain a header row followed by these columns in order:
`source`, `link`, `mine_size`, `supply_chain`, `declaration`, `year`, `kg`,
`notes`, `country`, `weight`.

Each load replaces only the matching `source_country` / `source_year` slice:
it deletes that slice from its own destination table, then inserts the current
source rows. This makes a retry for the same inputs repeatable without
appending duplicates.

## Current status

- The Orchestra CLI schema validation passed for the pipeline YAML.
- The user reported that importing the Git-backed pipeline succeeded using
  alias `wgc_reported_volume`.
- The returned pipeline ID was not recorded in this repository/document.
- The user confirmed that the pipeline run succeeded. Run ID, input values,
  loaded row counts, and task-level parity results were not provided.

## Next steps

1. Optionally record the successful run ID, input values, and loaded row counts
   for future operational reference.
2. Keep an eye on subsequent runs and inspect task logs if a later run fails.

## Connections referenced by the YAML

| Connection ID | Type | Purpose |
| --- | --- | --- |
| `orchestra_gcp_59732` | GCP Cloud Storage | Check that the CSV object exists |
| `orchestra_gcp_52611` | GCP BigQuery | Create tables, run native load, and run quality checks |
| `python_wgc_70839` | Python | Run the Python implementation and post-load summary |

The BigQuery identity must be able to read the source object and create/query
tables in the target dataset. The Python tasks must have the packages in
[`../python/requirements.txt`](../python/requirements.txt) available.
They also need Orchestra SDK access to read the linked BigQuery connection and
submit BigQuery jobs. Keep API keys and service-account credentials in
Orchestra connections or secrets, never in the YAML or Git.

## GitHub Actions run

The manually triggered workflow is
[`../.github/workflows/run-pipeline.yml`](../.github/workflows/run-pipeline.yml).
Configure repository secret `ORCHESTRA_API_KEY` and repository variable
`ORCHESTRA_PIPELINE_ID` with the UUID returned by the one-time import. Start it
from the GitHub Actions page and enter the desired country/year. It is not
triggered by pushes, to avoid unintentional data loads.

## CLI reference

Run these from the repository root. Import is a one-time registration step;
do not repeat it to update the existing Git-backed pipeline.

```sh
orchestra pipeline validate ./orchestra/wgc-reported-volume-poc.yaml
orchestra pipeline list
orchestra pipeline run --alias wgc_reported_volume
```
