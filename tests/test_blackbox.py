"""
Black box test: render every page, run the full questionnaire flow,
verify DB integration end-to-end.

Requires MySQL running on localhost:3306 with spk_hoaks database loaded.
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox
from typing import Any

import pytest

import ui.theme as tema
from core import layanan as L
from core.auth import UserSession, clear_session, set_session


# ── DB gate ──────────────────────────────────────────────────

def _db_available() -> bool:
    try:
        L.query_one("SELECT 1 AS ok")
        return True
    except Exception:
        return False


_SKIP = not _db_available()
_SKIP_REASON = "MySQL unreachable; black-box test skipped."


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="module")
def root(app):
    """Root Tk bersama dari conftest; test_blackbox tidak membuat root sendiri."""
    return app


@pytest.fixture
def sample_students():
    """Seed 3 test students + answers for 2 of them. Clean up after."""
    if _SKIP:
        pytest.skip(_SKIP_REASON)
    random.seed(7)
    codes = [r["kode_sub"] for r in L.ambil_semua_subkriteria()]
    ids: list[int] = []
    for i in range(1, 4):
        mid = L.simpan_mahasiswa({
            "nim": f"BBX{i:03d}", "nama": f"TestStudent {i}",
            "jenis_kelamin": "Laki-laki" if i % 2 else "Perempuan",
            "angkatan": "2025", "username": f"bbx{i}", "password": "rahasia",
        })
        ids.append(mid)
    for mid in ids[:2]:
        L.simpan_jawaban(mid, {s: random.randint(1, 5) for s in codes})
    L.hitung_semua_penilaian()
    yield ids
    for mid in ids:
        try:
            L.hapus_mahasiswa(mid)
        except Exception:
            pass
    L.execute("DELETE FROM hasil_penilaian")
    L.execute("DELETE FROM bobot_fahp")
    clear_session()


@pytest.fixture(autouse=True)
def _no_blocking_dialogs():
    """Suppress messagebox so tests don't block on OK buttons."""
    saved = {}
    for name in ("showinfo", "showwarning", "showerror", "askyesno"):
        saved[name] = getattr(messagebox, name)
        setattr(messagebox, name, lambda *a, **k: True)  # type: ignore[assignment]
    yield
    for name, fn in saved.items():
        setattr(messagebox, name, fn)


# ── Login tests ──────────────────────────────────────────────

@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_admin_login_success(root):
    from ui.login import LoginFrame
    results: list = []
    frame = LoginFrame(root, on_login=results.append)
    frame._role_var.set("admin")
    frame._role = "admin"  # type: ignore[assignment]
    frame._user.insert(0, "admin")
    frame._pass.insert(0, "admin123")
    frame._login()
    assert len(results) == 1
    assert results[0].role == "admin"
    frame.destroy()
    clear_session()


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_mahasiswa_login_success(root, sample_students):
    from ui.login import LoginFrame
    results: list = []
    frame = LoginFrame(root, on_login=results.append)
    frame._role_var.set("mahasiswa")
    frame._role = "mahasiswa"  # type: ignore[assignment]
    frame._user.insert(0, "bbx1")
    frame._pass.insert(0, "rahasia")
    frame._login()
    assert len(results) == 1
    assert results[0].role == "mahasiswa"
    assert results[0].nim == "BBX001"
    frame.destroy()
    clear_session()


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_wrong_password_shows_error(root):
    from ui.login import LoginFrame
    frame = LoginFrame(root, on_login=lambda _u: pytest.fail("should not login"))
    frame._user.insert(0, "admin")
    frame._pass.insert(0, "wrong-password")
    frame._login()
    assert "salah" in frame._err.cget("text").lower()
    frame.destroy()


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_role_guard_blocks_cross_access():
    set_session(UserSession(id_user=1, username="admin", nama="Admin",
                            role="admin"))
    with pytest.raises(PermissionError):
        from core.auth import require_role
        require_role("mahasiswa")
    clear_session()


# ── FAHP + scoring pipeline ──────────────────────────────────

@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_auto_fahp_weights_sum_to_one(root, sample_students):
    bobot = L.ambil_bobot_tersimpan()
    assert len(bobot) == 6
    assert abs(sum(bobot.values()) - 1.0) < 1e-6


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_scored_students_have_valid_categories(root, sample_students):
    for h in L.ambil_hasil_penilaian():
        assert 0.0 <= h["nilai_risiko"] <= 100.0
        assert h["kategori_risiko"] in ("Rendah", "Sedang", "Tinggi")
    ranking = L.ambil_ranking()
    nilai = [r["nilai_risiko"] for r in ranking]
    assert nilai == sorted(nilai, reverse=True)


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_unanswered_student_not_scored(root, sample_students):
    assert not L.sudah_menjawab(sample_students[2])
    scored_ids = [h["id_mahasiswa"] for h in L.ambil_hasil_penilaian()
                  if "id_mahasiswa" in h]
    assert sample_students[2] not in scored_ids


# ── Render all admin pages ───────────────────────────────────

