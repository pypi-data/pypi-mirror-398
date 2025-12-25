import click
import shutil
import subprocess
import tempfile
from importlib import resources
from pathlib import Path

from cde_submit_migration.utils.logger import setup_logging


logger = setup_logging(name="MigrationSubmitLogger")


def make_zip(destination: Path, source: Path) -> None:
    archive_name = shutil.make_archive(destination, "zip", source)
    logger.info(f"Created '{archive_name}' in local file system.")

    return Path(archive_name)


def run_cde_spark_submit(
    path: Path, db: str, verbose: bool, profile: str | None = None
) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)

        # find migration.py script path
        runner_script_path = str(
            resources.files("cde_submit_migration").joinpath("migration.py")
        )

        if path.is_file():
            migration_file_path = path
        elif path.is_dir():
            migration_file_path = make_zip(tmp_dir_path / path.name, path)
        else:
            raise ValueError("Path does not exist, or is not a file or directory")

        cmd = [
            "cde",
            "spark",
            "submit",
            "--files",
            migration_file_path.name,
        ]

        if profile:
            cmd.extend(["--config-profile", profile])

        cmd.extend(
            [
                runner_script_path,
                "--",
                "--path",
                migration_file_path.name,
                "--db",
                db,
            ]
        )
        logger.info("Running 'cde spark submit' in a subprocess.")

        if verbose:
            click.echo("Command: \n" + " ".join(cmd))

            if not click.confirm(
                "Do you want to proceed with running this command?", default=False
            ):
                logger.info("Command execution cancelled by user.")
                return

        subprocess.run(cmd, cwd=tmp_dir_path, check=True)


@click.command(help="Submit SQL migration(s)")
@click.option(
    "--path",
    "path_",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to SQL migration file or folder containing multiple SQL migration files",
)
@click.option(
    "--db",
    required=True,
    help="Target database name where migration should take place",
)
@click.option(
    "--profile",
    default=None,
    help="CDE configuration profile name",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Shows 'cde spark submit' command and prompts for confirmation",
)
def main(path_: Path, db: str, profile: str | None, verbose: bool) -> None:
    run_cde_spark_submit(path=path_, db=db, verbose=verbose, profile=profile)


if __name__ == "__main__":
    main()
