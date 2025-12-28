"""Modulo de resultados de notificación."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NotificationResult:
    """Resultado de una notificación."""
    success: bool
    error: Optional[str] = None
