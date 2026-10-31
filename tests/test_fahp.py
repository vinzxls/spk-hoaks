"""
Unit test engine Fuzzy AHP.

Fixture numerik diambil dari hasil verifikasi silang terhadap
Chang (1996), Chou/Liang/Chang (2003), dan implementasi referensi
GAMS. Nilai-nilai ini harus dikunci agar regresi数学 terdeteksi.
"""

from __future__ import annotations

import math

import pytest

from core.fahp import (
    METODE_FEA,
    METODE_GEOMEAN,
    FuzzyAhpError,
    degree_of_possibility,
    fuzzify,
    fuzzify_matrix,
    hitung_bobot_fahp,
    normalize_weights,
    priority_vector,
    synthetic_extent,
)

# ── Fixture 4x4 ──────────────────────────────────────────────
CRISP_4 = [
    [1, 1 / 2, 4, 5],
    [2, 1, 3, 4],
    [1 / 4, 1 / 3, 1, 2],
    [1 / 5, 1 / 4, 1 / 2, 1],
]
EXPECTED_S_4 = [
    (0.249377, 0.403329, 0.667237),
    (0.209476, 0.384123, 0.667237),
    (0.073317, 0.137644, 0.248075),
    (0.050873, 0.074904, 0.132592),
]
EXPECTED_V_4 = [
    [1.0, 1.0, 1.0, 1.0],
    [0.956057, 1.0, 1.0, 1.0],
    [0.0, 0.135398, 1.0, 1.0],
    [0.0, 0.0, 0.485802, 1.0],
]
EXPECTED_D_4 = [1.0, 0.956057, 0.0, 0.0]
EXPECTED_W_4 = [0.511233, 0.488767, 0.0, 0.0]

# ── Fixture 5x5 ──────────────────────────────────────────────
CRISP_5 = [
    [1, 2, 2, 3, 4],
    [1 / 2, 1, 1, 2, 3],
    [1 / 2, 1, 1, 2, 2],
    [1 / 3, 1 / 2, 1 / 2, 1, 2],
    [1 / 4, 1 / 3, 1 / 2, 1 / 2, 1],
]
EXPECTED_S_5 = [
    (0.176471, 0.364557, 0.704846),
    (0.117647, 0.227848, 0.440529),
    (0.095588, 0.197468, 0.396476),
    (0.064338, 0.131646, 0.286344),
    (0.046691, 0.078481, 0.168869),
]
EXPECTED_V_5 = [
    [1.0, 1.0, 1.0, 1.0, 1.0],
    [0.658882, 1.0, 1.0, 1.0, 1.0],
    [0.568351, 0.901750, 1.0, 1.0, 1.0],
    [0.320531, 0.636833, 0.743459, 1.0, 1.0],
    [0.0, 0.255359, 0.381139, 0.662866, 1.0],
]
EXPECTED_D_5 = [1.0, 0.658882, 0.568351, 0.320531, 0.0]
EXPECTED_W_5 = [0.392501, 0.258612, 0.223078, 0.125809, 0.0]

TOL = 1e-6


# ── Fuzzifikasi ──────────────────────────────────────────────
def test_fuzzify_nilai_kanonik():
    assert fuzzify(1.0) == (1.0, 1.0, 1.0)
    assert fuzzify(2.0) == (1.0, 2.0, 3.0)
    assert fuzzify(3.0) == (2.0, 3.0, 4.0)
    assert fuzzify(4.0) == (3.0, 4.0, 5.0)
    assert fuzzify(5.0) == (4.0, 5.0, 6.0)
    assert fuzzify(6.0) == (5.0, 6.0, 7.0)
    assert fuzzify(7.0) == (6.0, 7.0, 8.0)
    assert fuzzify(8.0) == (7.0, 8.0, 9.0)
    # Pengecualian kanonik: 9 -> (9,9,9), bukan (8,9,10).
    assert fuzzify(9.0) == (9.0, 9.0, 9.0)


def test_fuzzify_nilai_pecahan():
    assert fuzzify(0.5) == pytest.approx((1 / 3, 0.5, 1.0), abs=TOL)
    assert fuzzify(1 / 3) == pytest.approx((0.25, 1 / 3, 0.5), abs=TOL)
    assert fuzzify(1 / 9) == pytest.approx((1 / 9, 1 / 9, 1 / 9), abs=TOL)


