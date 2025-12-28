"""Utilidades de logging para RPA."""
import datetime
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
from functools import wraps

FMT = "%(asctime)-5s [%(levelname)s] %(name)s %(filename)s:%(lineno)d - %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"


def init_logging():
    """Logging centralizado.

    VARIABLES DE ENTORNO SOPORTADAS:
        LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
        LOG_OUTPUT=CONSOLE|CONSOLE_FILE
    """
    root = logging.getLogger()

    # Nivel de log
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    print(f"[LOG INIT] level={level_name}")
    level = getattr(logging, level_name, logging.INFO)
    root.setLevel(level)

    # Evitar handlers duplicados
    if root.handlers:
        return root

    formatter = logging.Formatter(FMT, DATE_FMT)

    # Consola siempre
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Archivo si LOG_OUTPUT = CONSOLE_FILE
    if os.getenv("LOG_OUTPUT", "CONSOLE").upper() == "CONSOLE_FILE":
        logs_dir = Path("./logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Sufijo horario → YYYYMMDDHH
        suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = logs_dir / f"app_{suffix}.log"

        fh = RotatingFileHandler(
            str(file_path),
            maxBytes=10_000_000,
            backupCount=5
        )
        fh.setFormatter(formatter)
        root.addHandler(fh)

    root.info(f"[LOG INIT] level={level_name}")
    return root


def timed(func):
    """Decorador para loggear el tiempo de ejecución de una función.

    - Usa el logger del módulo que ejecuta la función
    - No captura excepciones
    - No altera el resultado
    """
    logger = logging.getLogger(func.__module__)
    func_name = func.__qualname__

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(
            "############### Inicio: %s ###############",
            func_name,
        )

        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start

        logger.info(
            "## Tiempo transcurrido (%s): %.2f s",
            func_name,
            duration,
        )
        logger.info(
            "############### Fin: %s ###############",
            func_name,
        )

        return result

    return wrapper
