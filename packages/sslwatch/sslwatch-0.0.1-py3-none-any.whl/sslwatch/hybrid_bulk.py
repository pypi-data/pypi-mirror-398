import asyncio
from typing import Iterable, Dict, Union

from .hybrid_watcher import HybridSSLWatcher
from .certificate import SSLCertificate
from .exceptions import SSLWatchError
from .utils import normalize_hosts


class HybridBulkSSLWatcher:
    """
    Async orchestration + ThreadPoolExecutor TLS
    """

    def __init__(
        self,
        timeout: int = 10,
        validate_chain: bool = True,
        max_workers: int = 20,
    ):
        self.watcher = HybridSSLWatcher(timeout, validate_chain, max_workers)

    async def fetch_all(
        self,
        hosts: Iterable[str],
        port: int = 443,
        concurrency: int = 100,
    ) -> Dict[str, Union[SSLCertificate, SSLWatchError]]:

        semaphore = asyncio.Semaphore(concurrency)
        results = {}

        async def worker(host):
            async with semaphore:
                try:
                    results[host] = await self.watcher.fetch_certificate(host, port)
                except SSLWatchError as exc:
                    results[host] = exc

        await asyncio.gather(*(worker(h) for h in normalize_hosts(hosts)))
        return results
