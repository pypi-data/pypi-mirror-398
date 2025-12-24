class SSLWatchError(Exception):
    """Base exception untuk sslwatch."""


class CertificateValidationError(SSLWatchError):
    """Kesalahan validasi sertifikat (chain / CA)."""
