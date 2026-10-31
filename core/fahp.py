"""
Fuzzy AHP engine - Chang's Extent Analysis Method (FEA).

Metode ini menghasilkan bobot prioritas dari matriks perbandingan
berpasangan antar kriteria. Perhitungan dilakukan secara internal di
backend; Admin tidak mengoperasikan menu Fuzzy AHP.

Tahapan (sesuai specification requirement):
    1. Fuzzifikasi ke TFN (Triangular Fuzzy Number)
    2. Perhitungan synthetic extent
    3. Degree of possibility
    4. Nilai vektor (priority vector)
    5. Normalisasi -> bobot prioritas akhir

Properti struktural FEA
----------------------
Kriteria dengan prioritas terendah sering memperoleh bobot tepat 0.0,
karena ``upper bound``-nya berada di bawah ``lower bound`` kriteria
tertinggi. Ini perilaku kanonik, bukan bug. Jangan "memperbaiki" dengan
epsilon.

Metode alternatif ``GEOMEAN`` (Buckley / van Laarhoven) disertakan
sebagai pembanding, untuk kasus skripsi klien memakai varian tersebut.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

#: TFN = (l, m, u) dengan l <= m <= u
Tfn = tuple[float, float, float]

METODE_FEA = "FEA"
METODE_GEOMEAN = "GEOMEAN"
_METODE_VALID = (METODE_FEA, METODE_GEOMEAN)


class FuzzyAhpError(ValueError):
    """Kesalahan perhitungan Fuzzy AHP. Pesan dalam bahasa Indonesia."""


@dataclass(frozen=True)
class FahpResult:
    """Hasil perhitungan Fuzzy AHP."""

    bobot: list[float]
    """Bobot crisp akhir; jumlah selalu 1.0."""

    synthetic_extents: list[Tfn]
    """Synthetic extent S_i (kosong untuk metode GEOMEAN)."""

    priority: list[float]
    """Nilai vektor d'[i] sebelum normalisasi."""

    metode: str
    warnings: list[str] = field(default_factory=list)
    """Peringatan non-fatal, mis. matriks kurang resiprokal."""


# ── Tahap 1: Fuzzifikasi ──────────────────────────────────────
def fuzzify(x: float) -> Tfn:
    """Ubah nilai crisp skala Saaty menjadi TFN.

    Bentuk tertutup (closed form)::

        x >= 1 :  l = x - 1,  m = x,  u = x + 1

    dengan dua pengecualian kanonik dari tabel linguistik Chang (1996):
    ``1 -> (1, 1, 1)`` dan ``9 -> (9, 9, 9)``.

    Untuk ``x < 1`` digunakan aturan resiprokal
    ``TFN(1/x) = (1/u, 1/m, 1/l)``.
    """
    if not math.isfinite(x) or x <= 0.0:
        raise FuzzyAhpError("Nilai perbandingan harus angka finite dan positif.")
    if x == 1.0:
        return (1.0, 1.0, 1.0)
    if x > 1.0:
        if x == 9.0:
            # Kanonik: Chang (1996) memetakan 9 ke (9,9,9), bukan (8,9,10).
            return (9.0, 9.0, 9.0)
        return (x - 1.0, x, x + 1.0)
    inv = 1.0 / x
    if inv == 1.0:
        return (1.0, 1.0, 1.0)
    if inv == 9.0:
        return (1.0 / 9.0, 1.0 / 9.0, 1.0 / 9.0)
    l0, m0, u0 = (inv - 1.0, inv, inv + 1.0)
    return (1.0 / u0, 1.0 / m0, 1.0 / l0)


def fuzzify_matrix(m: Sequence[Sequence[float]]) -> list[list[Tfn]]:
    """Fuzzifikasi seluruh matriks crisp menjadi TFN."""
    return [[fuzzify(v) for v in baris] for baris in m]


