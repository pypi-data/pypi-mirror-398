"""Contrato genérico de notificación."""
from abc import ABC, abstractmethod
from typing import Mapping, Iterable, Optional
from pathlib import Path

from util_rpa.mail.result import NotificationResult


class Notifier(ABC):
    """Contrato genérico de notificación."""

    @abstractmethod
    def notify(
        self,
        *,
        context: Mapping[str, str],
        attachments: Optional[Iterable[Path]] = None,
    ) -> NotificationResult:
        """Envía una notificación genérica."""
        pass
