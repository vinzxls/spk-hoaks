"""Unit test core/risiko.py — agregasi, skala, kategori, ranking."""

from __future__ import annotations

import pytest

from core.risiko import (
    HasilRisiko,
    hitung_nilai_risiko,
    ranking_dari_hasil,
    skor_subkriteria_dari_jawaban,
)

# ── Fixture terverifikasi ───────────────────────────────────
# Bobot kriteria, bobot subkriteria, jawaban, dan hasil yang sudah
# diverifikasi silang terhadap referensi riset.
W = {"K1": 0.30, "K2": 0.25, "K3": 0.20, "K4": 0.15, "K5": 0.06, "K6": 0.04}
V_MATRIKS = [
    [0.50, 0.30, 0.20],
    [0.34, 0.33, 0.33],
    [1 / 3, 1 / 3, 1 / 3],
    [0.50, 0.25, 0.25],
    [0.60, 0.20, 0.20],
    [0.40, 0.40, 0.20],
]
A_MATRIKS = [
    [4, 5, 3],
    [3, 3, 4],
    [5, 4, 5],
    [2, 3, 2],
    [4, 4, 4],
    [1, 2, 1],
]


def _jawaban_dari(a: list[list[int]]) -> dict[str, int]:
    return {f"SK{k}.{s}": a[k - 1][s - 1] for k in range(1, 7) for s in range(1, 4)}


def _bobot_sub_dari(v: list[list[float]]) -> dict[str, float]:
    return {f"SK{k}.{s}": v[k - 1][s - 1] for k in range(1, 7) for s in range(1, 4)}


JAWABAN = _jawaban_dari(A_MATRIKS)
BOBOT_SUB = _bobot_sub_dari(V_MATRIKS)


def _jawaban_konstan(nilai: int) -> dict[str, int]:
    return {f"SK{k}.{s}": nilai for k in range(1, 7) for s in range(1, 4)}


# ── Fixture terverifikasi ───────────────────────────────────
def test_fixture_verifikasi_bobot_subtertentu():
    h = hitung_nilai_risiko(JAWABAN, W, BOBOT_SUB)
    assert h.skor_kriteria["K1"] == pytest.approx(4.10, abs=1e-6)
    assert h.skor_kriteria["K2"] == pytest.approx(3.33, abs=1e-6)
    assert h.skor_kriteria["K3"] == pytest.approx(4.666667, abs=1e-5)
    assert h.skor_kriteria["K4"] == pytest.approx(2.25, abs=1e-6)
    assert h.skor_kriteria["K5"] == pytest.approx(4.00, abs=1e-6)
    assert h.skor_kriteria["K6"] == pytest.approx(1.40, abs=1e-6)
    R = sum(W[k] * h.skor_kriteria[k] for k in W)
    assert R == pytest.approx(3.629333, abs=1e-5)
    assert h.nilai_risiko == pytest.approx(65.7333, abs=1e-2)
    assert h.kategori == "Sedang"


# ── Default: bobot subkriteria sama rata ───────────────────
def test_default_menghasilkan_rata_rata_sederhana():
    """Bobot None -> rata-rata sederhana per kriteria."""
    h = hitung_nilai_risiko(JAWABAN, W, None)
    assert h.skor_kriteria["K1"] == pytest.approx(4.0, abs=1e-6)
    assert h.skor_kriteria["K2"] == pytest.approx((3 + 3 + 4) / 3, abs=1e-6)
    assert h.skor_kriteria["K6"] == pytest.approx((1 + 2 + 1) / 3, abs=1e-6)


def test_skor_subkriteria_dari_jawaban():
    out = skor_subkriteria_dari_jawaban({"SK1.1": 4, "SK1.2": 5})
    assert out == {"SK1.1": 4.0, "SK1.2": 5.0}
    assert all(isinstance(v, float) for v in out.values())


# ── Ekstrem & kategori ──────────────────────────────────────
def test_semua_satu_menghasilkan_nol():
    h = hitung_nilai_risiko(_jawaban_konstan(1), W)
    assert h.nilai_risiko == pytest.approx(0.0, abs=1e-9)
    assert h.kategori == "Rendah"


def test_semua_lima_menghasilkan_seratus():
    h = hitung_nilai_risiko(_jawaban_konstan(5), W)
    assert h.nilai_risiko == pytest.approx(100.0, abs=1e-9)
    assert h.kategori == "Tinggi"


@pytest.mark.parametrize(
    "nilai,harapan",
    [
        (0, "Rendah"),
        (1, "Rendah"),
        (40, "Rendah"),
        (41, "Sedang"),
        (70, "Sedang"),
        (71, "Tinggi"),
        (100, "Tinggi"),
        (101, "Tinggi"),
    ],
)
def test_batas_kategori(nilai, harapan):
    import config
    assert config.kategori_dari_nilai(nilai) == harapan


