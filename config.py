"""
SPK Penilaian Risiko Penyebaran Hoaks — Application Configuration.

All constants are read-only. Module-level, no classes.
"""

from __future__ import annotations

import pathlib

# ── Paths ──────────────────────────────────────────────────
PROJECT_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parent
SQL_DIR: pathlib.Path = PROJECT_ROOT / "db"
EXPORT_DIR: pathlib.Path = PROJECT_ROOT / "exports"

# Ensure exports directory exists at import time.
EXPORT_DIR.mkdir(exist_ok=True)

# ── Application metadata ──────────────────────────────────
APP_TITLE: str = "SPK Penilaian Tingkat Risiko Penyebaran Hoaks"
APP_ORG: str = "Program Studi Ilmu Komputer — Universitas Pattimura"

# ── Database (MySQL / Laragon / XAMPP) ────────────────────
DB_CONFIG: dict[str, object] = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "spk_hoaks",
    "charset": "utf8mb4",
}

# ── Questionnaire scale ───────────────────────────────────
LIKERT_MIN: int = 1
LIKERT_MAX: int = 5

# ── Risk categories (Nilai → label) ──────────────────────
# Each tuple: (label, min_inclusive, max_inclusive)
KATEGORI_RISIKO: tuple[tuple[str, int, int], ...] = (
    ("Rendah", 1, 40),
    ("Sedang", 41, 70),
    ("Tinggi", 71, 100),
)

# ── Default admin credentials (seed only) ────────────────
ADMIN_DEFAULT_USERNAME: str = "admin"
ADMIN_DEFAULT_PASSWORD: str = "admin123"


def kategori_dari_nilai(nilai: float) -> str:
    """Map a 1–100 risk score to its category label.

    Returns 'Rendah', 'Sedang', or 'Tinggi'.
    Values outside 1–100 are clamped to the nearest band.
    """
    for label, lo, hi in KATEGORI_RISIKO:
        if lo <= nilai <= hi:
            return label
    # Clamp to extremes if out of range.
    if nilai < KATEGORI_RISIKO[0][1]:
        return KATEGORI_RISIKO[0][0]
    return KATEGORI_RISIKO[-1][0]
