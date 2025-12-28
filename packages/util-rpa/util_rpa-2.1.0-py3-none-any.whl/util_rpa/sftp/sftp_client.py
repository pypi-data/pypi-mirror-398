"""Cliente SFTP basado en Paramiko."""
import logging
from pathlib import Path, PurePosixPath
from typing import Iterable, Tuple
import fnmatch
import paramiko

from util_rpa.sftp.sftp_credentials import SFTPCredentials
from util_rpa.sftp.exceptions import (
    SFTPConnectionError,
    SFTPFileNotFound
)

log = logging.getLogger(__name__)


class SFTPClient:
    """Cliente SFTP para operaciones de archivo remoto."""

    def __init__(self, creds: SFTPCredentials):
        self.creds = creds
        self._transport = None
        self._client = None

    def __enter__(self):
        """Establece la conexión SFTP."""
        log.info(
            f"Conectando a SFTP {self.creds.hostname}:{self.creds.port} "
            f"como usuario {self.creds.username}"
        )

        try:
            self._transport = paramiko.Transport(
                (self.creds.hostname, self.creds.port)
            )
            self._transport.default_window_size = (
                paramiko.common.MAX_WINDOW_SIZE // 2
            )
            self._transport.connect(
                username=self.creds.username,
                password=self.creds.password,
            )

            self._client = paramiko.SFTPClient.from_transport(self._transport)
            self._client.get_channel().settimeout(self.creds.timeout)

            log.info("Conexión SFTP establecida correctamente")
            return self

        except Exception as e:
            log.error("Error al establecer conexión SFTP", exc_info=True)
            raise SFTPConnectionError(str(e))

    def __exit__(self, exc_type, exc, tb):
        """Cierra la conexión SFTP."""
        log.info("Cerrando conexión SFTP")

        if self._client:
            self._client.close()
        if self._transport:
            self._transport.close()

        log.info("Conexión SFTP cerrada")

    def upload(self, files: Iterable[Path], remote_dir: PurePosixPath):
        """Sube archivos a un directorio remoto."""
        log.info(f"Inicio carga de archivos a {remote_dir}")
        self._client.chdir(remote_dir.as_posix())

        for file in files:
            if not file.exists():
                log.error(f"Archivo local no existe: {file}")
                raise SFTPFileNotFound(file)

            dest = (remote_dir / file.name).as_posix()
            log.debug(f"Subiendo {file} → {dest}")
            self._client.put(str(file), dest)

        log.info("Carga de archivos finalizada")

    def download_pattern(
        self,
        remote_pattern: PurePosixPath,
        local_dir: Path,
        remove: bool = False,
    ):
        """Descarga archivos que coinciden con un patrón remoto."""
        log.info(
            f"Buscando archivos en {remote_pattern.parent} "
            f"con patrón {remote_pattern.name}"
        )

        self._client.chdir(remote_pattern.parent.as_posix())
        files = self._client.listdir()

        matches = [
            f for f in files
            if fnmatch.fnmatch(f, remote_pattern.name)
        ]

        if not matches:
            log.warning(f"No se encontraron archivos para {remote_pattern}")
            raise SFTPFileNotFound(remote_pattern)

        for f in matches:
            dest = local_dir / f
            log.debug(f"Descargando {f} → {dest}")
            self._client.get(f, str(dest))

            if remove:
                log.debug(f"Eliminando archivo remoto {f}")
                self._client.remove(f)

        log.info(
            f"Descarga completada: {len(matches)} archivo(s)"
        )

    def mkdir(self, path: PurePosixPath, recursive: bool = False, mode=755):
        """Crea un directorio remoto."""
        if not recursive:
            log.info(f"Creando directorio remoto {path}")
            self._client.mkdir(path.as_posix(), mode)
            return

        log.info(f"Creación recursiva de directorio {path}")
        current = PurePosixPath("/")

        for part in path.parts[1:]:
            current /= part
            try:
                self._client.stat(current.as_posix())
                log.debug(f"Directorio ya existe: {current}")
            except IOError:
                log.info(f"Creando directorio {current}")
                self._client.mkdir(current.as_posix(), mode)

    def list(self, path: PurePosixPath, attr=False):
        """Lista archivos en un directorio remoto."""
        log.info(f"Listando contenido de {path}")
        self._client.chdir(path.as_posix())

        result = (
            self._client.listdir_attr()
            if attr
            else self._client.listdir()
        )

        log.info(f"Elementos encontrados: {len(result)}")
        return result

    def move(self, src: PurePosixPath, dst: PurePosixPath):
        """Mueve archivos en el servidor SFTP."""
        log.info(f"Moviendo archivo {src} a {dst} en SFTP")

        self._client.rename(src.as_posix(), dst.as_posix())
        log.info("Movimiento de archivo completado")

    def move_many(
        self,
        moves: Iterable[Tuple[PurePosixPath, PurePosixPath]],
        continue_on_error: bool = False,
    ):
        """Mueve múltiples archivos en el servidor SFTP.

        Args:
            moves: iterable de (origen, destino)
            continue_on_error: si True, continúa ante error
        """
        log.info(f"Moviendo {len(list(moves))} archivo(s) en SFTP")

        for src, dst in moves:
            try:
                log.debug(f"Moviendo {src} → {dst}")
                self._client.rename(src.as_posix(), dst.as_posix())
            except Exception:
                log.error(f"Error moviendo {src}", exc_info=True)
                if not continue_on_error:
                    raise