def _build_admin_pages(root):
    import ui.admin.dashboard as pg_dash
    import ui.admin.hasil as pg_hasil
    import ui.admin.kriteria as pg_krit
    import ui.admin.kuesioner as pg_kuis
    import ui.admin.laporan as pg_lap
    import ui.admin.mahasiswa as pg_mhs
    import ui.admin.ranking as pg_rank

    noop = lambda _k: None
    pages: dict[str, Any] = {}
    for key, cls in (
        ("dashboard", pg_dash.DashboardPage),
        ("mahasiswa", pg_mhs.MahasiswaPage),
        ("kuesioner", pg_kuis.KuesionerPage),
        ("kriteria", pg_krit.KriteriaPage),
        ("hasil", pg_hasil.HasilPage),
        ("ranking", pg_rank.RankingPage),
        ("laporan", pg_lap.LaporanPage),
    ):
        holder = tk.Frame(root, bg=tema.BG)
        holder.pack()
        pages[key] = cls(holder, on_pilih=noop, on_logout=lambda: None)
        root.update_idletasks()
    return pages


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_all_admin_pages_render(root, sample_students):
    set_session(UserSession(id_user=1, username="admin", nama="Admin",
                            role="admin"))
    pages = _build_admin_pages(root)
    for key, page in pages.items():
        assert hasattr(page, "sidebar"), f"{key}: no sidebar"
        assert page.sidebar.winfo_exists()
        assert page.konten.winfo_exists()
        assert page.konten.winfo_children(), f"{key}: konten empty"
    for _, card in pages["dashboard"]._stat.items():
        assert card.value_label.cget("text") != "-"
    assert len(pages["mahasiswa"]._tabel.tree.get_children()) >= 2
    assert len(pages["hasil"]._tabel.tree.get_children()) >= 2
    assert len(pages["ranking"]._tabel.tree.get_children()) >= 2
    for p in pages.values():
        p.destroy()
    clear_session()


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_search_filters_mahasiswa(root, sample_students):
    import ui.admin.mahasiswa as pg_mhs
    holder = tk.Frame(root, bg=tema.BG)
    holder.pack()
    page = pg_mhs.MahasiswaPage(holder, on_pilih=lambda _: None,
                                on_logout=lambda: None)
    all_rows = len(page._tabel.tree.get_children())
    assert all_rows >= 3
    page._cari.var.set("TestStudent 1")
    page._cari._jalankan()
    filtered = len(page._tabel.tree.get_children())
    assert 0 < filtered < all_rows
    page.destroy()


# ── Mahasiswa dashboard + questionnaire flow ─────────────────

def _build_mhs_pages(root):
    import ui.mahasiswa.dashboard as pg_dash
    import ui.mahasiswa.kuesioner as pg_kuis
    noop = lambda _k: None
    holder = tk.Frame(root, bg=tema.BG)
    holder.pack()
    dash = pg_dash.MahasiswaDashboardPage(holder, on_pilih=noop,
                                         on_logout=lambda: None)
    kuis = pg_kuis.KuesionerPage(holder, on_pilih=noop,
                                 on_logout=lambda: None)
    return dash, kuis, holder


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_student_dashboard_greets_by_name(root, sample_students):
    mid = sample_students[2]
    set_session(UserSession(id_user=mid, username="bbx3", nama="TestStudent 3",
                            role="mahasiswa", id_mahasiswa=mid, nim="BBX003"))
    dash, _, holder = _build_mhs_pages(root)
    root.update_idletasks()
    labels = [c.cget("text") for c in dash.konten.winfo_children()
              if isinstance(c, (tk.Label, tk.Button))]
    assert any("TestStudent 3" in t for t in labels)
    assert any("BBX003" in t for t in labels)
    holder.destroy()
    clear_session()


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_full_questionnaire_flow(root, sample_students):
    mid = sample_students[2]
    set_session(UserSession(id_user=mid, username="bbx3", nama="TestStudent 3",
                            role="mahasiswa", id_mahasiswa=mid, nim="BBX003"))
    _, kuis, holder = _build_mhs_pages(root)
    root.update_idletasks()
    assert not L.sudah_menjawab(mid)
    n_sub = len(L.ambil_semua_subkriteria())
    assert len(kuis._vars) == n_sub, \
        f"expected {n_sub} questions, got {len(kuis._vars)}"
    for var in kuis._vars.values():
        var.set(random.randint(1, 5))
    kuis._kirim()
    root.update_idletasks()
    assert L.sudah_menjawab(mid)
    saved = L.ambil_jawaban_mahasiswa(mid)
    assert len(saved) == n_sub
    texts = [c.cget("text") for c in kuis.konten.winfo_children()
             if isinstance(c, (tk.Label, tk.Button))]
    assert any("Berhasil" in t or "Kirim" in t or "Dashboard" in t
               for t in texts), f"no confirmation: {texts[:5]}"
    L.hitung_semua_penilaian()
    scored_nims = [h["nim"] for h in L.ambil_hasil_penilaian()]
    assert "BBX003" in scored_nims
    holder.destroy()
    clear_session()


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_empty_answers_rejected(root, sample_students):
    mid = sample_students[2]
    set_session(UserSession(id_user=mid, username="bbx3", nama="TestStudent 3",
                            role="mahasiswa", id_mahasiswa=mid, nim="BBX003"))
    _, kuis, holder = _build_mhs_pages(root)
    kuis._kirim()
    assert not L.sudah_menjawab(mid)
    holder.destroy()
    clear_session()


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_already_answered_shows_done_screen(root, sample_students):
    mid = sample_students[0]
    set_session(UserSession(id_user=mid, username="bbx1", nama="TestStudent 1",
                            role="mahasiswa", id_mahasiswa=mid, nim="BBX001"))
    _, kuis, holder = _build_mhs_pages(root)
    root.update_idletasks()
    assert not kuis._vars, "form should not appear"
    texts = [c.cget("text") for c in kuis.konten.winfo_children()
             if isinstance(c, (tk.Label, tk.Button))]
    combined = " ".join(texts).lower()
    assert "dikirim" in combined or "sudah" in combined or "terima" in combined
    holder.destroy()
    clear_session()