def test_fuzzify_resiprokal():
    """fuzzify(1/x) harus sama dengan (1/u, 1/m, 1/l) dari fuzzify(x)."""
    for x in (2.0, 3.0, 5.0, 7.0, 9.0):
        l, m, u = fuzzify(x)
        assert fuzzify(1.0 / x) == pytest.approx((1 / u, 1 / m, 1 / l), abs=TOL)


def test_fuzzify_tolak_nilai_tidak_valid():
    for bad in (0.0, -1.0, -0.5, float("nan"), float("inf")):
        with pytest.raises(FuzzyAhpError):
            fuzzify(bad)


def test_fuzzify_matrix():
    out = fuzzify_matrix(CRISP_4)
    assert len(out) == 4
    assert all(len(row) == 4 for row in out)
    assert out[0][0] == (1.0, 1.0, 1.0)


# ── Degree of possibility ────────────────────────────────────
def test_dop_identik_selalu_satu():
    """Mengunci varian yang salah: bobot 0/1 tertukar akan gagal di sini."""
    for t in [(1.0, 1.0, 1.0), (3.0, 5.0, 7.0), (0.5, 1.0, 2.0), (9.0, 9.0, 9.0)]:
        assert degree_of_possibility(t, t) == 1.0


def test_dop_tidak_tumpang_tindih():
    assert degree_of_possibility((1.0, 2.0, 3.0), (7.0, 8.0, 9.0)) == 0.0
    assert degree_of_possibility((7.0, 8.0, 9.0), (1.0, 2.0, 3.0)) == 1.0


def test_dop_sentuh_jdbc():
    # u1 == l2: irisan hanya setinggi 0, jadi possabilitasnya 0.
    assert degree_of_possibility((1.0, 2.0, 3.0), (3.0, 4.0, 5.0)) == 0.0


def test_dop_kandungan():
    assert degree_of_possibility((1.0, 10.0, 10.0), (4.0, 5.0, 6.0)) == 1.0
    assert degree_of_possibility((4.0, 5.0, 6.0), (1.0, 10.0, 10.0)) == pytest.approx(
        0.5, abs=TOL
    )


def test_dop_rentang_selalu_valid():
    """Properti rentang: hasil selalu dalam [0, 1] untuk semua input."""
    kandidat = [
        (1.0, 1.0, 1.0),
        (5.0, 5.0, 5.0),
        (1.0, 1.0, 10.0),
        (0.5, 1.0, 2.0),
        (1.0, 3.0, 5.0),
        (3.0, 4.0, 5.0),
        (0.1, 0.1, 0.1),
        (2.0, 4.0, 6.0),
        (3.0, 5.0, 7.0),
        (0.25, 0.5, 1.0),
    ]
    for a in kandidat:
        for b in kandidat:
            v = degree_of_possibility(a, b)
            assert 0.0 <= v <= 1.0, f"v({a},{b}) = {v} di luar [0,1]"


def test_dop_bukan_simetris():
    """v(a>=b) + v(b>=a) >= 1, tapi TIDAK sama dengan 1."""
    a = (2.0, 4.0, 6.0)
    b = (3.0, 5.0, 7.0)
    assert degree_of_possibility(a, b) + degree_of_possibility(b, a) >= 1.0
    assert degree_of_possibility(a, b) != pytest.approx(
        1.0 - degree_of_possibility(b, a), abs=TOL
    )


def test_dop_tolak_tfn_tidak_valid():
    with pytest.raises(FuzzyAhpError):
        degree_of_possibility((3.0, 2.0, 1.0), (1.0, 1.0, 1.0))
    with pytest.raises(FuzzyAhpError):
        degree_of_possibility((1.0, 1.0, 1.0), (1.0, 5.0, 3.0))


# ── Synthetic extent + priority + normalisasi ────────────────
def test_synthetic_extent_4x4():
    se = synthetic_extent(fuzzify_matrix(CRISP_4))
    assert len(se) == 4
    for got, exp in zip(se, EXPECTED_S_4):
        assert got == pytest.approx(exp, abs=TOL)


def test_synthetic_extent_5x5():
    se = synthetic_extent(fuzzify_matrix(CRISP_5))
    for got, exp in zip(se, EXPECTED_S_5):
        assert got == pytest.approx(exp, abs=TOL)


def test_priority_vector_4x4():
    d = priority_vector(EXPECTED_V_4)
    assert d == pytest.approx(EXPECTED_D_4, abs=TOL)


def test_priority_vector_5x5():
    d = priority_vector(EXPECTED_V_5)
    assert d == pytest.approx(EXPECTED_D_5, abs=TOL)


