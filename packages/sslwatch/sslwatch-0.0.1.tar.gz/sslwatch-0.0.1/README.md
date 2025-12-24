# sslwatch - **Python SSL/TLS Certificate Monitoring Engine**

## Apa itu sslwatch?
``sslwatch`` adalah **library Python murni** untuk **pemantauan sertifikat SSL/TLS** yang dirancang sebagai **core engine**, bukan aplikasi.

Library ini dibuat untuk:
- Sistem monitoring internal
- Platform observability
- Security & compliance automation
- SRE / DevOps tooling
- Enterprise certificate inventory

## Fitur Utama (Lengkap)
**SSL Certificate Inspection**
- Ambil sertifikat SSL dari endpoint TLS
- Ekstraksi lengkap:
  - Subject
  - Issuer
  - Serial number
  - Version
  - Validity period
- Hitung hari tersisa sebelum expired

**Certificate Chain & CA Validation**
- Validasi certificate chain penuh
- Verifikasi trusted CA (OS trust store)
- Deteksi:
  - Sertifikat expired
  - Self-signed certificate
  - Chain tidak lengkap
  - CA tidak trusted
  - Hostname mismatch

**Bulk SSL Monitoring**
- Monitoring **puluhan**, **ratusan**, hingga **ribuan** domain
- Error-tolerant:
  - Satu domain gagal ≠ batch gagal
- Return hasil terstruktur per host

**Async (asyncio)**
- Async TLS connection
- Cocok untuk high-concurrency
- Non-blocking orchestration

**Hybrid Async + ThreadPool**
- Async orchestration (``asyncio``)
- Blocking TLS handshake di ``ThreadPoolExecutor``
- Solusi paling **stabil & scalable** untuk Python
[x] Aman untuk ribuan host
[x] Tidak membekukan event loop
[x] Ideal untuk production

## Instalasi
```python
pip install sslwatch
```

Atau dari source:

```python
git clone https://github.com/Athallah1234/sslwatch
cd sslwatch
pip install .
```

## Contoh Penggunaan
1. **Single Domain (Sync)**
```python
from sslwatch import SSLWatcher

watcher = SSLWatcher()

cert = watcher.fetch_certificate("google.com")

print(cert.subject)
print(cert.issuer)
print(cert.days_remaining)
print(cert.is_expired)
```

2. **Bulk Monitoring (Sync)**
```python
from sslwatch import BulkSSLWatcher

hosts = ["google.com", "github.com", "expired.badssl.com"]

bulk = BulkSSLWatcher()
results = bulk.fetch_all(hosts)

for host, result in results.items():
    if isinstance(result, Exception):
        print(f"[ERROR] {host}: {result}")
    else:
        print(f"[OK] {host}: {result.days_remaining} hari")
```

3. **Async Monitoring (asyncio)**
```python
import asyncio
from sslwatch import AsyncBulkSSLWatcher

async def main():
    watcher = AsyncBulkSSLWatcher()
    results = await watcher.fetch_all([
        "google.com",
        "github.com",
        "expired.badssl.com"
    ])

    for host, result in results.items():
        print(host, result)

asyncio.run(main())
```

4. **Hybrid Async + ThreadPool**
```python
import asyncio
from sslwatch import HybridBulkSSLWatcher

async def main():
    watcher = HybridBulkSSLWatcher(
        max_workers=50
    )

    results = await watcher.fetch_all(
        hosts=[
            "google.com",
            "github.com",
            "cloudflare.com",
            "expired.badssl.com",
        ],
        concurrency=200,
    )

    for host, result in results.items():
        if isinstance(result, Exception):
            print("[ERROR]", host, result)
        else:
            print("[OK]", host, result.days_remaining)

asyncio.run(main())
```
[x] Async orchestration
[x] Blocking TLS di thread pool
[x] Paling aman & scalable

## Mode yang Tersedia
| Mode | Kelas | Kegunaan |
|------|-------|----------|
| Sync | ``SSLWatcher`` | Sederhana |
| Sync Bulk | ``BulkSSLWatcher`` | Batch kecil |
| Async | ``AsyncSSLWatcher`` | High concurrency |
| Async Bulk | ``AsyncBulkSSLWatcher`` | Async native |
| Hybrid | ``HybridSSLWatcher`` | TLS blocking |
| Hybrid Bulk | ``HybridBulkSSLWatcher`` | Production |

## Error Handling
Semua error bersifat eksplisit:
```python
SSLWatchError
└── CertificateValidationError
```
Contoh:
```python
try:
    watcher.fetch_certificate("invalid.host")
except Exception as e:
    handle_error(e)
```

## Struktur Proyek
```bash
sslwatch/
├── watcher.py          # Sync
├── bulk.py             # Sync bulk
├── async_watcher.py    # Async
├── async_bulk.py       # Async bulk
├── hybrid_watcher.py   # Hybrid
├── hybrid_bulk.py      # Hybrid bulk
├── chain.py            # Chain validation
├── async_chain.py
├── certificate.py
├── exceptions.py
├── utils.py
└── logger.py
```

## Lisensi
[MIT License]()
Bebas digunakan untuk:
- Komersial
- SaaS
- Open source
