---
name: validate-pipeline
description: Validate the WGC Orchestra pipeline YAML and compile the Python task code. Use before committing or opening a PR that touches orchestra/ or python/, or when the user asks to check, lint or validate the pipeline.
---

# Validate the pipeline

Run from the repository root.

1. Validate the pipeline against the Orchestra API:

   ```sh
   orchestra pipeline validate ./orchestra/wgc-reported-volume-poc.yaml
   ```

   If the CLI says you aren't logged in, ask the user to run `orchestra login`
   (it opens a browser), then retry.

2. Compile the standalone Python code:

   ```sh
   python -m compileall -q python/wgc_poc
   ```

3. Check the inline Python in the `load_python` task. Extract the `code:` block
   and compile it, for example:

   ```sh
   python - <<'PY'
   import yaml
   doc = yaml.safe_load(open("orchestra/wgc-reported-volume-poc.yaml"))
   code = doc["pipeline"]["load_group"]["tasks"]["load_python"]["parameters"]["code"]
   compile(code, "load_python", "exec")
   print("load_python compiles")
   PY
   ```

4. Check consistency rules the API doesn't catch:
   - Every `connection:` is one of `orchestra_gcp_59732` (GCS),
     `orchestra_gcp_52611` (BigQuery) or `python_wgc_70839` (Python), unless the
     user has said a new one exists.
   - Each `depends_on` names an existing task group.
   - Both destination table DDLs in `prepare_group` have the same columns.

Report each step as passed or failed, quoting the error output for failures.
Don't edit files to make validation pass unless the user asks.
