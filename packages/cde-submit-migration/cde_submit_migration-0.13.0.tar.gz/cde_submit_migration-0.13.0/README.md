# cde-submit-migration

Lightweight Spark-based migration runner for executing SQL migrations on Spark catalog tables in Cloudera Data Engineering (CDE).

This repository contains a small CLI and a Spark job that can apply SQL migration files (single .sql file or a zipped folder containing multiple .sql files) to a Spark catalog. It was created to make it easy to run migrations either locally (for testing) or by submitting the job through CDE's `cde spark submit` command.

## Highlights
- Run a single SQL migration file or a folder (zipped automatically) containing multiple ordered `.sql` files.
- Local mode (uses a local path-based Iceberg catalog) for development and testing.
- Integration with Cloudera Data Engineering (`cde spark submit`) for production runs.

## Requirements
- Python 3.11 or later
- `pyspark==3.5.1`


## Install
```bash
uv tool install cde-submit-migration
```

```bash
pip install cde-submit-migration
```

After installation you should have following console command available:
    - `submit-cde-migration` to perform migration on CDE environment,
    - `submit-local-migration` to perform migration in local environment (for testing purposes)

To upgrade package to the latest version use following commands:
```bash
uv tool upgrade cde-submit-migration 
```

```bash
pip install --upgrade cde-submit-migration
```

## Usage
```bash
submit-cde-migration --path path/to/migrations --db target_database --profile my-cde-profile
```

```bash
submit-local-migration --path path/to/migrations --db target_database
```

Notes on arguments:
- `--path` — path to a single `.sql` file or a folder containing `.sql` files. When passing a folder in non-local mode, the folder is copied and zipped before submission.
- `--db` — target database name to use as the current catalog database. If the database does not exist, it will be created.
- `--profile` — optional CDE configuration profile name used when calling `cde spark submit`.


## Project structure
- `src/cde_submit_migration/main.py` — CLI entrypoint that either runs locally or packages and submits to CDE.
- `src/cde_submit_migration/migration.py` — Spark job that executes SQL migration(s).
- `pyproject.toml` — project metadata and dependencies.


## Troubleshooting
- If `cde spark submit` is not in your PATH, the CDE mode will fail. Make sure the `cde` CLI is installed and configured in the environment you use to run `submit-cde-migration`.
- If you see Spark/Java version incompatibilities when running locally, verify your local Spark/PySpark installation matches the expected runtime (the project pins `pyspark==3.5.1`).
