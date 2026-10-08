---
name: change-load-logic
description: Change how the WGC pipeline transforms or stores reported volumes, keeping the native BigQuery and Python loads identical. Use when the user wants to add, rename or recast a column, change filtering, or edit either MERGE in orchestra/wgc-reported-volume-poc.yaml.
---

# Change the load logic

The pipeline loads the same data twice and the `dq_native_vs_python` check
fails if the results differ. Any change to one load path must be made to the
other in the same edit.

## Where the logic lives

All in `orchestra/wgc-reported-volume-poc.yaml`:

| Concern | Native BigQuery | Python |
| --- | --- | --- |
| Source columns | `prepare_group.create_external_table` (shared) | same |
| Destination schema | `prepare_group.ensure_native_table` | `prepare_group.ensure_python_table` |
| Transform and MERGE | `load_group.load_native` (uses `${{ inputs.* }}`) | `load_group.load_python` `code:` block (uses `@country`, `@year`, etc. query parameters) |
| Parity check | `checks_group.dq_native_vs_python` | same |

## Steps

1. Make the change in the native SQL first, then mirror it exactly in the
   Python MERGE. Keep the expressions the same; only the parameter syntax
   differs (`'${{ inputs.country }}'` versus `@country`).
2. If the destination schema changes, update both `ensure_*_table` DDLs.
   `CREATE TABLE IF NOT EXISTS` won't alter existing tables, so tell the user
   they need an `ALTER TABLE` (or to drop and recreate the tables) and offer to
   write it. Don't run destructive DDL yourself.
3. If you add a business column, add it to both CTEs in `dq_native_vs_python`
   so the parity check covers it.
4. Keep the Python query parameterised. Never format inputs into the SQL
   string.
5. Update the README if the inputs, tables or columns change.
6. Run the `validate-pipeline` skill.
