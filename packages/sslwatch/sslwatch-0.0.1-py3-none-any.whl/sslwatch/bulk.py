from typing import Iterable, Dict, Union

from .watcher import SSLWatcher
from .certificate import SSLCertificate
from .exceptions import SSLWatchError
from .utils import normalize_hosts


class BulkSSLWatcher:
    def __init__(self, timeout: int = 10, validate_chain: bool = True):
        self.watcher = SSLWatcher(timeout, validate_chain)

    def fetch_all(
        self,
        hosts: Iterable[str],
        port: int = 443,
    ) -> Dict[str, Union[SSLCertificate, SSLWatchError]]:
        results = {}
        for host in normalize_hosts(hosts):
            try:
                results[host] = self.watcher.fetch_certificate(host, port)
            except SSLWatchError as exc:
                results[host] = exc
        return results
