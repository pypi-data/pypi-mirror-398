import argparse
import sys
import zipfile
from pathlib import Path
from pyspark.sql import SparkSession

from cde_submit_migration.utils.logger import setup_logging


JOB_NAME = "Migration"

logger = setup_logging(name=f"{JOB_NAME}Logger")


def get_spark_session(env: str | None = None) -> SparkSession:
    if env == "local":
        spark = (
            SparkSession.builder.master("local[1]")
            .appName(JOB_NAME)
            .config(
                "spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1",
            )
            .config(
                "spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            )
            .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
            .config("spark.sql.catalog.local.type", "hadoop")
            .config("spark.sql.catalog.local.warehouse", "./spark-warehouse")
            .config("spark.sql.defaultCatalog", "local")
            .getOrCreate()
        )
        logger.info(
            f"Run in local environment. Deafult catalog switched to path-based catalog: {spark.catalog.currentCatalog()}"
        )
    else:
        spark = SparkSession.builder.appName(JOB_NAME).getOrCreate()

    return spark


def unpack_zip_archive(path: Path) -> None:
    # Convert to clean string
    extract_dir = path.with_suffix("")

    if not path.exists():
        raise FileNotFoundError("Zip archive not found in working dir.")

    logger.info(f"Extracting {str(path)} → {str(extract_dir)}")
    with zipfile.ZipFile(path, "r") as z:
        z.extractall(extract_dir)

    if extract_dir.exists():
        logger.info("Zip archive successfully extracted!")

    return extract_dir


def execute_statements(script_path: Path, spark: SparkSession) -> None:
    script_name = script_path.name

    logger.info(f"Applying migration: {script_name}")

    with script_path.open() as f:
        lines = f.readlines()

    # Remove full-line comments
    cleaned_lines = [line for line in lines if not line.strip().startswith("--")]
    cleaned_sql = "".join(cleaned_lines)

    statements = [stmt.strip() for stmt in cleaned_sql.split(";") if stmt.strip()]

    for stmt in statements:
        try:
            spark.sql(stmt)
        except Exception as e:
            logger.error(
                f"Error while executing SQL statement from {script_name}: \n'''{stmt}'''"
            )
            raise e

    logger.info(f"Successfully applied migration: {script_name}")


def run_migration(path: Path, spark: SparkSession) -> None:
    # If it's a single SQL file, run it
    if path.is_file() and path.suffix == ".sql":
        execute_statements(path, spark)

    elif path.is_dir():
        # Sorted list of files and dirs within the current path
        path_list = sorted(path.rglob("*.sql"))

        for p in path_list:
            execute_statements(p, spark)

    else:
        raise ValueError("Invalid path. Accepted paths: .sql file or directory")


def main():
    parser = argparse.ArgumentParser(description="Run SQL migration(s)")
    parser.add_argument(
        "--path", type=Path, required=True, help="Path to SQL file or folder"
    )
    parser.add_argument("--db", type=str, required=True, help="Target database name")

    args = parser.parse_args()
    path = args.path
    db = args.db

    if sys.argv[0].endswith("submit-local-migration"):
        spark = get_spark_session(env="local")
    else:
        spark = get_spark_session()

    if not spark.catalog.databaseExists(db):
        spark.sql(f"CREATE DATABASE {db}")
    spark.catalog.setCurrentDatabase(db)

    if zipfile.is_zipfile(path):
        path = unpack_zip_archive(path)

    run_migration(path, spark)


if __name__ == "__main__":
    main()
