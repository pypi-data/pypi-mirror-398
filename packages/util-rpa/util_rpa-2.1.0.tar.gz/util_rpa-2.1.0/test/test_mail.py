"""Tests for mail utilities."""
import datetime
import logging
from util_rpa.mail.smtp import SMTPClient
from util_rpa.mail.smtp_notifier import SMTPNotifier

log = logging.getLogger(__name__)


def test_smtp_notifier_integration(monkeypatch):
    """Test SMTPNotifier con plantillas y contexto real (flujo OK)."""
    # Plantillas de email
    EMAIL_SUBJECT = "[${OPERACION}] Proceso RPA - ${FECHA}"
    EMAIL_BODY = """
<h2>Hola ${USUARIO}</h2>
<p>Este es un test de envío desde util-rpa.</p>
<b>Estado:</b> ${ESTADO}
<br><br>
<small>Mensaje generado automáticamente.</small>
"""

    # Configurar variables de entorno para SMTP
    monkeypatch.setenv("SMTP_HOST", "localhost")
    monkeypatch.setenv("SMTP_PORT", "2525")

    # Cliente SMTP (host y puerto vienen del entorno)
    client = SMTPClient()
    log.info(
        "SMTP Client configurado: %s:%s user=%s",
        client.host,
        client.port,
        client.user,
    )

    # Crear notificador
    notifier = SMTPNotifier(
        smtp=client,
        sender="robot.bolo@movistar.com.pe",
        to=["jonathan.bolo@integratel.com.pe"],
        cc=None,
        subject_template=EMAIL_SUBJECT,
        body_template=EMAIL_BODY,
    )

    # Verificar que el notificador se creó correctamente
    assert notifier.sender == "robot.bolo@movistar.com.pe"
    assert notifier.to == ["jonathan.bolo@integratel.com.pe"]
    assert notifier.cc == []

    # Verificar que las variables esperadas fueron extraídas
    expected_vars = {"OPERACION", "FECHA", "USUARIO", "ESTADO"}
    assert notifier._expected_vars == expected_vars

    # Contexto para la notificación
    context = {
        "OPERACION": "Ingreso",
        "FECHA": datetime.datetime.today().strftime("%d/%m/%Y"),
        "USUARIO": "Jonathan",
        "ESTADO": "✔️ OK",
    }

    # Ejecutar notificación
    resultado = notifier.notify(context=context)

    # Verificaciones
    assert resultado.success is True
    assert resultado.error is None

    log.info("Test de notificación completado exitosamente")