# ── Laporan PDF export ───────────────────────────────────────

@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_pdf_export_valid(root, sample_students, tmp_path):
    import ui.admin.laporan as pg_lap
    holder = tk.Frame(root, bg=tema.BG)
    holder.pack()
    page = pg_lap.LaporanPage(holder, on_pilih=lambda _: None,
                              on_logout=lambda: None)
    out = tmp_path / "report.pdf"
    ranking = L.ambil_ranking()
    st = L.statistik_dashboard()
    page._buat_pdf(str(out), ranking, st)
    assert out.exists(), "PDF not created"
    assert out.stat().st_size > 800
    assert out.read_bytes()[:4] == b"%PDF"
    page.destroy()


# ── Cascade delete ───────────────────────────────────────────

@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_cascade_delete_cleans_answers(root, sample_students):
    mid = sample_students[1]
    L.hapus_mahasiswa(mid)
    leftover = L.query_one(
        "SELECT COUNT(*) AS n FROM jawaban_kuesioner WHERE id_mahasiswa=%s",
        (mid,))["n"]
    assert int(leftover) == 0
    assert L.ambil_mahasiswa(mid) is None


# ── Input validation ─────────────────────────────────────────

@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_incomplete_answers_rejected_by_service(root, sample_students):
    mid = sample_students[2]
    with pytest.raises(ValueError):
        L.simpan_jawaban(mid, {"SK1.1": 3})


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_invalid_likert_score_rejected(root, sample_students):
    mid = sample_students[2]
    subs = {r["kode_sub"] for r in L.ambil_semua_subkriteria()}
    answers = {s: 3 for s in subs}
    answers["SK1.1"] = 99
    with pytest.raises(ValueError):
        L.simpan_jawaban(mid, answers)


@pytest.mark.skipif(_SKIP, reason=_SKIP_REASON)
def test_export_excel_spss_format(root, sample_students, tmp_path):
    from openpyxl import load_workbook

    codes = [r["kode_sub"] for r in L.ambil_semua_subkriteria()]
    assert len(codes) == 30, f"expected 30 subkriteria, got {len(codes)}"

    path = str(tmp_path / "kuesioner_spss.xlsx")
    n = L.export_ke_excel(path)
    # Database bisa sudah berisi responden lain (data asli pengguna), jadi
    # jangan mengunci jumlah total. Yang penting kedua mahasiswa uji yang
    # jawabannya lengkap ikut terekspor, dan yang tidak lengkap tidak.
    nims = {str(r["nim"]) for r in L.ambil_semua_mahasiswa() if r["id_mahasiswa"] in sample_students[:2]}
    assert n >= 2, f"expected at least the 2 complete test respondents, got {n}"

    wb = load_workbook(path)
    ws = wb.active
    header_row = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
    assert len(header_row) == 32, f"expected 32 columns (NIM+Nama+30), got {len(header_row)}"
    assert header_row[:2] == ["NIM", "Nama"]
    assert "." not in str(header_row), "header contains dots — SPSS rejects variable names with dots"
    spss_codes = [c.replace(".", "_") for c in codes]
    for sc in spss_codes:
        assert sc in header_row, f"missing SPSS header: {sc}"

    baris_nim = {
        str(ws.cell(row=r, column=1).value)
        for r in range(2, ws.max_row + 1)
    }
    for nim in nims:
        assert nim in baris_nim, f"NIM {nim} yang jawabannya lengkap tidak ikut terekspor"
    nim_kosong = str(L.ambil_mahasiswa(sample_students[2])["nim"])
    assert nim_kosong not in baris_nim, "mahasiswa tanpa jawaban lengkap tidak boleh terekspor"

    for r in range(2, ws.max_row + 1):
        data_row = [ws.cell(row=r, column=c).value for c in range(3, 33)]
        for v in data_row:
            assert v in range(1, 6), f"likert score out of range: {v}"
