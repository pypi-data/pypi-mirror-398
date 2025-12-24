import socket
import ssl

from .certificate import SSLCertificate
from .exceptions import SSLWatchError
from .chain import CertificateChainValidator


class SSLWatcher:
    def __init__(self, timeout: int = 10, validate_chain: bool = True):
        self.timeout = timeout
        self.validate_chain = validate_chain
        self.chain_validator = CertificateChainValidator(timeout)

    def fetch_certificate(self, hostname: str, port: int = 443) -> SSLCertificate:
        if self.validate_chain:
            self.chain_validator.validate(hostname, port)

        context = ssl.create_default_context()
        try:
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    return SSLCertificate(ssock.getpeercert())
        except Exception as exc:
            raise SSLWatchError(str(exc)) from exc
