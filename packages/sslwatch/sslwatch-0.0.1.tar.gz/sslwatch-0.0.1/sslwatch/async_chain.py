import ssl
import asyncio

from .exceptions import CertificateValidationError


class AsyncCertificateChainValidator:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def validate(self, hostname: str, port: int = 443) -> None:
        context = ssl.create_default_context()
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    hostname,
                    port,
                    ssl=context,
                    server_hostname=hostname,
                ),
                timeout=self.timeout,
            )
            writer.close()
            await writer.wait_closed()
        except ssl.SSLCertVerificationError as exc:
            raise CertificateValidationError(str(exc)) from exc
        except Exception as exc:
            raise CertificateValidationError(str(exc)) from exc
