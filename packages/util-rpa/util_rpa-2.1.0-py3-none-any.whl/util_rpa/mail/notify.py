"""Notificación de excepciones por medio de un Notifier."""
from typing import Mapping, Iterable, Optional
import logging

from util_rpa.mail.notifier import Notifier
from util_rpa.mail.result import NotificationResult

log = logging.getLogger(__name__)


def default_error_context(exception: Exception) -> dict:
    """Construye el contexto estándar de error.

    Reglas:
    - Si el mensaje de la excepción ya contiene un código ID*, se usa tal cual
    - Caso contrario, se envuelve en un mensaje genérico
    """
    message = str(exception)

    if message.startswith("ID"):
        body = message
    else:
        body = f"Ocurrió un error genérico en el proceso: {message}"

    return {
        "TEXT_SUBJECT": "Error",
        "TEXT_BODY": body,
    }


def notify_exception(
    *,
    exception: Exception,
    notifier: Notifier,
    context: Optional[Mapping[str, str]] = None,
    blacklist: Optional[Iterable[str]] = None,
) -> NotificationResult:
    """Notifica una excepción sin interrumpir el flujo del proceso.

    - Respeta blacklist de excepciones ID*
    - Enriquece el contexto automáticamente
    - Nunca lanza excepción
    - Devuelve el resultado del intento de notificación
    """
    blacklist = set(blacklist or [])
    context = dict(context or {})

    exc_type = type(exception).__name__
    exc_text = str(exception)

    # 1️⃣ Blacklist legacy (ID*)
    if exc_type.startswith("ID") and exc_type in blacklist:
        log.info(
            "Excepción %s ignorada por blacklist, no se notifica",
            exc_type,
        )
        return NotificationResult(
            success=True,
            error=None,
        )

    # 2️⃣ Enriquecer contexto (sin pisar valores existentes)
    context.setdefault("EXCEPTION", exc_text)
    context.setdefault("EXCEPTION_TYPE", exc_type)

    # (opcional pero útil)
    context.setdefault("ERROR", exc_text)

    # 3️⃣ Notificar
    try:
        result = notifier.notify(context=context)

    except Exception as unexpected:
        # 🔒 Defensa extra: el notifier NO debería lanzar,
        # pero nunca permitimos que rompa el proceso.
        log.error(
            "Error inesperado notificando excepción",
            exc_info=True,
        )
        return NotificationResult(
            success=False,
            error=str(unexpected),
        )

    # 4️⃣ Observabilidad
    if not result.success:
        log.warning(
            "Notificación de excepción falló: %s",
            result.error,
        )

    return result
