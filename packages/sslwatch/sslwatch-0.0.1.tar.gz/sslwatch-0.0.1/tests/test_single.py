from sslwatch import SSLWatcher

watcher = SSLWatcher()

cert = watcher.fetch_certificate("google.com")

print("Issuer:", cert.issuer)
print("Subject:", cert.subject)
print("Expired:", cert.is_expired)
print("Days remaining:", cert.days_remaining)
