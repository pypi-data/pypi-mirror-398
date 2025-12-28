"""Resultado del envío SMTP."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SMTPSendResult:
    """Resultado del envío SMTP."""
    success: bool
    error: Optional[str] = None
    stage: Optional[str] = None  # connect | auth | send | attachment | partial_send
    smtp_errors: Optional[dict] = None
