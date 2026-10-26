# backup-verify

Memastikan backup **benar-benar ada, masih segar, dan bisa dibaca** — bukan hanya file yang menumpuk.

```bash
python3 main.py /var/backups --maks-umur 36h
python3 main.py /var/backups --pola "*.dump" "*.sql.gz" --json hasil.json
```

Exit code `1` bila backup terbaru kedaluwarsa atau file korup → cocok untuk cron + alert Telegram.
