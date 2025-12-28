"""LEGACY MODULE (DEPRECATED).

Este archivo contiene código legacy histórico de util_rpa.
NO agregar nuevas funcionalidades aquí.

Usar módulos específicos:
- util_rpa.sftp
- util_rpa.mail
- util_rpa.sql
- util_rpa.logging_utils
"""

from util_rpa.sftp.sftp_credentials import SFTPCredentials
from util_rpa.sftp.sftp_client import SFTPClient
from util_rpa.mail.smtp_notifier import SMTPNotifier
from util_rpa.mail.smtp import SMTPClient
from util_rpa.mail.notify import default_error_context, notify_exception
from util_rpa.logging_utils import init_logging

from pathlib import Path, PurePosixPath
from typing import Union, Iterable, List
from os import PathLike
import time
from functools import wraps
import numpy as np
import datetime as dt
from dateutil import tz
import tarfile
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import fnmatch
import itertools
from string import ascii_lowercase
from datetime import datetime
from sqlite3 import Error
import sqlite3
import configparser
import subprocess
from logging import NullHandler
import logging
import shutil
import re
import os
import warnings
warnings.warn(
    "util_rpa.__init__ contiene código legacy. "
    "No usar para nuevas implementaciones.",
    DeprecationWarning,
    stacklevel=2
)


log = logging.getLogger(__name__)
log.addHandler(NullHandler())

StrOrPath = Union[str, PathLike[str]]
StrOrPathList = Union[str, PathLike[str], Iterable[str], Iterable[PathLike[str]]]


def xlsx_to_csv(filename="", sheet="", newfilename="", separator=""):
    """Funcion que mediante openpyxnl convierne un xlsx a csv(usar Pandas).

    Args:
        filename (str, optional): Archivo a convertir. Defaults to "".
        sheet (str, optional): Hoja a convertir del excel. Defaults to "".
        newfilename (str, optional): Archivo csv destino. Defaults to "".
        separator (str, optional): Separador a usar en el csv. Defaults to "".
    """

    import openpyxl
    import csv
    xlsx = openpyxl.load_workbook(filename)
    sheet = xlsx.active
    data = sheet.rows

    csv = open(newfilename, "w+")

    for row in data:
        l = list(row)
        for i in range(len(l)):

            value = ''

            if str(l[i].value) != "None":
                value = str(l[i].value)

            if i == len(l) - 1:
                csv.write(value)
            else:
                csv.write(value + separator)

        csv.write('\n')

    csv.close()

    return


def upload_file_sftp(filename: StrOrPathList,
                     destine_path: StrOrPath,
                     credentials={}):
    """Funcion que sube archivos a un SFTP

    Args:
        filename (StrOrPathList): Nombre de archivo(acepta comodines unix * ?) 
                                  o lista de archivos. Defaults to [].
        destine_path (StrOrPath): Ruta destino remoto.
        credentials (dict, optional): Diccionario credenciales. Defaults to {}.
    """
    import paramiko

    puerto = 22
    try:
        puerto = credentials["port"]
    except:
        pass

    with paramiko.Transport((credentials["hostname"], puerto)) as transport:
        # SFTP FIXES
        transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE // 2
        # transport.default_max_packet_size = paramiko.common.MAX_WINDOW_SIZE
        # transport.packetizer.REKEY_BYTES   = pow(2, 40)  # 1TB max, this is a security degradation!
        # transport.packetizer.REKEY_PACKETS = pow(2, 40)  # 1TB max, this is a security degradation!

        # / SFTP FIXES
        transport.connect(username=credentials["username"], password=credentials["password"])
        with paramiko.SFTPClient.from_transport(transport) as server:
            server.get_channel().settimeout(100000.0)

            try:
                destine_path = PurePosixPath(destine_path).as_posix()
            except:
                raise Exception("Destino incorrecto")

            if str(destine_path) != ".":
                log.debug("Ubicandose en ruta remota: " + destine_path)
                server.chdir(destine_path)
            else:
                log.debug("Ubicandose en ruta default")

            if type(filename) is list:
                lista_archivos = []
                for p in filename:
                    try:
                        lista_archivos.append(Path(p))
                    except:
                        raise Exception("Un de los destinos es incorrecto")

                for i in lista_archivos:
                    log.debug("Subiendo archivo: " + str(i))
                    server.put(
                        i,
                        (PurePosixPath(destine_path) / i.name).as_posix())

            else:
                try:
                    filename = Path(filename)
                except:
                    raise Exception("Origen incorrecto")

                dir_local = filename.parent

                log.debug("Ubicandose en ruta local: " + str(dir_local))

                flag_exists = False
                log.debug("Buscando coincidencias con: " + filename.name)

                for file in dir_local.iterdir():

                    if fnmatch.fnmatch(file, filename.name):
                        flag_exists = True
                        filename_local = dir_local / file
                        log.debug("Subiendo archivo: " + str(filename_local))
                        server.put(
                            filename_local,
                            (PurePosixPath(destine_path) / file).as_posix())

                if not flag_exists:
                    raise Exception("No se encontró coincidencias para: " +
                                    str(filename))


