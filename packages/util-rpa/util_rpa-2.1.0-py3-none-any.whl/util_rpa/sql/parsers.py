"""Parsers para logs SQL (sqlcmd / bcp)."""
import re
from pathlib import Path
import logging

log = logging.getLogger(__name__)


def extract_prefixed_lines(
    sql_log: Path,
    output_file: Path,
    *,
    prefix: str = "DATA:",
    start_marker: str | None = "INI_DATA_SQLSERVER",
    encoding: str = "utf-8",
):
    """Extrae líneas de un log SQL (sqlcmd / bcp) que comiencen con un prefijo y las escribe en un archivo.

    Args:
        sql_log (Path): Archivo log de entrada.
        output_file (Path): Archivo de salida.
        prefix (str): Prefijo de las líneas a capturar (ej. 'DATA:').
        start_marker (str | None): Marca opcional desde donde empezar a leer.
        encoding (str): Encoding de lectura.
    """
    sql_log = Path(sql_log)
    output_file = Path(output_file)

    if not sql_log.exists():
        raise FileNotFoundError(sql_log)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    log.debug("Parseando log SQL: %s", sql_log)

    found_start = start_marker is None

    with sql_log.open("r", encoding=encoding, errors="ignore") as fin, \
            output_file.open("w", encoding="utf-8") as fout:

        for line in fin:
            if not found_start and start_marker and re.search(start_marker, line):
                log.debug("Start marker encontrado: %s", start_marker)
                found_start = True
                continue

            if found_start and line.startswith(prefix):
                fout.write(line[len(prefix):])

    log.debug("Resultado generado: %s", output_file)
