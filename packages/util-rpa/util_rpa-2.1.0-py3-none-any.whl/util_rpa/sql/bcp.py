"""BCP client for bulk copy operations with SQL Server."""
import subprocess
from pathlib import Path
import os
import logging

log = logging.getLogger(__name__)


class BCP:
    """BCP client for bulk copy operations with SQL Server."""

    def __init__(self, credentials: dict, encoding="-C 65001"):
        self.credentials = credentials
        self.encoding = encoding
        self.bin = "bcp" if os.name == "nt" else "/opt/mssql-tools/bin/bcp"

    def run(
        self,
        table: str,
        file: Path,
        operation: str,
        error_log: Path,
        validate_error=True
    ):
        """Run a BCP operation (IN/OUT) using bcp command."""
        if operation not in ("IN", "OUT"):
            raise ValueError("Operacion BCP no permitida")

        cmd = [
            self.bin,
            table,
            operation,
            str(file),
            "-e", str(error_log),
            "-S", self.credentials["hostname"],
            "-d", self.credentials["database"],
            "-U", self.credentials["username"],
            "-P", self.credentials["password"],
            "-c", self.encoding,
            '-t|',
            "-b1000",
            "-m1000",
        ]

        log.debug("BCP: %s", " ".join(cmd))

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        log.debug(proc.stdout)

        if validate_error and error_log.exists():
            if "error" in error_log.read_text(errors="ignore").lower():
                raise RuntimeError("Error detectado en BCP")