def makedir_sftp(sftp_path: StrOrPath,
                 credentials={},
                 recursive=False,
                 mode=755):
    """Funcion que crea directorios en un SFTP

    Args:
        sftp_path (StrOrPath): Ruta remoto a crear.
        credentials (dict): Diccionario con credenciales. Defaults to {}.
        recursive (bool, optional): Flag que permite crear directorios
                                    recursivamente. Defaults to False.
        mode (int, optional): Permisos de directorio. Defaults to 755.
    """

    import paramiko

    puerto = 22
    try:
        puerto = credentials["port"]
    except:
        pass

    with paramiko.Transport((credentials["hostname"], puerto)) as transport:
        # SFTP FIXES
        transport.connect(username=credentials["username"], password=credentials["password"])
        with paramiko.SFTPClient.from_transport(transport) as server:
            server.get_channel().settimeout(100000.0)

            try:
                sftp_path = PurePosixPath(sftp_path).as_posix()
            except:
                raise Exception("Directorio definido erroneo.")

            log.info("Inicio creacion directorio:" + sftp_path)

            if recursive:

                folder_list = sftp_path.split("/")

                print(folder_list)

                ini = 0
                ini_dir = ""

                if sftp_path[0:1] == "/":
                    log.info("Trabajando con directorio absoluto '/' ")
                    ini = 1
                    ini_dir = "/"

                for i in range(ini + 1, len(folder_list) + 1):

                    abs_path = ini_dir + "/".join(folder_list[ini:i])
                    exists = False
                    try:
                        server.stat(abs_path)
                        exists = True
                    except:
                        pass

                    if not exists:
                        log.info("Creando directorio recursivo:" + abs_path)
                        server.mkdir(abs_path, mode)
                    else:
                        log.info("Directorio recursivo ya existe:" + abs_path)
                        continue

            else:
                exists = False
                try:
                    server.stat(sftp_path)
                    exists = True
                except:
                    pass

                if not exists:
                    log.info("Creando directorio no recursivo:" +
                             sftp_path)
                    server.mkdir(sftp_path, mode)
                else:
                    log.info("Directorio no recursivo ya existe:" +
                             sftp_path)


def list_sftp(sftp_path: StrOrPath,
              credentials={},
              attr=False):
    """Funcion que lista archivos de un SFTP

    Args:
        sftp_path (StrOrPath): Ruta remoto a listar.
        credentials (dict, optional): Diccionario credenciales. Defaults to {}.
        attr (bool, optional): Flag que permite borrar el archivo origen.
                               Defaults to False.

    Returns:
        list: Lista de archivos y directorios encontrado
    """

    import paramiko

    puerto = 22
    try:
        puerto = credentials["port"]
    except:
        pass

    with paramiko.Transport((credentials["hostname"], puerto)) as transport:
        # SFTP FIXES
        transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE // 2
        # transport.default_max_packet_size = paramiko.common.MAX_WINDOW_SIZE
        # transport.packetizer.REKEY_BYTES   = pow(2, 40)  # 1TB max, this is a security degradation!
        # transport.packetizer.REKEY_PACKETS = pow(2, 40)  # 1TB max, this is a security degradation!

        # / SFTP FIXES
        transport.connect(username=credentials["username"], password=credentials["password"])
        with paramiko.SFTPClient.from_transport(transport) as server:
            server.get_channel().settimeout(100000.0)

            try:
                sftp_path = PurePosixPath(sftp_path).as_posix()
            except:
                raise Exception("Ruta origen erronea.")

            server.chdir(sftp_path)
            if attr:
                filelist = server.listdir_attr()
            else:
                filelist = server.listdir()
            return filelist


def remove_sftp(list_files_sftp: StrOrPathList,
                credentials={},
                attr=False):
    """Funcion que borra archivos de un SFTP

    Args:
        list_files_sftp (StrOrPathList): Lista de archivos a borrar.
        credentials (dict, optional): Diccionario credenciales. Defaults to {}.
        attr (bool, optional): Flag que permite borrar el archivo origen.
                               Defaults to False.
    """

    import paramiko

    puerto = 22
    try:
        puerto = credentials["port"]
    except:
        pass

    with paramiko.Transport((credentials["hostname"], puerto)) as transport:
        # SFTP FIXES
        transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE // 2
        # transport.default_max_packet_size = paramiko.common.MAX_WINDOW_SIZE
        # transport.packetizer.REKEY_BYTES   = pow(2, 40)  # 1TB max, this is a security degradation!
        # transport.packetizer.REKEY_PACKETS = pow(2, 40)  # 1TB max, this is a security degradation!

        # / SFTP FIXES
        transport.connect(username=credentials["username"], password=credentials["password"])
        with paramiko.SFTPClient.from_transport(transport) as server:
            server.get_channel().settimeout(100000.0)

            for file in list_files_sftp:
                try:
                    log.info("Borrando archivo: " + file)
                    p_file = PurePosixPath(file).as_posix()
                    server.remove(p_file)
                except Exception as e:
                    log.info(str(e))
                    log.info("Ocurrio un error al borrar el archivo: " + file)