# ── Invarian aljabar ────────────────────────────────────────
def test_dua_tahap_sama_dengan_bentuk_rata():
    """Agregasi 2 tahap harus sama dengan R = Σ w·v·A langsung."""
    h = hitung_nilai_risiko(JAWABAN, W, BOBOT_SUB)
    r_langsung = sum(
        W[f"K{k}"] * BOBOT_SUB[f"SK{k}.{s}"] * A_MATRIKS[k - 1][s - 1]
        for k in range(1, 7)
        for s in range(1, 4)
    )
    r_dua_tahap = sum(W[k] * h.skor_kriteria[k] for k in W)
    assert r_dua_tahap == pytest.approx(r_langsung, abs=1e-5)


def test_bobot_kriteria_sama_rata():
    """Dengan bobot kriteria sama rata, hasil adalah rata-rata-global."""
    w_rata = {f"K{k}": 1 / 6 for k in range(1, 7)}
    h = hitung_nilai_risiko(_jawaban_konstan(3), w_rata)
    assert h.nilai_risiko == pytest.approx(50.0, abs=1e-6)
    assert h.kategori == "Sedang"


# ── Validasi ────────────────────────────────────────────────
def test_tolak_jawaban_kosong():
    with pytest.raises(ValueError, match="tidak boleh kosong"):
        hitung_nilai_risiko({}, W)


def test_tolak_bobot_kriteria_kosong():
    with pytest.raises(ValueError, match="tidak boleh kosong"):
        hitung_nilai_risiko(JAWABAN, {})


def test_tolak_skor_di_luar_rentang():
    for buruk in (0, 6, -1, 2.5):
        j = dict(JAWABAN)
        j["SK1.1"] = buruk
        with pytest.raises(ValueError, match="tidak valid"):
            hitung_nilai_risiko(j, W)


def test_tolak_bobot_kriteria_tidak_jumlah_satu():
    with pytest.raises(ValueError, match="harus 1.0"):
        hitung_nilai_risiko(JAWABAN, {"K1": 0.5, "K2": 0.9})


def test_tolak_subkriteria_kurang():
    j = {k: v for k, v in JAWABAN.items() if k != "SK1.3"}
    with pytest.raises(ValueError, match="padahal kriteria lain memiliki"):
        hitung_nilai_risiko(j, W)


def test_tolak_kode_sub_tidak_dikenal():
    j = dict(JAWABAN)
    j["XX9.9"] = 3
    with pytest.raises(ValueError, match="tidak dikenali"):
        hitung_nilai_risiko(j, W)


def test_tolak_bobot_sub_kurang_lengkap():
    b = dict(BOBOT_SUB)
    del b["SK2.1"]
    with pytest.raises(ValueError, match="tidak lengkap"):
        hitung_nilai_risiko(JAWABAN, W, b)


def test_tolak_bobot_sub_tidak_jumlah_satu():
    b = dict(BOBOT_SUB)
    b["SK1.1"] = 0.9
    with pytest.raises(ValueError, match="harus 1.0"):
        hitung_nilai_risiko(JAWABAN, W, b)


# ── Ranking ─────────────────────────────────────────────────
def _h(nilai: float, kategori: str = "Sedang") -> HasilRisiko:
    return HasilRisiko(
        nilai_risiko=nilai,
        kategori=kategori,
        skor_kriteria={},
        skor_subkriteria={},
    )


def test_ranking_urutan_turun():
    daftar = [
        ("001", "Andi", _h(40.0)),
        ("002", "Budi", _h(80.0)),
        ("003", "Citra", _h(60.0)),
    ]
    r = ranking_dari_hasil(daftar)
    assert [x["nim"] for x in r] == ["002", "003", "001"]
    assert [x["peringkat"] for x in r] == [1, 2, 3]


def test_ranking_seri_competition_ranking():
    """Seri memakai peringkat sama, lalu lompat (1, 2, 2, 5)."""
    daftar = [
        ("001", "A", _h(90.0)),
        ("002", "B", _h(80.0)),
        ("003", "C", _h(80.0)),
        ("004", "D", _h(80.0)),
        ("005", "E", _h(50.0)),
    ]
    r = ranking_dari_hasil(daftar)
    assert [x["peringkat"] for x in r] == [1, 2, 2, 2, 5]


def test_ranking_kosong():
    assert ranking_dari_hasil([]) == []


def test_ranking_satu_item():
    r = ranking_dari_hasil([("001", "A", _h(50.0))])
    assert len(r) == 1
    assert r[0]["peringkat"] == 1


def test_ranking_mengandung_kunci_lengkap():
    r = ranking_dari_hasil([("001", "Andi", _h(75.0, "Tinggi"))])
    assert set(r[0]) == {"nim", "nama", "nilai_risiko", "kategori", "peringkat"}
    assert r[0]["kategori"] == "Tinggi"


# ── Pesan error berbahasa Indonesia ─────────────────────────
def test_pesan_error_bahasa_indonesia():
    with pytest.raises(ValueError) as exc:
        hitung_nilai_risiko({}, W)
    assert "tidak boleh kosong" in str(exc.value)
