import subprocess
import sys
from pathlib import Path

from prefect import flow, task

ROOT = Path(__file__).resolve().parent.parent

# dbt is installed next to the running interpreter (.venv/bin or .venv\Scripts).
DBT_BIN = str(Path(sys.executable).parent / ("dbt.exe" if sys.platform == "win32" else "dbt"))


@task(retries=1, retry_delay_seconds=10)
def run_extract() -> None:
    subprocess.run([sys.executable, str(ROOT / "flows" / "extract.py")], cwd=ROOT, check=True)


@task(retries=1, retry_delay_seconds=10)
def run_dbt() -> None:
    subprocess.run(
        [DBT_BIN, "run", "--profiles-dir", str(ROOT), "--project-dir", str(ROOT)],
        cwd=ROOT,
        check=True,
    )


@task(retries=1, retry_delay_seconds=10)
def run_tests() -> None:
    subprocess.run(
        [DBT_BIN, "test", "--profiles-dir", str(ROOT), "--project-dir", str(ROOT)],
        cwd=ROOT,
        check=True,
    )


@flow(name="cnpj-dbt-pipeline")
def cnpj_pipeline() -> None:
    run_extract()
    run_dbt()
    run_tests()


if __name__ == "__main__":
    cnpj_pipeline()
