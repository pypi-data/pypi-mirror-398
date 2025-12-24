import ssl
import asyncio

from .certificate import SSLCertificate
from .exceptions import SSLWatchError
from .async_chain import AsyncCertificateChainValidator


class AsyncSSLWatcher:
    def __init__(self, timeout: int = 10, validate_chain: bool = True):
        self.timeout = timeout
        self.validate_chain = validate_chain
        self.chain_validator = AsyncCertificateChainValidator(timeout)

    async def fetch_certificate(self, hostname: str, port: int = 443) -> SSLCertificate:
        context = ssl.create_default_context()
        try:
            if self.validate_chain:
                await self.chain_validator.validate(hostname, port)

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    hostname,
                    port,
                    ssl=context,
                    server_hostname=hostname,
                ),
                timeout=self.timeout,
            )

            ssl_obj = writer.get_extra_info("ssl_object")
            cert = ssl_obj.getpeercert()

            writer.close()
            await writer.wait_closed()

            return SSLCertificate(cert)
        except Exception as exc:
            raise SSLWatchError(str(exc)) from exc
