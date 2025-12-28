"""Data class representing an email message."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class EmailMessage:
    """Data class representing an email message."""
    sender: str
    to: List[str]
    subject: str
    body_html: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Path]] = None
