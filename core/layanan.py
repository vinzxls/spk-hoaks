"""
Service layer: semua query DB + orkestrasi pipeline FAHP.

Halaman UI tidak pernah menulis SQL langsung; semuanya lewat modul ini.
Fuzzy AHP dijalankan otomatis di sini sesuai requirement — Admin tidak
mengoperasikan menu perhitungan.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Mapping, Sequence

import config
from core import risiko as m_risiko
from core.fahp import METODE_FEA, hitung_bobot_fahp
from db.connection import execute, execute_many, query_all, query_one

logger = logging.getLogger(__name__)

METODE_FAHP = METODE_FEA


# ── Helper konversi ─────────────────────────────────────────
def _f(v: Any) -> float:
    """Ubah Decimal/None/int menjadi float yang aman."""
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


# ════════════════════════════════════════════════════════════
# MAHASISWA
# ════════════════════════════════════════════════════════════
def ambil_semua_mahasiswa(cari: str = "") -> list[dict[str, Any]]:
    sql = (
        "SELECT id_mahasiswa, nim, nama, jenis_kelamin, angkatan, username "
        "FROM mahasiswa"
    )
    params: list[Any] = []
    if cari:
        sql += " WHERE nama LIKE %s OR nim LIKE %s"
        params = [f"%{cari}%", f"%{cari}%"]
    sql += " ORDER BY nama"
    return query_all(sql, params)


def ambil_mahasiswa(id_mahasiswa: int) -> dict[str, Any] | None:
    return query_one(
        "SELECT id_mahasiswa, nim, nama, jenis_kelamin, angkatan, username "
        "FROM mahasiswa WHERE id_mahasiswa = %s",
        (id_mahasiswa,),
    )


def simpan_mahasiswa(data: Mapping[str, Any], id_mahasiswa: int | None = None
                     ) -> int:
    """Insert (id None) atau update. Password di-hash bila diberikan."""
    from core.auth import hash_password

    if id_mahasiswa is None:
        pw = hash_password(str(data["username"]), str(data.get("password") or "123456"))
        return execute(
            "INSERT INTO mahasiswa (nim, nama, jenis_kelamin, angkatan, "
            "username, password) VALUES (%s,%s,%s,%s,%s,%s)",
            (data["nim"], data["nama"], data["jenis_kelamin"],
             data["angkatan"], data["username"], pw),
        )
    lama = query_one(
        "SELECT username FROM mahasiswa WHERE id_mahasiswa=%s",
        (id_mahasiswa,),
    )
    # Password di-hash sebagai SHA256(username + password). Bila username
    # berubah, hash lama otomatis tidak cocok lagi -> akun terkunci dan
    # mahasiswa tidak bisa login. Karena plaintext tidak tersimpan, satu-
    # satunya jalan adalah memakai password baru. Validasi SEBELUM menulis
    # apa pun supaya data tidak setengah berubah saat error dilempar.
    if (
        not data.get("password")
        and lama is not None
        and str(lama["username"]) != str(data["username"])
    ):
        raise ValueError(
            "Username diubah, jadi password harus diisi ulang. "
            f"Password lama tidak bisa dipakai untuk username "
            f"'{data['username']}'."
        )
    execute(
        "UPDATE mahasiswa SET nim=%s, nama=%s, jenis_kelamin=%s, "
        "angkatan=%s, username=%s WHERE id_mahasiswa=%s",
        (data["nim"], data["nama"], data["jenis_kelamin"],
         data["angkatan"], data["username"], id_mahasiswa),
    )
    if data.get("password"):
        execute(
            "UPDATE mahasiswa SET password=%s WHERE id_mahasiswa=%s",
            (hash_password(str(data["username"]), str(data["password"])),
             id_mahasiswa),
        )
    return id_mahasiswa


def hapus_mahasiswa(id_mahasiswa: int) -> None:
    execute("DELETE FROM mahasiswa WHERE id_mahasiswa = %s", (id_mahasiswa,))


# ════════════════════════════════════════════════════════════
# KRITERIA & SUBKRITERIA
# ════════════════════════════════════════════════════════════
def ambil_kriteria_dengan_sub() -> list[dict[str, Any]]:
    """Kriteria beserta subkriteria-nya, urut kode."""
    kriteria = query_all(
        "SELECT id_kriteria, kode_kriteria, nama_kriteria FROM kriteria "
        "ORDER BY kode_kriteria"
    )
    for k in kriteria:
        k["subkriteria"] = query_all(
            "SELECT id_subkriteria, kode_sub, nama_subkriteria "
            "FROM subkriteria WHERE id_kriteria = %s ORDER BY kode_sub",
            (k["id_kriteria"],),
        )
    return kriteria


def simpan_kriteria(nama: str, id_kriteria: int | None = None) -> int:
    if id_kriteria is None:
        nxt = query_one(
            "SELECT COALESCE(MAX(CAST(SUBSTRING(kode_kriteria,2) AS UNSIGNED)),0) AS n "
            "FROM kriteria"
        )
        kode = f"K{int(nxt['n']) + 1}"
        return execute(
            "INSERT INTO kriteria (kode_kriteria, nama_kriteria) VALUES (%s,%s)",
            (kode, nama),
        )
    execute(
        "UPDATE kriteria SET nama_kriteria=%s WHERE id_kriteria=%s",
        (nama, id_kriteria),
    )
    return id_kriteria


def simpan_subkriteria(
    id_kriteria: int, nama: str, id_subkriteria: int | None = None
) -> int:
    if id_subkriteria is None:
        jml = query_one(
            "SELECT COUNT(*) AS n FROM subkriteria WHERE id_kriteria=%s",
            (id_kriteria,),
        )["n"]
        kode_k = query_one(
            "SELECT kode_kriteria FROM kriteria WHERE id_kriteria=%s",
            (id_kriteria,),
        )["kode_kriteria"]
        kode = f"{kode_k}.{int(jml) + 1}"
        return execute(
            "INSERT INTO subkriteria (id_kriteria, kode_sub, nama_subkriteria) "
            "VALUES (%s,%s,%s)",
            (id_kriteria, kode, nama),
        )
    execute(
        "UPDATE subkriteria SET nama_subkriteria=%s WHERE id_subkriteria=%s",
        (nama, id_subkriteria),
    )
    return id_subkriteria


def hapus_kriteria(id_kriteria: int) -> None:
    """Cascade menghapus subkriteria (FK ON DELETE CASCADE)."""
    execute("DELETE FROM kriteria WHERE id_kriteria=%s", (id_kriteria,))


def hapus_subkriteria(id_subkriteria: int) -> None:
    execute("DELETE FROM subkriteria WHERE id_subkriteria=%s", (id_subkriteria,))


def ambil_semua_subkriteria() -> list[dict[str, Any]]:
    return query_all(
        "SELECT s.id_subkriteria, s.kode_sub, s.nama_subkriteria, "
        "k.kode_kriteria, k.nama_kriteria "
        "FROM subkriteria s JOIN kriteria k ON k.id_kriteria=s.id_kriteria "
        "ORDER BY s.kode_sub"
    )


# ════════════════════════════════════════════════════════════
# MATRIKS + FAHP (berjalan otomatis)
# ════════════════════════════════════════════════════════════
def ambil_matriks_pairwise() -> tuple[list[str], list[list[float]]]:
    """Baca matriks perbandingan dari DB. Returns (kode_kriteria, matriks)."""
    kode = [r["kode_kriteria"] for r in query_all(
        "SELECT kode_kriteria FROM kriteria ORDER BY kode_kriteria"
    )]
    if not kode:
        return [], []
    baris = query_all(
        "SELECT kode_baris, kode_kolom, CAST(nilai AS CHAR) AS nilai "
        "FROM matriks_perbandingan"
    )
    peta = {(b["kode_baris"], b["kode_kolom"]): _f(b["nilai"]) for b in baris}
    n = len(kode)
    matriks: list[list[float]] = []
    for i in range(n):
        baris_m: list[float] = []
        for j in range(n):
            if i == j:
                baris_m.append(1.0)
            else:
                baris_m.append(peta.get((kode[i], kode[j]), 1.0))
        matriks.append(baris_m)
    return kode, matriks


def jalankan_fahp() -> dict[str, float]:
    """Hitung bobot Fuzzy AHP dari matriks, simpan ke bobot_fahp.

    Dipanggil otomatis; tidak ada menu UI untuk ini.
    """
    kode, matriks = ambil_matriks_pairwise()
    if not kode or not matriks:
        return {}
    hasil = hitung_bobot_fahp(matriks, METODE_FAHP)
    execute("DELETE FROM bobot_fahp")
    id_kriteria = {
        r["kode_kriteria"]: r["id_kriteria"]
        for r in query_all("SELECT id_kriteria, kode_kriteria FROM kriteria")
    }
    execute_many(
        "INSERT INTO bobot_fahp (id_kriteria, bobot_crisp) VALUES (%s,%s)",
        [(id_kriteria[k], round(b, 6)) for k, b in zip(kode, hasil.bobot)
         if k in id_kriteria],
    )
    if hasil.warnings:
        logger.warning("Peringatan FAHP: %s", "; ".join(hasil.warnings))
    return dict(zip(kode, hasil.bobot))


def ambil_bobot_tersimpan() -> dict[str, float]:
    """Bobot yang tersimpan; jalankan FAHP bila tabel kosong."""
    rows = query_all(
        "SELECT k.kode_kriteria, CAST(b.bobot_crisp AS CHAR) AS bobot "
        "FROM bobot_fahp b JOIN kriteria k ON k.id_kriteria=b.id_kriteria"
    )
    if rows:
        return {r["kode_kriteria"]: _f(r["bobot"]) for r in rows}
    return jalankan_fahp()


# ════════════════════════════════════════════════════════════
# KUESIONER MAHASISWA
# ════════════════════════════════════════════════════════════
def sudah_menjawab(id_mahasiswa: int) -> bool:
    row = query_one(
        "SELECT COUNT(DISTINCT id_subkriteria) AS n FROM jawaban_kuesioner "
        "WHERE id_mahasiswa=%s",
        (id_mahasiswa,),
    )
    total = query_one("SELECT COUNT(*) AS n FROM subkriteria")["n"]
    return int(row["n"]) >= int(total) > 0


def simpan_jawaban(id_mahasiswa: int, jawaban: Mapping[str, int]) -> int:
    """Simpan jawaban seluruh subkriteria. Idempoten: hapus jawaban lama dulu."""
    sub = {
        r["kode_sub"]: r["id_subkriteria"]
        for r in query_all("SELECT id_subkriteria, kode_sub FROM subkriteria")
    }
    pairs = []
    for kode, skor in jawaban.items():
        if kode not in sub:
            raise ValueError(f"Subkriteria tidak dikenal: {kode}")
        if int(skor) < config.LIKERT_MIN or int(skor) > config.LIKERT_MAX:
            raise ValueError(f"Skor {kode} harus {config.LIKERT_MIN}-{config.LIKERT_MAX}")
        pairs.append((id_mahasiswa, sub[kode], int(skor)))
    if len(pairs) != len(sub):
        raise ValueError(
            f"Jawaban tidak lengkap: {len(pairs)} dari {len(sub)} subkriteria."
        )
    execute("DELETE FROM jawaban_kuesioner WHERE id_mahasiswa=%s", (id_mahasiswa,))
    execute_many(
        "INSERT INTO jawaban_kuesioner (id_mahasiswa, id_subkriteria, skor_likert) "
        "VALUES (%s,%s,%s)",
        pairs,
    )
    return len(pairs)


def ambil_jawaban_mahasiswa(id_mahasiswa: int) -> dict[str, int]:
    rows = query_all(
        "SELECT s.kode_sub, j.skor_likert FROM jawaban_kuesioner j "
        "JOIN subkriteria s ON s.id_subkriteria=j.id_subkriteria "
        "WHERE j.id_mahasiswa=%s",
        (id_mahasiswa,),
    )
    return {r["kode_sub"]: int(r["skor_likert"]) for r in rows}


def ambil_daftar_pengisi() -> list[dict[str, Any]]:
    """Mahasiswa yang sudah mengisi, lengkap dengan jumlah jawaban."""
    return query_all(
        "SELECT m.id_mahasiswa, m.nim, m.nama, "
        "COUNT(j.id_jawaban) AS jumlah, MAX(j.tanggal_isi) AS terakhir "
        "FROM mahasiswa m JOIN jawaban_kuesioner j "
        "ON j.id_mahasiswa = m.id_mahasiswa "
        "GROUP BY m.id_mahasiswa, m.nim, m.nama "
        "ORDER BY terakhir DESC"
    )


# ════════════════════════════════════════════════════════════
# PENILAIAN (orchestrasi: FAHP -> skor -> kategori -> ranking)
# ════════════════════════════════════════════════════════════
def hitung_semua_penilaian() -> int:
    """Proses otomatis: bobot FAHP -> nilai risiko -> rank, simpan semua."""
    bobot = ambil_bobot_tersimpan()
    if not bobot:
        return 0

    semua = ambil_daftar_pengisi()
    if not semua:
        execute("DELETE FROM hasil_penilaian")
        return 0

    total_sub = int(query_one("SELECT COUNT(*) AS n FROM subkriteria")["n"])
    daftar: list[tuple[str, str, m_risiko.HasilRisiko]] = []
    for m in semua:
        if int(m["jumlah"]) < total_sub:
            continue
        jawaban = ambil_jawaban_mahasiswa(int(m["id_mahasiswa"]))
        try:
            h = m_risiko.hitung_nilai_risiko(jawaban, bobot)
        except ValueError as exc:
            logger.warning("Gagal menilai %s: %s", m["nim"], exc)
            continue
        daftar.append((m["nim"], m["nama"], h))

    ranking = m_risiko.ranking_dari_hasil(daftar)

    execute("DELETE FROM hasil_penilaian")
    id_by_nim = {
        r["nim"]: r["id_mahasiswa"]
        for r in query_all("SELECT id_mahasiswa, nim FROM mahasiswa")
    }
    baris = [
        (id_by_nim[r["nim"]], r["nilai_risiko"], r["kategori"], r["peringkat"])
        for r in ranking
        if r["nim"] in id_by_nim
    ]
    if baris:
        execute_many(
            "INSERT INTO hasil_penilaian "
            "(id_mahasiswa, nilai_risiko, kategori_risiko, peringkat) "
            "VALUES (%s,%s,%s,%s)",
            baris,
        )
    return len(baris)


def ambil_hasil_penilaian() -> list[dict[str, Any]]:
    return query_all(
        "SELECT h.peringkat, m.nim, m.nama, h.nilai_risiko, h.kategori_risiko "
        "FROM hasil_penilaian h JOIN mahasiswa m ON m.id_mahasiswa=h.id_mahasiswa "
        "ORDER BY h.peringkat, m.nama"
    )


def ambil_ranking() -> list[dict[str, Any]]:
    return ambil_hasil_penilaian()


def statistik_dashboard() -> dict[str, Any]:
    """Angka untuk kartu statistik + donut distribusi."""
    n_mhs = int(query_one("SELECT COUNT(*) AS n FROM mahasiswa")["n"])
    n_kuis = int(query_one(
        "SELECT COUNT(DISTINCT id_mahasiswa) AS n FROM jawaban_kuesioner"
    )["n"])
    n_hasil = int(query_one("SELECT COUNT(*) AS n FROM hasil_penilaian")["n"])
    rows = query_all(
        "SELECT kategori_risiko, COUNT(*) AS n FROM hasil_penilaian "
        "GROUP BY kategori_risiko"
    )
    distribusi = {"Rendah": 0, "Sedang": 0, "Tinggi": 0}
    for r in rows:
        if r["kategori_risiko"] in distribusi:
            distribusi[r["kategori_risiko"]] = int(r["n"])
    return {
        "total_mahasiswa": n_mhs,
        "total_kuesioner": n_kuis,
        "total_penilaian": n_hasil,
        "total_ranking": n_hasil,
        "distribusi": distribusi,
    }


# ════════════════════════════════════════════════════════════
# EXPORT EXCEL (format SPSS untuk uji reliabilitas & validitas)
# ════════════════════════════════════════════════════════════
def export_ke_excel(path: str) -> int:
    """Ekspor jawaban ke .xlsx — format siap SPSS.

    Baris header : NIM | Nama | SK1_1 | SK1_2 | ... | SK6_5
    Setiap baris : satu mahasiswa yang sudah mengisi lengkap.

    Returns jumlah baris data yang ditulis.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    subs = ambil_semua_subkriteria()
    kode_subs = [s["kode_sub"] for s in subs]
    kode_spss = [s.replace(".", "_") for s in kode_subs]

    pengisi = ambil_daftar_pengisi()
    if not pengisi:
        raise ValueError("Belum ada data kuesioner yang masuk.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Data Kuesioner"

    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF",
                              fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    headers = ["NIM", "Nama"] + kode_spss
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = thin_border

    row_num = 2
    for m in pengisi:
        jawaban = ambil_jawaban_mahasiswa(int(m["id_mahasiswa"]))
        if len(jawaban) < len(kode_subs):
            continue
        ws.cell(row=row_num, column=1, value=str(m["nim"]))
        ws.cell(row=row_num, column=2, value=str(m["nama"]))
        for j, kode in enumerate(kode_subs):
            cell = ws.cell(row=row_num, column=j + 3, value=jawaban.get(kode, ""))
            cell.border = thin_border
        row_num += 1

    ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 30)

    wb.save(path)
    return row_num - 2
