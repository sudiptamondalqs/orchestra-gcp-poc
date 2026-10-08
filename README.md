# orchestra-gcp-poc

A proof of concept that uses [Orchestra](https://www.getorchestra.io/) to load
the WGC reported-volumes CSV from Cloud Storage into BigQuery. The load runs
twice: once as native BigQuery SQL and once as a Python task. The pipeline
then checks that both produce the same rows.

See the [pipeline handoff](./docs/WGC_REPORTED_VOLUME_PIPELINE.md) for the flow,
current status, and next steps.

## Repository layout

| Path | Purpose |
| --- | --- |
| [`orchestra/wgc-reported-volume-poc.yaml`](./orchestra/wgc-reported-volume-poc.yaml) | Orchestra pipeline definition |
| [`python/wgc_poc/qa_summary.py`](./python/wgc_poc/qa_summary.py) | Post-load summary for native and Python results |
| [`python/requirements.txt`](./python/requirements.txt) | Dependencies for the Python load and QA tasks |
| [`.github/workflows/validate-pipeline.yml`](./.github/workflows/validate-pipeline.yml) | GitHub Actions job that validates the pipeline on PRs |
| [`.github/workflows/run-pipeline.yml`](./.github/workflows/run-pipeline.yml) | Manually triggered GitHub Actions workflow for running the pipeline |
| [`.claude/skills/`](./.claude/skills/) | Claude Code skills for working on this repo (see below) |

## What the pipeline does

The source file is `gs://orchestra-gcp-poc/reported_volumes_inputs.csv`. It
must have a header row and these columns, in order: `source`, `link`,
`mine_size`, `supply_chain`, `declaration`, `year`, `kg`, `notes`, `country`,
`weight`.

| Stage | Task group | What happens |
| --- | --- | --- |
| 1 | `check_file_group` | Confirms the CSV exists in GCS |
| 2 | `prepare_group` | Creates the external table `ext_reported_volumes_inputs` and makes sure both destination tables exist |
| 3 | `load_group` | Loads the selected country/year into both tables in parallel |
| 4 | `checks_group` | Fails if either table has a null `qty_kg`, or if the two tables differ |

All tables live in the `wgc_reported_volumes_poc` dataset:

- `reported_volumes_raw`: loaded by native BigQuery SQL
- `reported_volumes_raw_py`: loaded by the Python task

Each load is a `MERGE` scoped to one `source_country` and `source_year`. It
deletes that slice and reinserts it, so rerunning for the same inputs is safe.
`kg` and `weight` have their thousands separators removed and are cast to
`NUMERIC`. Each row records its `source_uri`, `loaded_at` and
`pipeline_run_id`.

### Inputs

| Input | Default | Meaning |
| --- | --- | --- |
| `country` | `Ghana` | Country to load (case-insensitive match against the CSV) |
| `year` | `2024` | Year to load |
| `notify_email` | pipeline owner | Address for failure, warning, success and slow-run emails |

### Orchestra connections

| Connection ID | Type | Used by |
| --- | --- | --- |
| `orchestra_gcp_59732` | GCP Cloud Storage | File check |
| `orchestra_gcp_52611` | GCP BigQuery | DDL, native load and checks |
| `python_wgc_70839` | Python | Python load |

The BigQuery service account needs to read the CSV from Cloud Storage and to
create and query tables in the dataset. The Python connection needs Orchestra
SDK access so it can read the linked BigQuery connection's credentials.

## Working with the pipeline

Install and log in to the Orchestra CLI:

```sh
pip install orchestra-cli
orchestra login
```

### First-time setup: validate, push, then import

**Import is the final one-time setup step before the first run.** Do these
steps in order:

1. Confirm the GCS, BigQuery, and Python connections exist in Orchestra.
2. Validate the pipeline locally:

```sh
orchestra pipeline validate ./orchestra/wgc-reported-volume-poc.yaml
```

3. Commit and push the validated YAML to the GitHub repository connected to
   your Orchestra workspace.
4. Import it into Orchestra once:

```sh
orchestra pipeline import \
  --alias wgc_reported_volume \
  --path ./orchestra/wgc-reported-volume-poc.yaml
```

The import registers the Git-backed pipeline and returns its ID. This is the
last setup step before running the pipeline; it does not execute any tasks.
Do not repeat the import to publish changes, because each import creates
another pipeline.

### Run after import

```sh
orchestra pipeline run --alias wgc_reported_volume
```

The command waits for the run to finish by default. To read one task's logs,
use `orchestra task logs --task-run-id <id>`.
To choose non-default input values, start the run in Orchestra and enter the
desired `country` and `year`.

For future changes, edit the YAML and push it to the tracked Git branch; do
not import the pipeline again.

### Run from GitHub Actions

The manual workflow at
[`.github/workflows/run-pipeline.yml`](./.github/workflows/run-pipeline.yml)
can trigger and monitor a run. In the GitHub repository settings, add:

- Repository secret `ORCHESTRA_API_KEY`: an Orchestra API key.
- Repository variable `ORCHESTRA_PIPELINE_ID`: the UUID printed when the
  pipeline was imported.

Then open **Actions → Run WGC reported-volume pipeline → Run workflow** and
enter the country and year. The workflow is manual-only so a code push cannot
accidentally start a data load.

## Claude Code skills

This repo includes project skills in [`.claude/skills/`](./.claude/skills/).
Claude Code picks them up automatically when you open the repo, and you can
also call them by name:

| Skill | Use it to |
| --- | --- |
| `/validate-pipeline` | Validate the YAML and compile the Python code before a commit or PR |
| `/run-pipeline` | Run the pipeline for a country and year, then summarise the result and any failing task's logs |
| `/change-load-logic` | Change the load or table schema while keeping the native and Python paths identical |