def download_file_sftp(filename: StrOrPathList,
                       destine_path: StrOrPath,
                       credentials={},
                       flag_remove=False):
    """Funcion que descargar archivos de un SFTP

    Args:
        filename (StrOrPathList): Nombre de archivo(acepta comodines unix * ?) 
                                  o lista de archivos.
        destine_path (StrOrPath): Ruta destino donde se hara la descarga.
        credentials (dict, optional): Diccionario credenciales. Defaults to {}.
        flag_remove (bool, optional): Flag que permite borrar el archivo 
                                      origen. Defaults to False.
    """

    import paramiko

    puerto = 22
    try:
        puerto = credentials["port"]
    except:
        pass

    with paramiko.Transport((credentials["hostname"], puerto)) as transport:
        # SFTP FIXES
        transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE // 2
        # transport.default_max_packet_size = paramiko.common.MAX_WINDOW_SIZE
        # transport.packetizer.REKEY_BYTES   = pow(2, 40)  # 1TB max, this is a security degradation!
        # transport.packetizer.REKEY_PACKETS = pow(2, 40)  # 1TB max, this is a security degradation!

        # / SFTP FIXES
        transport.connect(username=credentials["username"], password=credentials["password"])
        with paramiko.SFTPClient.from_transport(transport) as server:
            # server.get_channel().settimeout(100000.0)

            try:
                destine_path = Path(destine_path)
            except:
                raise Exception("Destino erroneo.")

            if type(filename) is list:

                lista_archivos: List[PurePosixPath] = []

                for i in filename:
                    try:
                        lista_archivos.append(PurePosixPath(i))
                    except:
                        raise Exception("Origen erroneo.")

                for file in lista_archivos:

                    dir_remoto = file.parent.as_posix()

                    log.debug("Ubicandose en ruta: " + str(dir_remoto))
                    server.chdir(dir_remoto)

                    destine = destine_path / file.name
                    log.debug("Obteniendo archivo: " + str(file))
                    log.debug("Ruta Destino: " + str(destine))

                    server.get(file.name, str(destine))

                    if flag_remove:
                        server.remove(file.name)
            else:

                try:
                    filename = PurePosixPath(filename)
                except:
                    raise Exception("Origen erroneo.")

                dir_remoto = filename.parent.as_posix()

                log.debug("Ubicandose en ruta: " + dir_remoto)
                server.chdir(dir_remoto)
                dir_list = server.listdir()

                log.debug("Lista SFTP: " + str(dir_list))

                log.debug("Buscando coincidencias con: " +
                          filename.name)

                flag_exists = False

                for file in dir_list:

                    if fnmatch.fnmatch(file, filename.name):
                        flag_exists = True
                        filename_remoto = (filename.parent / file).as_posix()
                        log.debug("Obteniendo archivo: " + filename_remoto)

                        destine = destine_path / file
                        log.debug("Guardando en: " + str(destine))
                        server.get(file, str(destine))

                        if flag_remove:
                            server.remove(file)

                if not flag_exists:
                    raise Exception("No se encontró coincidencias para: " +
                                    str(filename))


def download_by_prefix_sftp(sftpPath: StrOrPath,
                            prefix="",
                            downloadPath: StrOrPath = "",
                            credentials={},
                            flag_remove=False):
    """Funcion que descarga archivos de un SFTP basado en prefijos

    Args:
        sftpPath (StrOrPath): Path origen del sftp.
        prefix (str, optional): Prefijo de archivo a descargar. Defaults to "".
        downloadPath (StrOrPath, optional): Path destino. Defaults to "".
        credentials (dict, optional): Diccionario con credenciales. Defaults to {}.
        flag_remove (bool, optional): Flag que permite borrar el archivo origen. Defaults to False.
    """

    import paramiko

    puerto = 22
    try:
        puerto = credentials["port"]
    except:
        pass

    with paramiko.Transport((credentials["hostname"], puerto)) as transport:
        # SFTP FIXES
        transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE // 2
        # transport.default_max_packet_size = paramiko.common.MAX_WINDOW_SIZE
        # transport.packetizer.REKEY_BYTES   = pow(2, 40)  # 1TB max, this is a security degradation!
        # transport.packetizer.REKEY_PACKETS = pow(2, 40)  # 1TB max, this is a security degradation!

        # / SFTP FIXES
        transport.connect(username=credentials["username"], password=credentials["password"])
        with paramiko.SFTPClient.from_transport(transport) as server:
            server.get_channel().settimeout(100000.0)

            try:
                sftpPath = PurePosixPath(sftpPath)
            except:
                raise Exception("Origen erroneo")

            try:
                downloadPath = Path(downloadPath)
            except:
                raise Exception("Destino erroneo")

            server.chdir(sftpPath.as_posix())
            filelist = server.listdir()
            log.debug("Lista SFTP: " + str(len(filelist)))

            for filename in filelist:
                path_file = downloadPath / filename

                if prefix in filename:
                    log.debug("Obteniendo archivo: " + str(sftpPath / filename))
                    log.debug("Ruta Destino: " + str(path_file))
                    server.get(filename, str(path_file))

                    if flag_remove:
                        if path_file.exists:
                            server.remove(filename)
                        else:
                            log.error("Ocurrio un error al obtener archivo: " +
                                      str(path_file))
                            continue


def move_sftp(filenames: dict,
              credentials={}):
    """Funcion que renombra un archivo en SFTP

    Args:
        filenames (dict): Key archivo original y Value archivo destino.
        credentials (dict, optional): Diccionario credenciales. Defaults to {}.

    Raises:
        Exception: Generado al fallar 
    """

    import paramiko

    puerto = 22
    try:
        puerto = credentials["port"]
    except:
        pass

    with paramiko.Transport((credentials["hostname"], puerto)) as transport:
        # SFTP FIXES
        transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE // 2
        # transport.default_max_packet_size = paramiko.common.MAX_WINDOW_SIZE
        # transport.packetizer.REKEY_BYTES   = pow(2, 40)  # 1TB max, this is a security degradation!
        # transport.packetizer.REKEY_PACKETS = pow(2, 40)  # 1TB max, this is a security degradation!

        # / SFTP FIXES
        transport.connect(username=credentials["username"], password=credentials["password"])
        with paramiko.SFTPClient.from_transport(transport) as server:
            server.get_channel().settimeout(100000.0)

            if type(filenames) is not dict:
                raise Exception("No se recibio diccionario de datos.")

            pendientes = {}

            for origin, destine in filenames.items():
                try:
                    pendientes[PurePosixPath(origin)] = PurePosixPath(destine)
                except:
                    raise Exception("Rutas ingresadas estan erroneas.")

            for origin, destine in pendientes.items():
                log.debug("Moviendo: " + str(origin) + " hacia " + str(destine))
                server.rename(origin, destine)


