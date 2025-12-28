"""SQLCMD client for executing SQL scripts against SQL Server."""
import subprocess
import shutil
from pathlib import Path
import os
import logging

log = logging.getLogger(__name__)


class SQLCmd:
    """SQLCMD client for executing SQL scripts against SQL Server."""

    def __init__(self, credentials: dict, encoding="65001"):
        self.credentials = credentials
        self.encoding = encoding
        self.bin = "sqlcmd" if os.name == "nt" else "/opt/mssql-tools/bin/sqlcmd"

    def run(
        self,
        sql_file: Path,
        output_log: Path,
        variables: dict | None = None,
        validate_error: bool = True
    ):
        """Run a SQL script using sqlcmd."""
        if not sql_file.exists():
            raise FileNotFoundError(sql_file)

        tmp = sql_file.with_suffix(".tmp.sql")

        if variables:
            self._replace_vars(sql_file, tmp, variables)
        else:
            shutil.copy(sql_file, tmp)

        cmd = [
            self.bin,
            "-e", "-y", "0",
            "-i", str(tmp),
            "-o", str(output_log),
            "-S", self.credentials["hostname"],
            "-d", self.credentials["database"],
            "-U", self.credentials["username"],
            "-P", self.credentials["password"],
            "-f", self.encoding,
        ]

        log.debug("SQLCMD: %s", " ".join(cmd))

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        log.debug(proc.stdout)

        tmp.unlink(missing_ok=True)

        if validate_error and output_log.exists():
            if "error" in output_log.read_text(errors="ignore").lower():
                raise RuntimeError("Error detectado en SQLCMD")

    def _replace_vars(self, src: Path, dst: Path, variables: dict):
        content = src.read_text()
        for k, v in variables.items():
            content = content.replace(k, v)
        dst.write_text(content)
