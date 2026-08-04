from pathlib import Path
import subprocess
import sys

from prefect import flow, task

ROOT = Path(__file__).resolve().parent.parent


@task(retries=1, retry_delay_seconds=10)
def run_extract() -> None:
    subprocess.run([sys.executable, str(ROOT / "flows" / "extract.py")], cwd=ROOT, check=True)


@task(retries=1, retry_delay_seconds=10)
def run_dbt() -> None:
    subprocess.run([str(ROOT / ".venv" / "Scripts" / "dbt.exe"), "run", "--profiles-dir", str(ROOT), "--project-dir", str(ROOT)], cwd=ROOT, check=True)


@task(retries=1, retry_delay_seconds=10)
def run_tests() -> None:
    subprocess.run([str(ROOT / ".venv" / "Scripts" / "dbt.exe"), "test", "--profiles-dir", str(ROOT), "--project-dir", str(ROOT)], cwd=ROOT, check=True)


@flow(name="franq-dbt-pipeline")
def franq_pipeline() -> None:
    run_extract()
    run_dbt()
    run_tests()


if __name__ == "__main__":
    franq_pipeline()
