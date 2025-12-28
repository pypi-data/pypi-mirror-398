"""Module for SFTP credentials management."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SFTPCredentials:
    """Data class for SFTP connection credentials."""
    hostname: str
    username: str
    password: str
    port: int = 22
    timeout: float = 100000.0
