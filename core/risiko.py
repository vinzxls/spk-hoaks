"""Risiko scoring: jawaban kuesioner -> nilai risiko 0-100 + kategori.

Modul ini murni fungsi aljabar. Tidak ada UI, tidak ada SQL.

Alur
----
1. Kelompokkan jawaban subkriteria ke 6 kriteria (otomatis dari kode SKx.y).
2. Hitung rata-rata berbobot jawaban per kriteria (default bobot subkriteria sama rata).
3. Hitung skor 1-5 terbobot: ``R = Σ(w_k × skor_k)``.
4. Skalakan ONCE ke 0-100: ``nilai = (R - 1) / 4 × 100``.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import config


@dataclass(frozen=True)
class HasilRisiko:
    """Hasil perhitungan risiko untuk SATU mahasiswa."""

    nilai_risiko: float
    kategori: str  # "Rendah" | "Sedang" | "Tinggi"
    skor_kriteria: dict[str, float] = field(repr=False)
    """Skor per kriteria pada skala 1-5."""
    skor_subkriteria: dict[str, float] = field(repr=False)
    """Jawaban mentah per subkriteria (skala 1-5)."""


# ── Utilitas internal ────────────────────────────────────────

def _kriteria_dari_sub(kode_sub: str) -> str:
    """``"SK1.1"`` -> ``"K1"``, ``"SK12.3"`` -> ``"K12"``."""
    if not kode_sub.startswith("SK") or "." not in kode_sub:
        raise ValueError(
            f"Kode subkriteria tidak dikenali: {kode_sub!r}. "
            "Harus berformat 'SKx.y'."
        )
    num = kode_sub[2:].split(".")[0]
    if not num.isdigit():
        raise ValueError(f"Kode subkriteria tidak valid: {kode_sub!r}.")
    return f"K{num}"


# ── API publik ───────────────────────────────────────────────

def skor_subkriteria_dari_jawaban(
    jawaban: Mapping[str, int],
) -> dict[str, float]:
    """Konversi jawaban mentah ke dict kode_sub -> float."""
    return {k: float(v) for k, v in jawaban.items()}


def hitung_nilai_risiko(
    jawaban: Mapping[str, int],
    bobot_kriteria: Mapping[str, float],
    bobot_subkriteria: Mapping[str, float] | None = None,
) -> HasilRisiko:
    """Hitung nilai risiko seorang mahasiswa.

    Parameters
    ----------
    jawaban:
        Peta ``kode_sub`` (misal ``"SK1.1"``) -> jawaban Likert 1-5.
        Harus berisi satu entri per subkriteria, jumlah sama untuk
        semua kriteria.
    bobot_kriteria:
        Bobot Fuzzy AHP per kriteria (misal ``{"K1": 0.25, ...}``).
        Jumlah harus 1.0.
    bobot_subkriteria:
        Bobot lokal per subkriteria. ``None`` = sama rata di dalam
        tiap kriteria. Bila disediakan, jumlah bobot per kriteria
        harus 1.0.
    """
    # ── Validasi masukan ─────────────────────────────────────
    if not jawaban:
        raise ValueError("Jawaban kuesioner tidak boleh kosong.")

    for kode, skor in jawaban.items():
        if not isinstance(skor, int) or skor < config.LIKERT_MIN or skor > config.LIKERT_MAX:
            raise ValueError(
                f"Skor untuk {kode} tidak valid: {skor!r}. "
                f"Harus integer {config.LIKERT_MIN}-{config.LIKERT_MAX}."
            )

    if not bobot_kriteria:
        raise ValueError("Bobot kriteria tidak boleh kosong.")

    total_bobot = sum(float(v) for v in bobot_kriteria.values())
    if abs(total_bobot - 1.0) > 1e-6:
        raise ValueError(
            f"Jumlah bobot kriteria harus 1.0 (ditemukan {total_bobot:.6f})."
        )

    # ── Kelompokkan jawaban per kriteria ─────────────────────
    sub_by_kriteria: dict[str, list[str]] = {}
    for kode_sub in jawaban:
        kk = _kriteria_dari_sub(kode_sub)
        sub_by_kriteria.setdefault(kk, []).append(kode_sub)

    n_per_kriteria = {kk: len(sub_by_kriteria.get(kk, [])) for kk in bobot_kriteria}
    if len(set(n_per_kriteria.values())) > 1:
        fullest = max(n_per_kriteria.values())
        for kk, n in n_per_kriteria.items():
            if n != fullest:
                raise ValueError(
                    f"Kriteria {kk} memiliki {n} jawaban subkriteria, "
                    f"padahal kriteria lain memiliki {fullest}. "
                    f"Setiap kriteria harus punya jumlah subkriteria yang sama."
                )

    # ── Hitung skor per kriteria (rata-rata berbobot) ────────
    skor_kriteria: dict[str, float] = {}
    skor_subkriteria: dict[str, float] = {}

    for kk in bobot_kriteria:
        subs = sorted(sub_by_kriteria[kk])
        if bobot_subkriteria is not None:
            # Bobot spesifik per subkriteria.
            bobot_list = []
            for s in subs:
                if s not in bobot_subkriteria:
                    raise ValueError(
                        f"Bobot subkriteria untuk {kk} tidak lengkap: "
                        f"{s} tidak ditemukan."
                    )
                bobot_list.append(float(bobot_subkriteria[s]))
            total_local = sum(bobot_list)
            if abs(total_local - 1.0) > 1e-6:
                raise ValueError(
                    f"Jumlah bobot subkriteria untuk {kk} harus 1.0 "
                    f"(ditemukan {total_local:.6f})."
                )
            skor = sum(w * jawaban[s] for w, s in zip(bobot_list, subs)) / total_local
        else:
            # Default: bobot sama rata.
            skor = sum(jawaban[s] for s in subs) / len(subs)
        skor_kriteria[kk] = round(skor, 6)
        for s in subs:
            skor_subkriteria[s] = float(jawaban[s])

    # ── Rata-rata terbobot → skor 0-100 ─────────────────────
    R = sum(float(bobot_kriteria[kk]) * skor_kriteria[kk] for kk in bobot_kriteria)
    nilai_risiko = (R - 1.0) / 4.0 * 100.0
    nilai_risiko = round(nilai_risiko, 2)
    kategori = config.kategori_dari_nilai(nilai_risiko)

    return HasilRisiko(
        nilai_risiko=nilai_risiko,
        kategori=kategori,
        skor_kriteria=skor_kriteria,
        skor_subkriteria=skor_subkriteria,
    )


def ranking_dari_hasil(
    daftar: Sequence[tuple[str, str, HasilRisiko]],
) -> list[dict[str, typing.Any]]:
    """Buat ranking dari daftar hasil, diurutkan nilai risiko DESC.

    Parameters
    ----------
    daftar:
        List tupel ``(nim, nama, hasil_risiko)``.

    Returns
    -------
    List dict dengan kunci: nim, nama, nilai_risiko, kategori, peringkat.
    Ranking memakai *competition ranking*: jika ada seri, peringkat
    dibagi, dan peringkat berikutnya dilompati.
        Contoh: 1, 2, 2, 4, 5.
    """
    if not daftar:
        return []

    sorted_list = sorted(daftar, key=lambda x: x[2].nilai_risiko, reverse=True)
    result: list[dict[str, typing.Any]] = []
    rank = 1
    prev_skor = None
    posisi = 0

    for i, (nim, nama, h) in enumerate(sorted_list):
        if prev_skor is not None and h.nilai_risiko != prev_skor:
            rank = posisi + 1
        result.append({
            "nim": nim,
            "nama": nama,
            "nilai_risiko": h.nilai_risiko,
            "kategori": h.kategori,
            "peringkat": rank,
        })
        prev_skor = h.nilai_risiko
        posisi = i + 1

    return result
