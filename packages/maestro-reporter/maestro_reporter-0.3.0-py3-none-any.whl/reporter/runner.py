import subprocess
import shlex
from .logger import get_logger
from pathlib import Path


log = get_logger(__name__)


def run_maestro_command(
    command: str, cwd: str = None, timeout: int = 1800
) -> Path | None:
    """
    Runs a Maestro command and returns the path to the `report.xml` file if it exists.
    Usually, Maestro will create this file in the current working directory.

    :param command: Maestro command to run/perform the test
    :param cwd: current working directory to run the command
    """
    try:
        log.info(f"Running Maestro command: {command}")
        args = shlex.split(command)
        result = subprocess.run(
            args, stdout=subprocess.PIPE, text=True, timeout=timeout, cwd=cwd
        )

        if result.returncode != 0:
            log.error(f"Maestro command failed with return code: {result.returncode}")
            log.error(f"Maestro command output: {result.stdout}")
            return None

        # check whether `cwd` contains the report.xml file
        # if not, check in the current working directory
        base_directory = Path(cwd) if cwd else Path.cwd()
        file_path_locations = [base_directory / "report.xml"]
        for path in file_path_locations:
            if path.exists():
                log.info(f"Found Maestro report at: {path}")
                return path.resolve()

        log.error(f"No Maestro report found")
    except subprocess.TimeoutExpired:
        log.error("Maestro command timed out after 1800 seconds")
        return None
    except Exception as e:
        log.error(f"Uncaught exception while running Maestro command: {e}")
        return None
