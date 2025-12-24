import datetime
from typing import Iterable


def days_until(date: datetime.datetime) -> int:
    return (date - datetime.datetime.utcnow()).days


def normalize_hosts(hosts: Iterable[str]) -> list[str]:
    return list({h.strip().lower() for h in hosts if h.strip()})
