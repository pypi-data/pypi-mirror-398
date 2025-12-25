"""Custom exceptions for the RAIT Connector library."""


class RAITConnectorError(Exception):
    """Base exception for all RAIT Connector errors."""


class AuthenticationError(RAITConnectorError):
    """Raised when authentication fails."""


class EncryptionError(RAITConnectorError):
    """Raised when encryption/decryption operations fail."""


class MetricsError(RAITConnectorError):
    """Raised when metrics operations fail."""


class EvaluationError(RAITConnectorError):
    """Raised when evaluation operations fail."""


__all__ = [
    "RAITConnectorError",
    "AuthenticationError",
    "EncryptionError",
    "MetricsError",
    "EvaluationError",
]