# ── Tahap 2: Synthetic extent ─────────────────────────────────
def synthetic_extent(fuzzy: Sequence[Sequence[Tfn]]) -> list[Tfn]:
    """Hitung synthetic extent S_i untuk setiap baris.

    Perhatikan silang l/u - ini kesalahan transkripsi paling umum::

        S_l[i] = (sum_j l_ij) / total_u
        S_m[i] = (sum_j m_ij) / total_m
        S_u[i] = (sum_j u_ij) / total_l
    """
    n = len(fuzzy)
    if n == 0:
        return []
    total_l = sum(fuzzy[i][j][0] for i in range(n) for j in range(n))
    total_m = sum(fuzzy[i][j][1] for i in range(n) for j in range(n))
    total_u = sum(fuzzy[i][j][2] for i in range(n) for j in range(n))
    if total_l <= 0.0 or total_m <= 0.0 or total_u <= 0.0:
        raise FuzzyAhpError("Total synthetic extent tidak valid.")
    result: list[Tfn] = []
    for i in range(n):
        row_l = sum(fuzzy[i][j][0] for j in range(n))
        row_m = sum(fuzzy[i][j][1] for j in range(n))
        row_u = sum(fuzzy[i][j][2] for j in range(n))
        result.append((row_l / total_u, row_m / total_m, row_u / total_l))
    return result


# ── Tahap 3: Degree of possibility ───────────────────────────
def degree_of_possibility(a: Tfn, b: Tfn) -> float:
    """Degree of possibility ``v(a >= b)``; selalu dalam rentang [0, 1].

    Bentuk tanda-aman (setara aljabaris dengan bentuk terpublikasi)::

        v(a >= b) = 1.0                                         jika a.m >= b.m
        v(a >= b) = 0.0                                         jika b.l >= a.u
        v(a >= b) = (a.u - b.l) / ((a.u - a.m) + (b.m - b.l))   selainnya

    Peringatan: varian dengan cabang 0/1 yang tertukar banyak beredar
    di publikasi dan SALAH - varian itu mengembalikan 0 untuk TFN
    identik serta membalik urutan kriteria.
    """
    if not (a[0] <= a[1] <= a[2]):
        raise FuzzyAhpError("TFN A tidak valid: harus memenuhi l <= m <= u.")
    if not (b[0] <= b[1] <= b[2]):
        raise FuzzyAhpError("TFN B tidak valid: harus memenuhi l <= m <= u.")
    if a[1] >= b[1]:
        return 1.0
    if b[0] >= a[2]:
        return 0.0
    denominator = (a[2] - a[1]) + (b[1] - b[0])
    if denominator <= 0.0:
        return 0.0
    nilai = (a[2] - b[0]) / denominator
    return min(1.0, max(0.0, nilai))


# ── Tahap 4: Nilai vektor (priority vector) ───────────────────
def priority_vector(possibility: Sequence[Sequence[float]]) -> list[float]:
    """``d'[i] = min_{j != i} V[i][j]``. Diagonal dikecualikan."""
    n = len(possibility)
    if n == 0:
        return []
    result: list[float] = []
    for i in range(n):
        if n == 1:
            result.append(1.0)
            continue
        result.append(min(possibility[i][j] for j in range(n) if j != i))
    return result


# ── Tahap 5: Normalisasi ──────────────────────────────────────
def normalize_weights(d: Sequence[float]) -> list[float]:
    """Normalisasi bobot priority vector sehingga berjumlah 1.0."""
    total = sum(d)
    if total <= 0.0:
        raise FuzzyAhpError(
            "Bobot priority vector bernilai nol total; periksa matriks perbandingan."
        )
    return [v / total for v in d]


