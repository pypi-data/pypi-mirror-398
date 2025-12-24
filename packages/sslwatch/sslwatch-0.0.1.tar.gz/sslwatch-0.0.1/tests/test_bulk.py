from sslwatch import BulkSSLWatcher

hosts = [
    "google.com",
    "github.com",
]

bulk = BulkSSLWatcher()
results = bulk.fetch_all(hosts)

for host, result in results.items():
    if isinstance(result, Exception):
        print(f"[ERROR] {host}: {result}")
    else:
        print(f"[OK] {host}: {result.days_remaining} hari tersisa")
