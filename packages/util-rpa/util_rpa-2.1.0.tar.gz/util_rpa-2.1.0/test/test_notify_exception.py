"""Tests para notify_exception."""
import logging
from util_rpa.mail.smtp import SMTPClient
from util_rpa.mail.smtp_notifier import SMTPNotifier
from util_rpa.mail.notify import default_error_context, notify_exception

log = logging.getLogger(__name__)


def test_notify_exception_integration(monkeypatch):
    """Test notify_exception con excepción real y blacklist."""
    # Plantillas de email
    EMAIL_SUBJECT = "Proceso RPA - ${TEXT_SUBJECT}"
    EMAIL_BODY = """${TEXT_BODY}"""

    # Configurar variables de entorno para SMTP
    monkeypatch.setenv("SMTP_HOST", "localhost")
    monkeypatch.setenv("SMTP_PORT", "2525")

    # Cliente SMTP
    client = SMTPClient()

    # Crear notificador
    notifier = SMTPNotifier(
        smtp=client,
        sender="robot.bolo@movistar.com.pe",
        to=["jonathan.bolo@integratel.com.pe"],
        cc=None,
        subject_template=EMAIL_SUBJECT,
        body_template=EMAIL_BODY,
    )

    # Simular una excepción
    try:
        raise RuntimeError("Fallo simulado en proceso RPA")
    except Exception as e:
        # 🚨 NOTIFICACIÓN DE EXCEPCIÓN
        result = notify_exception(
            exception=e,
            notifier=notifier,
            context=default_error_context(e),
            blacklist=[],  # o ["ID001Error", ...]
        )

        log.info(
            "Resultado notificación excepción: success=%s error=%s",
            result.success,
            result.error,
        )

        # Verificaciones
        assert result.success is True
        assert result.error is None
