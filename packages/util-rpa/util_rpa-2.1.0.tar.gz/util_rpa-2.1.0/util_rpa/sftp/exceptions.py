"""Exceptions for SFTP operations."""


class SFTPError(Exception):
    """Base exception for SFTP-related errors."""
    pass


class SFTPConnectionError(SFTPError):
    """Exception raised for SFTP connection errors."""
    pass


class SFTPPathError(SFTPError):
    """Exception raised for SFTP path errors."""
    pass


class SFTPFileNotFound(SFTPError):
    """Exception raised when a file is not found on the SFTP server."""
    pass
