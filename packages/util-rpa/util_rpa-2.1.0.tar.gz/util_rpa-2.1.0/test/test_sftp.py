"""Pruebas de integración SFTP para util-rpa.

Este archivo contiene TODAS las casuísticas comunes que el equipo
debe conocer al trabajar con SFTP en producción.

Uso:
- Ejecutar manualmente
- O convertir cada bloque en pytest test_*
"""

import logging
from pathlib import Path, PurePosixPath

from util_rpa.sftp.sftp_client import SFTPClient
from util_rpa.sftp.sftp_credentials import SFTPCredentials
from util_rpa.sftp.exceptions import (
    SFTPConnectionError,
    SFTPFileNotFound,
)
from util_rpa.logging_utils import init_logging
init_logging()
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# CONFIGURACIÓN BASE (NO TOCAR)
# ---------------------------------------------------------------------

creds = SFTPCredentials(
    hostname="localhost",
    username="jonathan",
    password="12345612345"
)

LOCAL_TMP = Path("/tmp")
REMOTE_HOME = PurePosixPath("/home/jonathan")

FILES_OK = [
    Path("/misapp/Personal/Descargas/firma_integratel.png"),
    Path("/misapp/Personal/Descargas/firma_integratel2.png"),
]


# ---------------------------------------------------------------------
# 1. CASO FELIZ - UPLOAD MÚLTIPLE
# ---------------------------------------------------------------------

def test_upload_ok():
    """Prueba de carga múltiple exitosa."""
    with SFTPClient(creds) as sftp:
        sftp.upload(
            files=FILES_OK,
            remote_dir=REMOTE_HOME
        )
        log.info("TEST 1 OK - Upload múltiple exitoso")


# ---------------------------------------------------------------------
# 2. ERROR - ARCHIVO LOCAL NO EXISTE
# ---------------------------------------------------------------------

def test_upload_file_not_found():
    """Prueba de carga de archivo que no existe."""
    try:
        with SFTPClient(creds) as sftp:
            sftp.upload(
                files=[Path("/ruta/que/no/existe.png")],
                remote_dir=REMOTE_HOME
            )
    except SFTPFileNotFound:
        log.info("TEST 2 OK - Archivo local inexistente detectado")


# ---------------------------------------------------------------------
# 3. ERROR - CREDENCIALES INCORRECTAS
# ---------------------------------------------------------------------

def test_bad_credentials():
    """Prueba de conexión con credenciales inválidas."""
    bad_creds = SFTPCredentials(
        hostname="localhost",
        username="jonathan",
        password="password_incorrecto"
    )

    try:
        with SFTPClient(bad_creds) as sftp:
            sftp.list(REMOTE_HOME)
    except SFTPConnectionError:
        log.info("TEST 3 OK - Error de autenticación controlado")


# ---------------------------------------------------------------------
# 4. DESCARGA POR PATRÓN (SIN BORRAR)
# ---------------------------------------------------------------------

def test_download_pattern():
    """Prueba de descarga de archivos por patrón sin borrado remoto."""
    with SFTPClient(creds) as sftp:
        sftp.download_pattern(
            remote_pattern=REMOTE_HOME / "firma_*.png",
            local_dir=LOCAL_TMP,
            remove=False
        )
        log.info("TEST 4 OK - Descarga por patrón sin borrado")


# ---------------------------------------------------------------------
# 5. DESCARGA POR PATRÓN + BORRADO REMOTO
# ---------------------------------------------------------------------

def test_download_and_remove():
    """Prueba de descarga de archivos por patrón con borrado remoto."""
    with SFTPClient(creds) as sftp:
        sftp.download_pattern(
            remote_pattern=REMOTE_HOME / "firma_*.png",
            local_dir=LOCAL_TMP,
            remove=True
        )
        log.info("TEST 5 OK - Descarga con borrado remoto")


# ---------------------------------------------------------------------
# 6. DESCARGA SIN COINCIDENCIAS
# ---------------------------------------------------------------------

def test_download_no_matches():
    """Prueba de descarga de archivos por patrón sin coincidencias."""
    try:
        with SFTPClient(creds) as sftp:
            sftp.download_pattern(
                remote_pattern=REMOTE_HOME / "no_existe_*.csv",
                local_dir=LOCAL_TMP
            )
    except SFTPFileNotFound:
        log.info("TEST 6 OK - Patrón sin coincidencias controlado")


# ---------------------------------------------------------------------
# 7. MKDIR NO RECURSIVO
# ---------------------------------------------------------------------

def test_mkdir_simple():
    """Prueba de creación de directorio simple (no recursivo)."""
    with SFTPClient(creds) as sftp:
        sftp.mkdir(
            path=REMOTE_HOME / "test_dir_simple",
            recursive=False
        )
        log.info("TEST 7 OK - Directorio simple creado")


# ---------------------------------------------------------------------
# 8. MKDIR RECURSIVO
# ---------------------------------------------------------------------

def test_mkdir_recursive():
    """Prueba de creación de directorio recursivo."""
    with SFTPClient(creds) as sftp:
        sftp.mkdir(
            path=REMOTE_HOME / "a/b/c/d",
            recursive=True
        )
        log.info("TEST 8 OK - Directorio recursivo creado")


# ---------------------------------------------------------------------
# 9. LISTADO SIMPLE Y CON ATRIBUTOS
# ---------------------------------------------------------------------

def test_list_directory():
    """Prueba de listado de directorio simple y con atributos."""
    with SFTPClient(creds) as sftp:
        files = sftp.list(REMOTE_HOME)
        files_attr = sftp.list(REMOTE_HOME, attr=True)

        log.info(f"TEST 9 OK - list(): {len(files)} elementos")
        log.info(f"TEST 9 OK - list(attr=True): {len(files_attr)} elementos")


# ---------------------------------------------------------------------
# 10. MOVE / RENAME
# ---------------------------------------------------------------------

def test_move_files():
    """Prueba de movimiento / renombrado de archivos."""
    with SFTPClient(creds) as sftp:
        sftp.upload(
            files=FILES_OK,
            remote_dir=REMOTE_HOME
        )
        sftp.move_many([
            (REMOTE_HOME / "firma_integratel.png", REMOTE_HOME / "firma_integratel3.png"),
            (REMOTE_HOME / "firma_integratel2.png", REMOTE_HOME / "firma_integratel4.png")
        ], True)
        log.info("TEST 10 OK - Move Many / rename ejecutado")

        sftp.move(REMOTE_HOME / "firma_integratel4.png", REMOTE_HOME / "firma_integratel5.png")
        log.info("TEST 11 OK - Move / rename ejecutado")
