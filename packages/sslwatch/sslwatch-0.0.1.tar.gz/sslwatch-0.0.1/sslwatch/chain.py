import ssl
import socket

from .exceptions import CertificateValidationError


class CertificateChainValidator:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def validate(self, hostname: str, port: int = 443) -> None:
        context = ssl.create_default_context()
        try:
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname):
                    pass
        except ssl.SSLCertVerificationError as exc:
            raise CertificateValidationError(str(exc)) from exc
        except Exception as exc:
            raise CertificateValidationError(str(exc)) from exc