def send_mail_by_exe(credentials={}, mail={}):
    """Funcion que permite ejecutar envio de correo a traves de un ejecutable inhouse.

    Args:
        credentials (dict, optional): Diccionario con credenciales del correo. Defaults to {}.
        mail (dict, optional): Diccionario con datos del correo a enviar. Defaults to {}.

    Raises:
        Exception: Generado por no detectar los campos necesarios del envio
        Exception: Generado al ejecutar el ejecutable mail.exe
    """
    path = os.path.dirname(__file__)
    program = os.path.join(path, 'mail.exe')

    try:
        arguments = credentials['username'] + '|' + credentials['password'] + '|'
        arguments += credentials['server'] + '|' + credentials['port'] + '|'
        arguments += mail['sender'] + '|' + mail['reciepients'] + '|' + mail['cc'] + '|'
        arguments += mail['body'] + '|' + mail['subject'] + '|' + mail['attachment']
    except IndexError as e:
        log.error("Uno de los campos email no fue encontrado")
        raise Exception(e)

    try:
        subprocess.call([program, arguments])
    except Exception as e:
        log.error("Ocurrio un error al ejecutar:" + program)
        raise Exception(e)


def create_folders(lista_carpetas=[]):
    """Funcion que crea carpetas de trabajo

    Args:
        lista_carpetas (list, optional): Lista de carpetas a crear. Defaults to [].
    """

    for carpeta in lista_carpetas:
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)


def create_folder_env(dir_path):
    """Funcion que crea las carpetas de trabajo estándar de trabajo

    Args:
        dir_path (str): Directorio raiz donde se desea crear la estructura
    """

    dir_in = os.path.join(dir_path, "input")
    dir_out = os.path.join(dir_path, "output")
    dir_log = os.path.join(dir_path, "log")

    if not os.path.exists(os.path.join(dir_in, "backup")):
        os.makedirs(os.path.join(dir_in, "backup"))

    if not os.path.exists(os.path.join(dir_out, "backup")):
        os.makedirs(os.path.join(dir_out, "backup"))

    if not os.path.exists(dir_log):
        os.makedirs(dir_log)

    return


def config_logging(file_log=None, level=logging.DEBUG, console=True):
    """Funcion que configura la gestion de Logs

    Args:
        file_log (str, optional): Nombre del archivo log. Defaults to None.
        level (logging.level, optional): Nivel de log. Defaults to logging.DEBUG.
        console (bool, optional): Define si se acepta impresion en consola. Defaults to True.

    Returns:
        logger: logger de logging
    """

    formatter = logging.Formatter('%(asctime)-5s %(filename)s %(lineno)d %(levelname)-8s %(message)s')

    log = logging.getLogger(__name__)

    # logging file
    if file_log and file_log != "":
        fh = logging.FileHandler(file_log)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    # logging console
    if console:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        log.addHandler(ch)

    log.setLevel(level=level)
    log.info("Level log: " + logging.getLevelName(level))

    for i in log.handlers:
        log.info("Handler:" + type(i).__name__)

    return log


def check_if_string_in_file(filename, string_to_search):
    """ Check if any line in the file contains given string """
    # Open the file in read only mode
    with open(filename, 'r', errors='ignore', encoding='utf-8') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            # For each line, check if line contains the string
            if string_to_search.lower() in line.lower():
                return True
    return False


class Configuration(object):
    """Clase que permite cargar dinámicamente los archivos de configuración del proceso."""

    def __init__(self, file_config="Config.ini", section_names=["DEFAULT"]):
        """Inicializa los parametros de entrada

        Args:
            file_config (str, optional): Ruta absoluta del archivo de configuración. Defaults to "Config.ini".
            section_names (list, optional): Lista de secciones a cargar. Defaults to ["DEFAULT"].

        Raises:
            ValueError: Generado al no encontrar el archivo de configuracion
        """

        parser = configparser.ConfigParser(interpolation=EnvInterpolation())
        parser.optionxform = str
        found = parser.read(file_config)

        if not found:
            raise ValueError('Archivo de configuracion no encontrado.')

        self.parser = parser

        # Cargando configuracion
        for name in section_names:
            self.__dict__.update(parser.items(name))


class EnvInterpolation(configparser.BasicInterpolation):
    """Interpolation which expands environment variables in values."""

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)
        return os.path.expandvars(value)


