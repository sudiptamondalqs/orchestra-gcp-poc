---
name: run-pipeline
description: Run the WGC reported-volume Orchestra pipeline for a country and year and report the result. Use when the user asks to run, trigger, rerun or test the pipeline, or to load a specific country/year into BigQuery.
---

# Run the pipeline

The pipeline is imported in Orchestra with alias `wgc-reported-volume`. It
takes `country` (default `Ghana`) and `year` (default `2024`) inputs.

1. Confirm the country and year with the user if they didn't give them. A run
   replaces that country/year slice in both BigQuery tables, so state that
   before running.

2. Make sure the YAML is valid first (use the `validate-pipeline` skill) if it
   changed in this session. The imported pipeline runs the YAML from git, so
   uncommitted or unpushed changes won't be in the run. Say so if the working
   tree has changes under `orchestra/`.

3. Run it:

   ```sh
   orchestra pipeline run --alias wgc-reported-volume \
     --input country=<Country> --input year=<Year>
   ```

   The command waits until the run finishes. To rerun one task group, add
   `--task <group or task name>`, plus `--continue` to also run downstream
   tasks.

   If the alias isn't found, run `orchestra pipeline list` and ask the user
   which pipeline to use. Don't run `orchestra pipeline import` without asking,
   because each import creates a new pipeline.

4. For any failed or warning task, fetch its logs:

   ```sh
   orchestra task logs --task-run-id <id> --no-watch
   ```

5. Report the run status, each task group's outcome and, for failures, the
   likely cause. Common causes:
   - `check_file_present` failed: the CSV is missing from
     `gs://orchestra-gcp-poc/reported_volumes_inputs.csv`.
   - `dq_no_null_qty` failed: some `kg` values didn't cast to NUMERIC.
   - `dq_native_vs_python` failed: the native and Python MERGE statements have
     drifted apart (see the `change-load-logic` skill).
   - `load_python` failed on credentials: the Python connection can't read the
     linked BigQuery connection.