# ── Metode alternatif: geometric mean ──────────────────────────
def _geomean_weights(fuzzy: Sequence[Sequence[Tfn]]) -> list[float]:
    n = len(fuzzy)
    geo: list[Tfn] = []
    for i in range(n):
        pl = pm = pu = 1.0
        for j in range(n):
            l, m, u = fuzzy[i][j]
            pl *= l
            pm *= m
            pu *= u
        akar = 1.0 / n
        geo.append((pl**akar, pm**akar, pu**akar))
    tl = sum(g[0] for g in geo)
    tm = sum(g[1] for g in geo)
    tu = sum(g[2] for g in geo)
    if tl <= 0.0 or tm <= 0.0 or tu <= 0.0:
        raise FuzzyAhpError("Total geometric mean tidak valid.")
    # Tetap memakai silang l/u yang sama seperti FEA.
    fuzzy_w = [(g[0] / tu + g[1] / tm + g[2] / tl) / 3.0 for g in geo]
    return normalize_weights(fuzzy_w)


# ── Orkestrasi ────────────────────────────────────────────────
def _validasi_matriks(matriks: Sequence[Sequence[float]]) -> int:
    n = len(matriks)
    if n == 0:
        raise FuzzyAhpError("Matriks perbandingan tidak boleh kosong.")
    if any(len(row) != n for row in matriks):
        raise FuzzyAhpError("Matriks perbandingan harus berbentuk persegi (nxn).")
    for row in matriks:
        for v in row:
            if not math.isfinite(v) or v <= 0.0:
                raise FuzzyAhpError(
                    "Matriks perbandingan hanya boleh berisi angka finite, bukan nol, dan positif."
                )
    for i in range(n):
        if abs(matriks[i][i] - 1.0) > 1e-6:
            raise FuzzyAhpError("Diagonal matriks perbandingan harus bernilai 1.")
    return n


def _peringatan_resiprokal(matriks: Sequence[Sequence[float]], n: int) -> list[str]:
    """Peringatan, bukan error: penyimpanan DECIMAL(5,3) membuat
    resiprokal seperti 1/3 hanya akurat sampai 3 desimal."""
    warnings: list[str] = []
    for i in range(n):
        for j in range(i + 1, n):
            produk = matriks[i][j] * matriks[j][i]
            if abs(produk - 1.0) > 0.01:
                warnings.append(
                    f"Matriks kurang resiprokal pada posisi ({i + 1},{j + 1}): "
                    f"hasil kali = {produk:.4f} (harusnya 1.0)."
                )
    return warnings


def hitung_bobot_fahp(
    matriks: Sequence[Sequence[float]],
    metode: str = METODE_FEA,
) -> FahpResult:
    """Hitung bobot prioritas dari matriks perbandingan berpasangan.

    Parameters
    ----------
    matriks:
        Matriks crisp ``n x n``. Diagonal harus bernilai 1.0.
    metode:
        ``"FEA"`` (default) untuk Chang's Extent Analysis, atau
        ``"GEOMEAN"`` untuk Buckley / van Laarhoven.
    """
    if metode not in _METODE_VALID:
        raise FuzzyAhpError(
            f"Metode Fuzzy AHP tidak dikenal: {metode!r}. "
            f"Gunakan 'FEA' atau 'GEOMEAN'."
        )
    n = _validasi_matriks(matriks)
    warnings = _peringatan_resiprokal(matriks, n)
    fuzzy = fuzzify_matrix(matriks)

    if metode == METODE_GEOMEAN:
        return FahpResult(
            bobot=_geomean_weights(fuzzy),
            synthetic_extents=[],
            priority=[],
            metode=METODE_GEOMEAN,
            warnings=warnings,
        )

    se = synthetic_extent(fuzzy)
    possibility = [
        [degree_of_possibility(se[i], se[j]) for j in range(n)] for i in range(n)
    ]
    for i in range(n):
        possibility[i][i] = 1.0
    d = priority_vector(possibility)
    return FahpResult(
        bobot=normalize_weights(d),
        synthetic_extents=se,
        priority=d,
        metode=METODE_FEA,
        warnings=warnings,
    )