def create_connection_sqlite(db_file=""):
    """ Funcion que crea una coneccion a la base de datos SQLite

    Args:
        db_file (str, optional): Ruta absoluta del archivo sqlite. Defaults to "".

    Returns:
        Connection: Coneccion sqlite
    """

    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """

    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def get_now_format(format="%Y%m%d%H%M%S%f"):
    """Funcion que devuelve la fecha actual bajo un formato."""
    return str(datetime.now().strftime(format))


def replace_string_in_file(filename_in: StrOrPath,
                           filename_out: StrOrPath,
                           dict_words):
    """Funcion que eemplaza cadenas de un archivo

    Args:
        filename_in (StrOrPath): Archivo entrada.
        filename_out (StrOrPath): Archivo salida.
        dict_words (dict): Diccionario de palabras y valores a reemplazar.
    """

    write_obj = open(filename_out, 'w')

    line = ""

    with open(filename_in, 'r') as read_obj:
        for line in read_obj:

            for k, v in dict_words.items():
                line = line.replace(k, v)

            # log.debug(line)
            write_obj.write(line)

    write_obj.close()


def sqlcmd(file_sql: StrOrPath,
           credentials,
           file_sql_log: StrOrPath,
           dict_variable={},
           validate_error=True,
           coding="65001"):
    """Funcion que ejecuta el utilitario SQLCMD de SQLServer en linea de comandos

    Args:
        file_sql (StrOrPath): Archivo SQL
        credentials (dict): Diccionario con credenciales SQL
        file_sql_log (StrOrPath): Archivo prefijo para generar archivo log.
        dict_variable (dict, optional): Diccionario de variables a reemplazar. 
                                        Defaults to {}.
        validate_error (bool, optional): Flag para generar exception si se 
                                         encuentra la palabra error. 
                                         Defaults to True.
        coding (str, optional): Coding de respuesta. Defaults to "65001".

    Raises:
        FileNotFoundError: Se necesita ingresar archivo sql
        Exception: Se necesita ingresar archivo log
        Exception: Se encontro un error en el archivo log de la BD
        Exception: Archivo output sqlcmd no generado
    """

    sqlcmd_bin = '/opt/mssql-tools/bin/sqlcmd'

    if os.name == 'nt':
        sqlcmd_bin = 'sqlcmd'

    file_sql = Path(file_sql)
    file_sql_log = Path(file_sql_log)

    if not file_sql.exists():
        raise FileNotFoundError(file_sql)

    file_sql_tmp = Path(str(file_sql) + ".tmp")

    if len(dict_variable) > 0:
        if file_sql_tmp.exists():
            file_sql_tmp.unlink()
        replace_string_in_file(file_sql, file_sql_tmp, dict_variable)
    else:
        shutil.copy(file_sql, file_sql_tmp)

    cmd = (sqlcmd_bin + ' -e -y 0' +
                        ' -i ' + str(file_sql_tmp) +
                        ' -o ' + str(file_sql_log) +
                        ' -S ' + credentials['hostname'] +
                        ' -d ' + credentials['database'] +
                        ' -U ' + credentials['username'] +
                        ' -P ' + credentials['password'] +
                        ' -f ' + coding)

    log.debug("Ejecutando sql")
    log.debug(cmd)

    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    while proc.poll() is None:
        line = proc.stdout.readline()
        # log.debug(line.rstrip())
        if isinstance(line, bytes):
            str_line = line.decode("utf-8")
        else:
            str_line = line

        if str_line != "":
            log.debug(str_line)

    file_sql_tmp.unlink()

    if file_sql_log.exists():
        log.debug(open(file_sql_log,
                       "r",
                       encoding='utf-8',
                       errors='ignore').read())

        if validate_error:
            if check_if_string_in_file(file_sql_log, "error"):
                raise Exception("Se encontro un error en el archivo log.")
    else:
        raise Exception("Archivo output sqlcmd no generado.")


def bcp(table,
        file: StrOrPath,
        operation,
        credentials,
        file_sql_log: StrOrPath,
        validate_error=True,
        coding="-C 65001"):
    """Funcion que ejecuta el utilitario BCP de SQLServer en linea de comandos

    Args:
        table (str): Tabla a trabajar
        file (str): Archivo de entrada o salida segun la operacion
        operation (str): operacion a ejecutar IN u OUT
        credentials (str): Credenciales de conexion a la Base de Datos SQLServer
        file_sql_log (str): Archivo prefijo para generar archivo log (file_sql_log + ".ahora.db")
        validate_error (bool, optional): Flag para generar exception si se encuentra la palabra error. Defaults to True.
        coding (str, optional): Coding de respuesta. Defaults to "65001".

    Raises:
        Exception: Se necesita ingresar archivo log
        Exception: Operacion BCP no permitida
        Exception: Se encontro un error en el archivo log de la BD
        Exception: Archivo output bcp no generado
    """

    bcpcmd_bin = '/opt/mssql-tools/bin/bcp'
    if os.name == 'nt':
        bcpcmd_bin = 'bcp'

    file = Path(file)
    file_sql_log = Path(file_sql_log)

    if not operation in ("IN", "OUT"):
        raise Exception("Operacion BCP no permitida")

    cmd = (bcpcmd_bin + ' ' + table + ' ' +
           operation + ' "' + str(file) + '"' +
           ' -e ' + str(file_sql_log) +
           ' -S ' + credentials['hostname'] +
           ' -d ' + credentials['database'] +
           ' -U ' + credentials['username'] +
           ' -P ' + credentials['password'] +
           ' -c ' + coding +
           ' -b1000 -m1000 -t"|"')

    log.debug("Ejecutando sql")
    log.debug(cmd)

    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    while proc.poll() is None:
        line = proc.stdout.readline()
        # log.debug(line.rstrip())
        if isinstance(line, bytes):
            str_line = line.decode("utf-8")
        else:
            str_line = line

        if str_line != "":
            log.debug(str_line)

    if file_sql_log.exists():
        log.debug(open(file_sql_log, "r", encoding='utf-8').read())

        if validate_error:
            if check_if_string_in_file(file_sql_log, "error"):
                raise Exception("Se encontro un error en el archivo log")
    else:
        raise Exception("Archivo output bcp no generado.")


def get_data_from_sqllog(file_sql_log: StrOrPath,
                         file_result: StrOrPath,
                         prefix="DATA:"):
    """Funcion que filtra las lineas de texto que comiencen con el prefijo

    Args:
        file_sql_log (str): Archivo log de entrada
        file_result (str): Archivo resultado
        prefix (str, optional): Prefijo a filtrar los datos. Defaults to "DATA:".

    Raises:
        FileNotFoundError: Archivo de entrada no encontrado
    """

    file_sql_log = Path(file_sql_log)
    file_result = Path(file_result)

    if not file_sql_log.exists():
        raise FileNotFoundError(file_sql_log)

    file_out = open(file_result, "w", encoding='utf-8')

    with open(file_sql_log, 'r', encoding='utf-8', errors='ignore') as res:
        f_data = False

        for line in res:
            if re.match("INI_DATA_SQLSERVER", line):
                log.debug("UBICADO:"+line)
                f_data = True
            if f_data and re.search(prefix, line):
                file_out.write(line.replace(prefix, ""))

    file_out.close()


def iter_all_strings():
    """Funcion que devuelve lista de letras secuenciales

    Yields:
        str: Secuencia
    """

    for size in itertools.count(1):
        for s in itertools.product(ascii_lowercase, repeat=size):
            yield "".join(s)


def enviar_correo_smtp(mail):
    """Funcion que envia correos via SMTP

    Args:
        mail (dict): Diccionanrio con credenciales smtp y cuerpo de correo

    Returns:
        bool: Resultado de ejecucion
    """

    try:
        email_smtp_host = mail['smtp_host']
        email_smtp_port = mail['smtp_port']
        email_from = mail['from']
        email_to = mail['to'].split(';')
        email_cc = mail['cc'].split(';')
        email_subject = mail['subject']
        email_body = mail['body']
        email_attachment = mail['attachment']
    except Exception as e:
        log.info(e, exc_info=True)
        log.info("Uno de los parametros del correo no esta definido")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = ','.join(email_to)
        msg['Subject'] = email_subject
        msg['cc'] = ','.join(email_cc)

        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        # msg.attach(MIMEText(email_body,'plain'))

        emails = email_to + email_cc

        filename = mail['attachment']

        if filename != "":
            for filename in email_attachment.split(";"):
                attachment = open(filename, 'rb')
                part = MIMEBase('application', 'octet-stream')
                part.set_payload((attachment).read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= " + os.path.basename(filename))
                msg.attach(part)

        text = msg.as_string()
        server = smtplib.SMTP(host=email_smtp_host, port=email_smtp_port)

        server.sendmail(email_from, emails, text)
        server.quit()
    except Exception as e:
        log.info(e, exc_info=True)
        log.info("Ocurrio un error al enviar el correo")
        return False

    return True


def comprimir(lista_objetos=[], nombre_salida="archivo_salida", tipo_compresion="tgz"):
    """Funcion que comprime archivos y carpetas

    Args:
        lista_objetos (list, optional): Lista de objetos a comprimir. Defaults to [].
        nombre_salida (str, optional): Nombre de archivo salida. Defaults to "archivo_salida".
        tipo_compresion (str, optional): Tipo de compresion. Defaults to "tgz".

    Raises:
        Exception: Ocurrio un error en la compresion
        Exception: Tipo compresion no identificada
    """

    if tipo_compresion == "tgz":
        try:
            with tarfile.open(nombre_salida + ".tgz", "w:gz") as tar:
                for name in lista_objetos:
                    tar.add(name)
                tar.list()
        except Exception as e:
            log.error(str(e), exc_info=True)
            raise Exception("Ocurrio un error en la compresion")
    else:
        raise Exception("Tipo compresion no identificada")


def convertir_local_a_utc(fecha_local):
    fecha_local = fecha_local.replace(tzinfo=tz.tzlocal())
    fecha_utc = fecha_local.astimezone(tz.tzutc())
    return fecha_utc


class RpaNotificacionCorreo:
    """Clase que define la configuracion y metodos para el envio de Correo."""

    def __init__(self, host="10.226.5.191", port="25", secure_mode=None, use_executable=False, **kwargs):
        """Funcion que inicializa valores plantilla del correo a enviar

        Args:
            host (str, optional): Ip del servidor de correos SMTP. Defaults to "10.226.5.191".
            port (str, optional): Puerto del servidor de correos SMTP. Defaults to "25".
            secure_mode (_type_, optional): Modo seguro para autenticarse. Solo puede ingresarse SSL o TLS. Defaults to None.
            use_executable (bool, optional): Booleano que determina si se debe o no usar el .exe (contigencia). Defaults to False.
            **kwargs : optional
                Parametros opcionales para la autenticacion
                user
                password
        Raises:
            ValueError: secure_mode: Solo pude ingresar el modo seguro SSL o TLS
        """

        self.host = host
        self.port = port

        # Definiendo modo seguro
        self.secure_mode = None
        if secure_mode:
            if not isinstance(secure_mode, str) or secure_mode not in ["SSL", "TLS"]:
                raise ValueError("secure_mode: Solo pude ingresar el modo seguro SSL o TLS")
            self.secure_mode = secure_mode

        # Definiendo autenticacion. Por defecto se usa relay smtp.
        self.use_auth = False
        if 'user' in kwargs and 'password' in kwargs:
            self.use_auth = True
            self.user = kwargs['user']
            self.password = kwargs['password']

        # Definiendo uso de contingenca .exe (Cuando no existe relay y los metodos SMTP
        # desarrollados hasta ahora no soportan el envio)
        self.use_executable = use_executable

        self.subject = ''
        self.body = ''
        self.email_from = ''
        self.email_to = []
        self.email_cc = []
        self.email_cco = []

    def __str__(self):
        """Funcion que devuelve los parametros configurados en los atributos.

        Returns:
            str: Servidor + Plantilla
        """

        con = ''
        if not self.use_auth:
            con += "Servidor : " + self.host + ":" + self.port + "\n"
        else:
            con += "Servidor: " + self.user + "/" + self.password + "@" + self.host + ":" + self.port + "\n"

        con += "Plantilla From   : " + self.email_from + "\n"
        con += "Plantilla To     : " + str(self.email_to) + "\n"
        con += "Plantilla Cc     : " + str(self.email_cc) + "\n"
        con += "Plantilla Cco    : " + str(self.email_cco) + "\n"
        con += "Plantilla Subject: " + self.subject + "\n"
        con += "Plantilla Body   : " + self.body

        return con

    def cargar_plantilla(self, subject_template=None, body_template=None, email_from=None, email_to=None, email_cc=None, email_cco=None):
        """Funcion que carga los valores plantilla del correo a enviar.

        Args:
            subject_template (_type_, optional): Asunto plantilla a usar en el correo. Defaults to None.
            body_template (_type_, optional): Cuerpo plantilla a usar en el correo. Defaults to None.
            email_from (_type_, optional): Emisor a colocar en el correo a enviar. Defaults to None.
            email_to (_type_, optional): Destinatarios a colocar en el correo a enviar. Si existe mas de uno,
                                         colocar como separador ';'. Defaults to None.
            email_cc (_type_, optional): Destinatarios Con Copia a colocar en el correo a enviar. Si existe mas de uno,
                                         colocar como separador ';'. Defaults to None.
            email_cco (_type_, optional): Destinatarios Con Copia Oculta a colocar en el correo a enviar. Si existe mas de uno,
                                          colocar como separador ';'. Defaults to None.

        Raises:
            ValueError: From: Debe ingresar un correo
            ValueError: From: Debe ingresar una cadena de correo(s) separados por ';'
            ValueError: Cc: Solo puede ingresar una cadena de correos separado por ';'
            ValueError: Cco: Solo puede ingresar una cadena de correos separado por ';'
            ValueError: Debe ingresar al menos un correo destinatario
        """

        if subject_template:
            self.subject = subject_template

        if body_template:
            self.body = body_template

        if type(email_from) not in [str]:
            raise ValueError("From: Debe ingresar un correo")

        if type(email_to) not in [str, type(None)]:
            raise ValueError("From: Debe ingresar una cadena de correo(s) separados por ';'")

        if type(email_cc) not in [str, type(None)]:
            raise ValueError("Cc: Solo puede ingresar una cadena de correos separado por ';'")

        if type(email_cco) not in [str, type(None)]:
            raise ValueError("Cco: Solo puede ingresar una cadena de correos separado por ';'")

        if type(email_to) == None and type(email_cc) == None and type(email_cco) == None:
            raise ValueError("Debe ingresar al menos un correo destinatario")

        self.email_from = email_from
        self.email_to = email_to.split(";") if type(email_to) == str else []
        self.email_cc = email_cc.split(";") if type(email_cc) == str else []
        self.email_cco = email_cco.split(";") if type(email_cco) == str else []

    def enviar_correo(self, subject_replace=None, body_replace=None, attachment_files=None):
        """Funcion que envia correos

        Args:
            subject_replace (_type_, optional): Palabras clave a reemplazar en el asunto del correo.
                                                Cada llave del diccionario será buscada en la plantilla 
                                                cargada inicialmente y reemplazada por su valor. Defaults to None.
            body_replace (_type_, optional): Palabras clave a reemplazar en el cuerpo del correo.
                                             Cada llave del diccionario será buscada en la plantilla cargada
                                             inicialmente y reemplazada por su valor.. Defaults to None.
            attachment_files (_type_, optional): Cadena de archivos a adjuntar en el correo. Los archivos
                                                 deben tener la ruta absoluta y estar separados por ';' en caso
                                                 de existir mas de uno. Defaults to None.

        Raises:
            ValueError: Ocurrio un error al enviar el correo

        Returns:
            bool: Se devolvera True si es que no se genero alguna excepcion. De lo contrario el valor
                  devuelto sera False
        """

        try:
            # Armando subject
            subject = self.subject
            if subject_replace:
                if type(subject_replace) != dict:
                    raise ValueError(
                        "Subject Replace: Debe ingresar un diccionario con las palabras clave a reemplazar")
                for i in subject_replace:
                    subject = str(subject).replace(i, subject_replace[i])

            # Armando body
            body = self.body
            if body_replace:
                if type(body_replace) != dict:
                    raise ValueError("Body Replace: Debe ingresar un diccionario con las palabras clave a reemplazar")
                for i in body_replace:
                    body = body.replace(i, body_replace[i])

        except Exception as e:
            log.info(e, exc_info=True)
            log.info("Ocurrio un error al enviar el correo")
            return False

        if not self.use_executable:
            log.info("Envio de correo via SMTPLib")
            try:
                msg = MIMEMultipart()
                msg['From'] = self.email_from
                msg['To'] = ','.join(self.email_to)
                msg['cc'] = ','.join(self.email_cc)
                msg['cco'] = ','.join(self.email_cco)
                msg['Subject'] = subject

                # Integrando
                msg.attach(MIMEText(body, 'html', 'utf-8'))

                # Armando lista de correos
                emails = self.email_to + self.email_cc + self.email_cco

                # Ingresando adjunto
                if attachment_files:
                    for filename in attachment_files.split(";"):
                        attachment = open(filename, 'rb')
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload((attachment).read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', "attachment; filename= " + os.path.basename(filename))
                        msg.attach(part)

                # Enviando
                text = msg.as_string()

                if not self.secure_mode:
                    # Usado en el relay smtp telefonica robotizacion
                    server = smtplib.SMTP(host=self.host, port=self.port)
                    if self.use_auth:
                        # Habilitado si es que en algun momento se necesita autenticar
                        server.login(self.user, self.password)
                else:
                    # Habilitado para conexiones seguras en el futuro
                    if self.secure_mode == "SSL":
                        server = smtplib.SMTP_SSL(host=self.host, port=self.port)
                    if self.secure_mode == "TLS":
                        server = smtplib.SMTP(host=self.host, port=self.port)
                        server.starttls()

                    if self.use_auth:
                        server.login(self.user, self.password)

                server.sendmail(self.email_from, emails, text)
                server.quit()
            except Exception as e:
                log.info(e, exc_info=True)
                log.info("Ocurrio un error al enviar el correo")
                return False
        else:
            log.info("Envio de correo via executable")
            try:
                path = os.path.dirname(__file__)
                program = os.path.join(path, 'bin', 'mail.exe')

                attachment = ''
                if attachment_files:
                    attachment = attachment_files

                arguments = self.user + '|' + self.password + '|'
                arguments += self.host + '|' + self.port + '|'
                arguments += self.email_from + '|' + ";".join(self.email_to) + '|' + ";".join(self.email_cc) + '|'
                arguments += body + '|' + subject + '|' + attachment
            except IndexError as e:
                log.info(e, exc_info=True)
                log.error("Uno de los campos email no fue encontrado")
                return False

            try:
                subprocess.call([program, arguments])
            except Exception as e:
                log.error("Ocurrio un error al ejecutar:" + program)
                return False

        return True


def isleap(year):
    """Funcion que devuelve True para años bisiestos y False para los que no lo son"""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def feriados_santos(anio):
    """Función que devuelve feriados santos"""
    # Calcular el resto de la division año/19
    a = anio % 19
    # Calcular el cociente entero de la division año/100
    b = anio//100
    # Calcular el resto de la division año/100
    c = anio % 100
    # Calcular cociente de la división b/4
    d = b//4
    # Calcular el resto de la división b/4
    e = b % 4
    # Calcular el cociente de la división (b+8)/25
    f = (b+8)//25
    # Calcular el cociente de la división (b-f+1)/3
    g = (b-f+1)//3
    # Calcular el resto de la división (19*a+b-d-g+15)/30
    h = (19*a+b-d-g+15) % 30
    # Calcular el cociente de la división c/4
    i = c//4
    # Calcular el resto de la división c/4
    k = c % 4
    # Calcular el resto de la división (32+2*e+2*i-h-k)/7
    l = (32+2*e+2*i-h-k) % 7
    # Calcular el cociente de la división (a+11*h+22*l)/451
    m = (a+11*h+22*l)//451
    # Calcular la suma h+l-7*m+114
    n = h+l-7*m+114
    # Mes,Calcular el cociente de la división n/31
    mes = n//31
    # Dia,calcular 1 + (el resto de n/31) o bien 1+(n-(mes*31))
    dia = 1+n % 31

    pascua = datetime(anio, mes, dia)
    jueves_santo = pascua - dt.timedelta(3)
    viernes_santo = pascua - dt.timedelta(2)
    dia_jueves = jueves_santo.timetuple().tm_yday
    dia_viernes = viernes_santo.timetuple().tm_yday
    return (dia_jueves, dia_viernes)


def lista_feriados(anio):
    """Función que añade los feriados de semana santa a los feriados predefinidos"""
    # Lista de feriados fijos
    lista_feriados = np.array([1, 121, 180, 209, 210, 242, 281, 305, 342, 343, 359], dtype=int)
    # Añadir feriados de semana santa
    jueves, viernes = feriados_santos(anio)
    lista_feriados = np.append(lista_feriados, [jueves, viernes], axis=0)
    lista_feriados.sort()
    # Si es bisiesto sumar 1 a los días después de Febrero 29 (día 60)
    if isleap(anio):
        log.info("El año " + str(anio) + " es un año bisiesto")
        feriados_afectados = np.fromiter(
            (element + 1 for element in lista_feriados if element > 60), dtype=lista_feriados.dtype)
        feriados_desafectados = np.fromiter(
            (element for element in lista_feriados if element <= 60), dtype=lista_feriados.dtype)
        lista_feriados = np.concatenate((feriados_desafectados, feriados_afectados), axis=0)

    return list(lista_feriados)


def notifica_exception(exception=None, notifica=None, lista_exceptions_bl=[], subject_replace=None, body_replace=None):
    """Función que notifica todas las excepciones. Si alguna se encuentra en la lista blacklist, no se notifica"""
    if not subject_replace:
        subject_replace = "Error"
    if not body_replace:
        body_replace = "IDS000-Ocurrio un error generico en el proceso: "

    if str(type(exception).__name__).startswith("ID"):
        if type(exception).__name__ not in lista_exceptions_bl:
            notifica.enviar_correo({'[TEXTO]': subject_replace}, {'[TEXTO]': str(exception)})
    else:
        notifica.enviar_correo({'[TEXTO]': subject_replace}, {'[TEXTO]': body_replace + str(exception)})


def timed(func):
    """Decorador para loggear el tiempo de ejecucion de una funcion.

    Args:
        func (object): funcion que sera decorada

    Returns:
        wrapper: funcion decorada
    """

    func_name = func.__name__

    @wraps(func)
    def wrapper(*args, **kwargs):

        log.info("############### Inicio: {} ###############".format(func_name))

        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        log.info("## Tiempo transcurrido: {}".format(round(duration, 2)))
        log.info("############### Fin: {} ###############".format(func_name))

        return result

    return wrapper


# ------------------------------------------------------------------
# API OFICIAL (NUEVA)
# - Clientes y utilidades base soportadas
# - Legacy interno NO debe ser usado directamente
# ------------------------------------------------------------------

__all__ = [
    "SMTPClient",
    "SMTPNotifier",
    "SFTPClient",
    "SFTPCredentials",
    "default_error_context",
    "notify_exception",
    "init_logging"
]
