"""Notificador SMTP con plantillas."""
import logging
from string import Template
from typing import Mapping, Iterable, Optional
from pathlib import Path
from util_rpa.mail._template_utils import extract_template_variables
from util_rpa.mail.notifier import Notifier
from util_rpa.mail.models import EmailMessage
from util_rpa.mail.result import NotificationResult
from util_rpa.mail.smtp import SMTPClient

log = logging.getLogger(__name__)


class SMTPNotifier(Notifier):
    """Notificador SMTP con plantillas."""

    def __init__(
        self,
        *,
        smtp: SMTPClient,
        sender: str,
        to: list[str],
        cc: Optional[list[str]] = None,
        subject_template: str,
        body_template: str,
    ):
        self.smtp = smtp
        self.sender = sender
        self.to = to
        self.cc = cc or []

        self.subject_tpl = Template(subject_template)
        self.body_tpl = Template(body_template)

        # variables esperadas (cacheadas)
        self._subject_vars = extract_template_variables(self.subject_tpl)
        self._body_vars = extract_template_variables(self.body_tpl)
        self._expected_vars = self._subject_vars | self._body_vars

    def notify(
        self,
        *,
        context: Mapping[str, str],
        attachments: Optional[Iterable[Path]] = None,
    ) -> NotificationResult:
        """Envía una notificación por correo SMTP usando plantillas."""
        provided = set(context.keys())
        missing = self._expected_vars - provided

        if missing:
            log.warning(
                "Variables no provistas para plantilla: %s",
                ", ".join(sorted(missing)),
            )

        subject = self.subject_tpl.safe_substitute(context)
        body = self.body_tpl.safe_substitute(context)

        msg = EmailMessage(
            sender=self.sender,
            to=self.to,
            cc=self.cc,
            subject=subject,
            body_html=body,
            attachments=list(attachments or []),
        )

        result = self.smtp.send(msg)
        if not result.success:
            log.warning(
                "Notificación no enviada (stage=%s): %s",
                result.stage,
                result.error,
            )

        return NotificationResult(
            success=result.success,
            error=result.error,
        )
