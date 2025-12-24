import asyncio
from concurrent.futures import ThreadPoolExecutor

from .watcher import SSLWatcher
from .certificate import SSLCertificate
from .exceptions import SSLWatchError


class HybridSSLWatcher:
    """
    Hybrid watcher:
    - asyncio for orchestration
    - ThreadPoolExecutor for blocking TLS
    """

    def __init__(
        self,
        timeout: int = 10,
        validate_chain: bool = True,
        max_workers: int = 20,
    ):
        self.sync_watcher = SSLWatcher(timeout, validate_chain)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def fetch_certificate(self, hostname: str, port: int = 443) -> SSLCertificate:
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                self.executor,
                self.sync_watcher.fetch_certificate,
                hostname,
                port,
            )
        except Exception as exc:
            raise SSLWatchError(str(exc)) from exc
