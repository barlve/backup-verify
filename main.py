#!/usr/bin/env python3
"""backup-verify — pastikan backup benar-benar ada, segar, dan bisa dibaca.

    python3 main.py /var/backups --maks-umur 36h
    python3 main.py /var/backups --pola "*.dump" "*.sql.gz" --json hasil.json
"""
from __future__ import annotations
import argparse, gzip, json, sys, time
from datetime import datetime, timedelta
from pathlib import Path


def umur_jam(p: Path) -> float:
    return (time.time() - p.stat().st_mtime) / 3600


def bisa_dibaca(p: Path) -> tuple[bool, str]:
    try:
        if p.suffix == ".gz":
            with gzip.open(p, "rb") as f:
                f.read(4096)
            return True, "gzip ok"
        if p.suffix in {".sql", ".txt", ".json"}:
            with p.open("rb") as f:
                f.read(4096)
            return True, "teks ok"
        with p.open("rb") as f:  # dump biner: cukup cek header tidak kosong
            head = f.read(64)
        return (len(head) > 0, "biner ok" if head else "kosong")
    except Exception as e:  # noqa: BLE001
        return False, type(e).__name__


def parse_umur(s: str) -> float:
    n = float(s[:-1]); u = s[-1].lower()
    return n if u == "h" else n * 24 if u == "d" else n / 60


def main() -> int:
    ap = argparse.ArgumentParser(description="backup-verify")
    ap.add_argument("folder")
    ap.add_argument("--pola", nargs="*", default=["*.dump", "*.sql", "*.sql.gz", "*.tar.gz", "*.zip", "*.bak"])
    ap.add_argument("--maks-umur", default="36h", help="mis. 12h / 2d")
    ap.add_argument("--min-ukuran", type=int, default=1024, help="byte minimum agar dianggap valid")
    ap.add_argument("--json")
    a = ap.parse_args()

    root = Path(a.folder)
    if not root.exists():
        print("Folder tidak ada:", root); return 2

    batas = parse_umur(a.maks_umur)
    file = []
    for pola in a.pola:
        file += list(root.rglob(pola))
    file = sorted(set(file), key=lambda p: p.stat().st_mtime, reverse=True)

    if not file:
        print(f"❌ Tidak ada file backup di {root} (pola: {', '.join(a.pola)})")
        return 1

    print(f"\nbackup-verify · {root}")
    print(f"batas umur: {a.maks_umur} · file ditemukan: {len(file)}\n")
    masalah = 0
    keluaran = []
    for p in file[:10]:
        jam = umur_jam(p)
        ukuran = p.stat().st_size
        ok_baca, ket = bisa_dibaca(p) if ukuran > 0 else (False, "kosong")
        segar = jam <= batas
        cukup = ukuran >= a.min_ukuran
        status = "OK " if (segar and cukup and ok_baca) else "⚠️ "
        if status.strip() == "⚠️":
            masalah += 1
        print(f"{status} {p.name:45} {ukuran/1048576:7.1f} MB · {jam:5.1f} jam · {ket}")
        keluaran.append({"file": str(p), "mb": round(ukuran / 1048576, 2), "umur_jam": round(jam, 1), "segar": segar, "terbaca": ok_baca})

    terbaru = umur_jam(file[0])
    print(f"\nbackup terbaru: {file[0].name} ({terbaru:.1f} jam lalu)")
    if terbaru > batas:
        print("❌ backup terbaru melewati batas umur"); masalah += 1
    if a.json:
        Path(a.json).write_text(json.dumps({"folder": str(root), "file": keluaran, "masalah": masalah}, indent=2))
        print("JSON:", a.json)
    return 1 if masalah else 0


if __name__ == "__main__":
    sys.exit(main())
