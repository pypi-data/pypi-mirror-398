import datetime
from typing import Dict, Any

from .utils import days_until


class SSLCertificate:
    def __init__(self, raw_cert: Dict[str, Any]):
        self.raw = raw_cert
        self.subject = dict(x[0] for x in raw_cert.get("subject", []))
        self.issuer = dict(x[0] for x in raw_cert.get("issuer", []))
        self.not_before = self._parse_date(raw_cert.get("notBefore"))
        self.not_after = self._parse_date(raw_cert.get("notAfter"))
        self.serial_number = raw_cert.get("serialNumber")
        self.version = raw_cert.get("version")

    @staticmethod
    def _parse_date(value: str) -> datetime.datetime:
        return datetime.datetime.strptime(value, "%b %d %H:%M:%S %Y %Z")

    @property
    def days_remaining(self) -> int:
        return days_until(self.not_after)

    @property
    def is_expired(self) -> bool:
        return self.days_remaining < 0

    def is_expiring_soon(self, threshold: int = 30) -> bool:
        return 0 <= self.days_remaining <= threshold
