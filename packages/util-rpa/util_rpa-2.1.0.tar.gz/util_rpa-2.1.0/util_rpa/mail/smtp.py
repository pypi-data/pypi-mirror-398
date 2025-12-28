"""SMTP client for sending emails."""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional

from util_rpa.mail.smtp_result import SMTPSendResult
from .models import EmailMessage

log = logging.getLogger(__name__)


class SMTPClient:
    """SMTP client for sending emails."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        secure: Optional[str] = None
    ):
        # 1️⃣ Cargar variables de entorno de prioridad
        env_host = os.getenv("SMTP_HOST")
        env_port = os.getenv("SMTP_PORT")

        # 2️⃣ Validar host obligatorio
        self.host = env_host or host
        if not self.host:
            raise ValueError(
                "No SMTP host configured. Set SMTP_HOST env variable or pass host parameter"
            )

        # 3️⃣ Puerto obligatorio
        self.port = int(env_port) if env_port else port
        if not self.port:
            raise ValueError(
                "No SMTP port configured. Set SMTP_PORT env variable or pass port parameter"
            )

        # 4️⃣ Auth opcional
        self.user = os.getenv("SMTP_USER") or user
        self.password = os.getenv("SMTP_PASSWORD") or password

        # 5️⃣ Secured settings
        self.secure = os.getenv("SMTP_SECURE") or secure
        if self.secure not in [None, "SSL", "TLS"]:
            raise ValueError("SMTP_SECURE must be None, 'SSL', or 'TLS'")

    def send(self, msg: EmailMessage) -> SMTPSendResult:
        """Envía un correo SMTP."""
        server = None  # Inicializar para el finally
        try:
            # 1️⃣ Validar adjuntos
            for f in msg.attachments or []:
                p = Path(f)
                if not p.exists() or not p.is_file():
                    raise FileNotFoundError(f"Attachment not found: {f}")

            mime = MIMEMultipart()
            mime["From"] = msg.sender

            # Normalizar destinatarios a lista
            to_list = msg.to if isinstance(msg.to, list) else [msg.to]
            mime["To"] = ",".join(to_list)
            mime["Subject"] = msg.subject

            if msg.cc:
                cc_list = msg.cc if isinstance(msg.cc, list) else [msg.cc]
                mime["Cc"] = ",".join(cc_list)
            else:
                cc_list = []

            mime.attach(MIMEText(msg.body_html, "html", "utf-8"))

            if msg.attachments:
                for f in msg.attachments:
                    p = Path(f)
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(p.read_bytes())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={p.name}",
                    )
                    mime.attach(part)

            # Construir lista completa de destinatarios
            bcc_list = []
            if msg.bcc:
                bcc_list = msg.bcc if isinstance(msg.bcc, list) else [msg.bcc]

            recipients = to_list + cc_list + bcc_list

            # 2️⃣ Conexión
            if self.secure == "SSL":
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
                if self.secure == "TLS":
                    server.starttls()

            # 3️⃣ Auth
            if self.user:
                server.login(self.user, self.password)

            # 4️⃣ Envío
            log.info("Sending SMTP email from %s to %s via %s:%s", msg.sender, recipients, self.host, self.port)
            send_errors = server.sendmail(msg.sender, recipients, mime.as_string())
            server.quit()

            if send_errors:
                # Fallo parcial
                return SMTPSendResult(
                    success=False,
                    stage="partial_send",
                    smtp_errors=send_errors,
                    error="Algunos destinatarios no recibieron el correo.",
                )

            return SMTPSendResult(success=True)

        except FileNotFoundError as e:
            log.error("SMTP attachment error", exc_info=True)
            return SMTPSendResult(
                success=False,
                error=str(e),
                stage="attachment",
            )

        except smtplib.SMTPAuthenticationError as e:
            log.error("SMTP auth error", exc_info=True)
            return SMTPSendResult(
                success=False,
                error=str(e),
                stage="auth",
            )

        except smtplib.SMTPException as e:
            log.error("SMTP send error", exc_info=True)
            return SMTPSendResult(
                success=False,
                error=str(e),
                stage="send",
            )

        except Exception as e:
            log.error("SMTP unknown error", exc_info=True)
            return SMTPSendResult(
                success=False,
                error=str(e),
                stage="unknown",
            )
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