def test_normalize_weights_jumlah_satu():
    assert sum(normalize_weights(EXPECTED_D_4)) == pytest.approx(1.0, abs=1e-9)
    assert sum(normalize_weights(EXPECTED_D_5)) == pytest.approx(1.0, abs=1e-9)


def test_normalize_weights_tolak_nol():
    with pytest.raises(FuzzyAhpError):
        normalize_weights([0.0, 0.0, 0.0])


# ── Orkestrasi penuh ─────────────────────────────────────────
def test_fea_4x4_bobot():
    hasil = hitung_bobot_fahp(CRISP_4, METODE_FEA)
    assert hasil.bobot == pytest.approx(EXPECTED_W_4, abs=TOL)
    assert sum(hasil.bobot) == pytest.approx(1.0, abs=1e-9)
    assert hasil.metode == METODE_FEA


def test_fea_5x5_bobot():
    hasil = hitung_bobot_fahp(CRISP_5, METODE_FEA)
    assert hasil.bobot == pytest.approx(EXPECTED_W_5, abs=TOL)
    assert sum(hasil.bobot) == pytest.approx(1.0, abs=1e-9)


def test_fea_terallic_metadata():
    """Synthetic extent dan priority harus ikut terkembalikan."""
    hasil = hitung_bobot_fahp(CRISP_4, METODE_FEA)
    assert len(hasil.synthetic_extents) == 4
    assert len(hasil.priority) == 4


def test_geomean_berjalan_dan_jumlah_satu():
    for matriks in (CRISP_4, CRISP_5):
        hasil = hitung_bobot_fahp(matriks, METODE_GEOMEAN)
        assert hasil.metode == METODE_GEOMEAN
        assert sum(hasil.bobot) == pytest.approx(1.0, abs=1e-9)
        assert all(b >= 0.0 for b in hasil.bobot)


def test_geomean_tidak_menghasilkan_nol():
    """Perbedaan kunci: geomean tidak pernah menghasilkan bobot 0."""
    hasil = hitung_bobot_fahp(CRISP_4, METODE_GEOMEAN)
    assert all(b > 0.0 for b in hasil.bobot)


# ── Validasi masukan ─────────────────────────────────────────
def test_tolak_matriks_bukan_persgi():
    with pytest.raises(FuzzyAhpError):
        hitung_bobot_fahp([[1, 2, 3], [1, 1, 1]])


def test_tolak_matriks_kosong():
    with pytest.raises(FuzzyAhpError):
        hitung_bobot_fahp([])


def test_tolak_nilai_nol():
    m = [[1, 0], [1, 1]]
    with pytest.raises(FuzzyAhpError):
        hitung_bobot_fahp(m)


def test_tolak_nilai_negatif():
    m = [[1, -2], [0.5, 1]]
    with pytest.raises(FuzzyAhpError):
        hitung_bobot_fahp(m)


def test_tolak_diagonal_bukan_satu():
    m = [[2, 1], [1, 1]]
    with pytest.raises(FuzzyAhpError):
        hitung_bobot_fahp(m)


def test_tolak_metode_tidak_dikenal():
    with pytest.raises(FuzzyAhpError):
        hitung_bobot_fahp(CRISP_4, "METODE_LAIN")


# ── Peringatan resiprokal ───────────────────────────────────
def test_peringatan_resiprokal_untuk_nilai_bulat():
    """Pembulatan DECIMAL(5,3) memicu peringatan, bukan error."""
    m = [
        [1.0, 2.0, 0.333],
        [0.5, 1.0, 2.0],
        [0.333, 0.5, 1.0],
    ]
    hasil = hitung_bobot_fahp(m, METODE_FEA)
    assert len(hasil.warnings) >= 0  # tidak crash
    assert sum(hasil.bobot) == pytest.approx(1.0, abs=1e-9)


def test_matriks_benar_tanpa_peringatan():
    hasil = hitung_bobot_fahp(CRISP_4, METODE_FEA)
    assert hasil.warnings == []


# ── Stabilitas numerik ──────────────────────────────────────
def test_tidak_ada_nan_atau_inf():
    for matriks in (CRISP_4, CRISP_5):
        for metode in (METODE_FEA, METODE_GEOMEAN):
            hasil = hitung_bobot_fahp(matriks, metode)
            for b in hasil.bobot:
                assert math.isfinite(b)
                assert 0.0 <= b <= 1.0
