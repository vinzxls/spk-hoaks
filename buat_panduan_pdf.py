"""
Generate PANDUAN-MENJALANKAN.pdf untuk aplikasi SPK Risiko Hoaks.

Jalankan dari folder spk_hoaks:
    .venv\\Scripts\\python.exe buat_panduan_pdf.py

Menghasilkan file: PANDUAN-MENJALANKAN.pdf
"""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)

OUT = "PANDUAN-MENJALANKAN.pdf"

# ── Warna tema ────────────────────────────────────────────────
NAVY = colors.HexColor("#12335c")
BLUE = colors.HexColor("#1b6ec2")
GREY = colors.HexColor("#4a4a4a")
LIGHT = colors.HexColor("#eef3f8")
CODE_BG = colors.HexColor("#f2f4f7")
BORDER = colors.HexColor("#c8d4e0")
GREEN = colors.HexColor("#1e7a46")

# ── Gaya teks ─────────────────────────────────────────────────
_ss = getSampleStyleSheet()

ST_TITLE = ParagraphStyle(
    "TitleX", parent=_ss["Title"], fontName="Helvetica-Bold",
    fontSize=20, leading=25, textColor=NAVY, alignment=TA_LEFT,
    spaceAfter=2,
)
ST_SUB = ParagraphStyle(
    "SubX", parent=_ss["Normal"], fontName="Helvetica",
    fontSize=11.5, leading=16, textColor=GREY, spaceAfter=4,
)
ST_H1 = ParagraphStyle(
    "H1X", parent=_ss["Heading1"], fontName="Helvetica-Bold",
    fontSize=14, leading=18, textColor=colors.white,
    backColor=NAVY, borderPadding=(6, 8, 7, 8),
    spaceBefore=16, spaceAfter=10,
)
ST_H2 = ParagraphStyle(
    "H2X", parent=_ss["Heading2"], fontName="Helvetica-Bold",
    fontSize=11.5, leading=15, textColor=BLUE,
    spaceBefore=10, spaceAfter=4,
)
ST_BODY = ParagraphStyle(
    "BodyX", parent=_ss["Normal"], fontName="Helvetica",
    fontSize=10.5, leading=15, textColor=colors.HexColor("#1f1f1f"),
    spaceAfter=6,
)
ST_BULLET = ParagraphStyle(
    "BulletX", parent=ST_BODY, leftIndent=16, bulletIndent=4,
    spaceAfter=3,
)
ST_NOTE = ParagraphStyle(
    "NoteX", parent=ST_BODY, fontName="Helvetica-Oblique",
    textColor=GREY, leftIndent=10, borderPadding=4,
)
ST_CODE = ParagraphStyle(
    "CodeX", parent=_ss["Code"], fontName="Courier",
    fontSize=9, leading=12.5, textColor=colors.HexColor("#14243a"),
)


def code(text: str):
    """Blok kode satu-kolom dengan latar abu."""
    inner = XPreformatted(text, ST_CODE)
    t = Table([[inner]], colWidths=[16.4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def table(rows, widths, header=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("LEADING", (0, 0), (-1, -1), 13),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, LIGHT]),
        ]
    else:
        style += [("ROWBACKGROUNDS", (0, 0), (-1, -1),
                   [colors.white, LIGHT])]
    t.setStyle(TableStyle(style))
    return t


def bullets(items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{x}", ST_BULLET) for x in items]


def build() -> None:
    story = []

    # ── Judul ────────────────────────────────────────────────
    story.append(Paragraph("Panduan Menjalankan Aplikasi", ST_TITLE))
    story.append(Paragraph(
        "SPK Penilaian Tingkat Risiko Penyebaran Hoaks", ST_SUB))
    story.append(Paragraph(
        "Panduan ini untuk <b>Sela</b> agar dapat menjalankan sistem "
        "secara mandiri di laptopnya.", ST_BODY))
    story.append(Paragraph(
        "Lokasi proyek: <font face='Courier'>C:\\Orderan Sela\\spk_hoaks</font>",
        ST_BODY))
    story.append(Spacer(1, 10))

    # ── A. Cara menjalankan rutin ────────────────────────────
    story.append(Paragraph("A. Cara Menjalankan (Rutin, Sehari-hari)", ST_H1))

    story.append(Paragraph("Langkah 1 &mdash; Nyalakan MySQL", ST_H2))
    for p in bullets([
        "Buka <b>Laragon</b>.",
        "Klik <b>Start All</b> (pastikan tulisan <b>MySQL</b> sudah "
        "berwarna hijau / berjalan).",
        "Tunggu sampai MySQL benar-benar aktif sebelum lanjut.",
    ]):
        story.append(p)
    story.append(Paragraph(
        "Catatan: aplikasi <b>tidak akan jalan</b> jika MySQL belum menyala.",
        ST_NOTE))

    story.append(Paragraph("Langkah 2 &mdash; Jalankan Aplikasi", ST_H2))
    for p in bullets([
        "Buka folder <font face='Courier'>C:\\Orderan Sela\\spk_hoaks</font>.",
        "Klik dua kali file <b>Jalankan Aplikasi.bat</b>.",
        "Jendela hitam akan muncul, lalu jendela login aplikasi terbuka.",
        "<b>Jangan tutup jendela hitam</b> selama aplikasi dipakai.",
    ]):
        story.append(p)

    story.append(Paragraph("Langkah 3 &mdash; Login", ST_H2))
    story.append(Paragraph(
        "Isi akun lalu klik tombol <b>Login</b>:", ST_BODY))
    story.append(table(
        [
            [Paragraph("<b>Peran</b>", ST_BODY),
             Paragraph("<b>Username</b>", ST_BODY),
             Paragraph("<b>Password</b>", ST_BODY)],
            [Paragraph("Admin", ST_BODY),
             Paragraph("admin", ST_BODY),
             Paragraph("admin123", ST_BODY)],
            [Paragraph("Mahasiswa", ST_BODY),
             Paragraph("dibuat oleh Admin", ST_BODY),
             Paragraph("dibuat oleh Admin", ST_BODY)],
        ],
        widths=[4.0 * cm, 6.2 * cm, 6.2 * cm],
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Catatan: akun mahasiswa dibuat oleh Admin melalui menu "
        "<b>Kelola Mahasiswa</b> di dalam aplikasi. Password dibuat di situ.",
        ST_NOTE))

    story.append(Paragraph("Langkah 4 &mdash; Menutup Aplikasi", ST_H2))
    for p in bullets([
        "Tutup jendela aplikasi seperti biasa (tombol X).",
        "Tutup jendela hitam (jika masih terbuka).",
        "Di Laragon, klik <b>Stop All</b> untuk mematikan MySQL.",
    ]):
        story.append(p)

    # ── B2. Memasang di laptop baru ──────────────────────────
    story.append(Paragraph("B2. Memasang di Laptop Baru", ST_H1))
    story.append(Paragraph(
        "Bagian ini dipakai <b>sekali saja</b> saat aplikasi dipasang di "
        "laptop lain. Kode proyek tersimpan di:", ST_BODY))
    story.append(Paragraph(
        "<font face='Courier'>https://github.com/vinzxls/spk-hoaks</font>",
        ST_NOTE))

    story.append(Paragraph("Langkah 1 &mdash; Pasang prasyarat", ST_H2))
    for p in bullets([
        "<b>Git</b> &mdash; unduh dari git-scm.com/download/win, install "
        "dengan pilihan bawaan.",
        "<b>Python 3.13</b> &mdash; unduh dari python.org/downloads. Saat "
        "instalasi <b>centang &ldquo;Add python.exe to PATH&rdquo;</b>.",
        "<b>Laragon</b> &mdash; untuk MySQL, seperti biasa.",
    ]):
        story.append(p)

    story.append(Paragraph("Langkah 2 &mdash; Unduh kode dari GitHub", ST_H2))
    story.append(Paragraph(
        "Buka Command Prompt (Win + R, ketik <font face='Courier'>cmd</font>, "
        "Enter), lalu jalankan:", ST_BODY))
    story.append(code(
        'cd C:\\\n'
        'git clone https://github.com/vinzxls/spk-hoaks.git "Orderan Sela\\spk_hoaks"\n'
        'cd "Orderan Sela\\spk_hoaks"'))
    story.append(Paragraph(
        "Perintah ini membuat folder <font face='Courier'>C:\\Orderan "
        "Sela\\spk_hoaks</font> berisi seluruh kode. Kalau kode di GitHub "
        "diperbarui, cukup jalankan <font face='Courier'>git pull</font> di "
        "folder itu.", ST_BODY))

    story.append(Paragraph("Langkah 3 &mdash; Buat lingkungan Python", ST_H2))
    story.append(code(
        'python -m venv .venv\n'
        '.venv\\Scripts\\pip install -r requirements.txt'))
    story.append(Paragraph(
        "Tunggu sampai selesai. Proses ini mengunduh pymysql, reportlab, "
        "openpyxl, dan pytest.", ST_BODY))

    story.append(Paragraph("Langkah 4 &mdash; Nyalakan MySQL &amp; impor "
                           "database", ST_H2))
    for p in bullets([
        "Buka <b>Laragon</b>, klik <b>Start All</b>, tunggu MySQL hijau.",
        "Di folder proyek, klik dua kali <b>Impor Database.bat</b>.",
        "Skrip membuat database <b>spk_hoaks</b>, seluruh tabel, dan mengisi "
        "data awal (admin, 6 kriteria, 30 subkriteria, matriks perbandingan).",
        "Tunggu sampai muncul tulisan <b>SELESAI</b>.",
    ]):
        story.append(p)
    story.append(Paragraph(
        "Catatan: skrip ini <b>menolak berjalan</b> kalau database sudah "
        "berisi jawaban kuesioner, supaya data asli tidak terhapus.", ST_NOTE))

    story.append(Paragraph("Langkah 5 &mdash; Jalankan aplikasi", ST_H2))
    story.append(Paragraph(
        "Klik dua kali <b>Jalankan Aplikasi.bat</b>, lalu login sebagai "
        "<b>admin</b> / <b>admin123</b>. Langkah 1&ndash;4 tidak perlu "
        "diulang lagi di kemudian hari.", ST_BODY))

    # ── B3. Cara alternatif ──────────────────────────────────
    story.append(Paragraph("B3. Cara Alternatif (lewat Terminal)", ST_H1))
    story.append(Paragraph(
        "Jika file <font face='Courier'>.bat</font> tidak bisa dipakai, "
        "jalankan perintah berikut di Command Prompt / PowerShell:", ST_BODY))
    story.append(code(
        'cd "C:\\Orderan Sela\\spk_hoaks"\n'
        '.venv\\Scripts\\activate\n'
        'python main.py'))

    story.append(PageBreak())

    # ── C. Syarat sistem ─────────────────────────────────────
    story.append(Paragraph("C. Syarat Sistem (untuk Referensi)", ST_H1))
    story.append(table(
        [
            [Paragraph("<b>Komponen</b>", ST_BODY),
             Paragraph("<b>Keterangan</b>", ST_BODY)],
            [Paragraph("Python", ST_BODY),
             Paragraph("Versi 3.13", ST_BODY)],
            [Paragraph("MySQL", ST_BODY),
             Paragraph("Lewat Laragon (port 3306, user root, tanpa password)",
                       ST_BODY)],
            [Paragraph("Database", ST_BODY),
             Paragraph("Nama database: spk_hoaks", ST_BODY)],
            [Paragraph("Library Python", ST_BODY),
             Paragraph("Sesuai requirements.txt (pymysql, reportlab, "
                       "openpyxl, pytest)", ST_BODY)],
            [Paragraph("Sumber kode", ST_BODY),
             Paragraph("https://github.com/vinzxls/spk-hoaks", ST_BODY)],
        ],
        widths=[4.0 * cm, 12.4 * cm],
    ))

    story.append(PageBreak())

    # ── D. Penanganan masalah ────────────────────────────────
    story.append(Paragraph("D. Jika Ada Masalah", ST_H1))

    story.append(Paragraph(
        "0. Langkah pertama: jalankan &ldquo;Cek Database.bat&rdquo;", ST_H2))
    story.append(Paragraph(
        "Kalau aplikasi terbuka tetapi <b>tidak bisa login</b> dengan akun apa "
        "pun, jangan menebak. Di folder proyek, klik dua kali "
        "<b>Cek Database.bat</b>. Skrip itu hanya <b>membaca</b> (tidak "
        "mengubah data) dan menampilkan konfigurasi koneksi, keadaan MySQL, "
        "daftar tabel, jumlah baris tiap tabel, apakah akun admin ada dan "
        "apakah password admin123 cocok, serta daftar akun mahasiswa.", ST_BODY))
    story.append(Paragraph(
        "Di bagian akhir muncul <b>KESIMPULAN</b> berisi penyebabnya:", ST_BODY))
    story.append(table(
        [
            [Paragraph("<b>Pesan di kesimpulan</b>", ST_BODY),
             Paragraph("<b>Perbaikan</b>", ST_BODY)],
            [Paragraph("MySQL tidak bisa dihubungi (kode 2003)", ST_BODY),
             Paragraph("Buka Laragon &rarr; Start All", ST_BODY)],
            [Paragraph("user/password MySQL ditolak (kode 1045)", ST_BODY),
             Paragraph("Sesuaikan DB_CONFIG di config.py", ST_BODY)],
            [Paragraph("database belum ada (kode 1049)", ST_BODY),
             Paragraph("Klik dua kali Impor Database.bat", ST_BODY)],
            [Paragraph("tabel belum lengkap / tabel admin kosong", ST_BODY),
             Paragraph("Klik dua kali Impor Database.bat", ST_BODY)],
            [Paragraph("belum ada akun mahasiswa", ST_BODY),
             Paragraph("Normal di laptop baru; buat lewat admin", ST_BODY)],
        ],
        widths=[9.4 * cm, 7.0 * cm],
    ))
    story.append(Paragraph(
        "Catatan: <b>database tidak ikut tersimpan di GitHub</b>. Setelah "
        "clone, database harus diimpor sekali lewat <b>Impor Database.bat</b>. "
        "Kalau langkah itu terlewat, aplikasi tetap terbuka tetapi login selalu "
        "gagal karena tabel <font face='Courier'>admin</font> masih kosong.",
        ST_NOTE))

    story.append(Paragraph(
        "1. Tidak bisa login &mdash; &ldquo;Username atau password salah&rdquo;",
        ST_H2))
    story.append(Paragraph(
        "Password disimpan dalam bentuk <b>hash</b> (SHA256), bukan teks "
        "biasa. Untuk mereset password admin, buka terminal MySQL dan "
        "jalankan:", ST_BODY))
    story.append(code(
        "USE spk_hoaks;\n"
        "UPDATE admin\n"
        "   SET password = SHA2(CONCAT('admin','admin123'), 256)\n"
        " WHERE username = 'admin';"))

    story.append(Paragraph(
        "1b. Mahasiswa tidak bisa login setelah username-nya diubah",
        ST_H2))
    story.append(Paragraph(
        "Password disimpan memakai pola <b>hash(username + password)</b>. Jadi "
        "kalau username diubah tanpa mengisi password baru, password lamanya "
        "tidak lagi cocok dan akun itu tidak bisa dipakai login. Aplikasi "
        "sekarang menolak perubahan username tanpa password baru. Kalau sudah "
        "terlanjur terjadi, buka menu <b>Kelola Mahasiswa</b> &rarr; pilih "
        "mahasiswa &rarr; <b>Edit</b> &rarr; isi password baru &rarr; "
        "<b>Simpan</b>, lalu login dengan username dan password baru tersebut.",
        ST_BODY))

    story.append(Paragraph(
        "2. Pesan &ldquo;Tidak dapat terhubung ke database MySQL&rdquo;",
        ST_H2))
    for p in bullets([
        "Pastikan <b>MySQL di Laragon sudah Start</b>.",
        "Pastikan nama database benar: <font face='Courier'>spk_hoaks</font>.",
        "Periksa file <font face='Courier'>config.py</font>, bagian "
        "<font face='Courier'>DB_CONFIG</font>.",
    ]):
        story.append(p)

    story.append(Paragraph(
        "3. Pesan &ldquo;python is not recognized&rdquo;", ST_H2))
    story.append(Paragraph(
        "Python belum terpasang atau belum masuk PATH. Cara tercepat: pasang "
        "ulang Python 3.13, pilih <b>Modify</b>, dan centang <b>&ldquo;Add "
        "Python to environment variables&rdquo;</b>. Atau pakai perintah "
        "<font face='Courier'>py</font> sebagai ganti "
        "<font face='Courier'>python</font>:", ST_BODY))
    story.append(code("py -m venv .venv"))

    story.append(Paragraph(
        "4. Pesan &ldquo;Virtual environment .venv tidak ditemukan&rdquo;",
        ST_H2))
    story.append(Paragraph("Buat ulang lingkungan virtual:", ST_BODY))
    story.append(code(
        'cd "C:\\Orderan Sela\\spk_hoaks"\n'
        'python -m venv .venv\n'
        '.venv\\Scripts\\pip install -r requirements.txt'))

    story.append(Paragraph(
        "5. Aplikasi berjalan tetapi data kosong", ST_H2))
    story.append(Paragraph(
        "Jalankan <b>Impor Database.bat</b> (MySQL harus menyala). Atau lewat "
        "terminal:", ST_BODY))
    story.append(code(
        "mysql -u root < db\\schema.sql\n"
        "mysql -u root spk_hoaks < db\\seed.sql"))

    story.append(Paragraph(
        "6. Database sudah berisi data lama dan ingin mulai dari nol", ST_H2))
    for p in bullets([
        "Buka <b>Laragon</b> &rarr; <b>Database</b> (atau HeidiSQL).",
        "Hapus database <font face='Courier'>spk_hoaks</font>.",
        "Klik dua kali <b>Impor Database.bat</b> lagi.",
    ]):
        story.append(p)
    story.append(Paragraph(
        "Catatan: menghapus database ikut menghapus semua akun mahasiswa dan "
        "jawaban kuesioner. Ekspor dulu rekapnya lewat menu <b>Kuesioner "
        "&rarr; Ekspor Excel</b> kalau datanya masih dibutuhkan.", ST_NOTE))

    # ── E. Ringkasan ─────────────────────────────────────────
    story.append(Paragraph("E. Ringkasan Cepat", ST_H1))

    story.append(Paragraph("Setiap mau pakai aplikasi:", ST_H2))
    for p in bullets([
        "Laragon &rarr; <b>Start All</b>",
        "Klik dua kali <b>Jalankan Aplikasi.bat</b>",
        "Login sebagai admin / admin123",
    ]):
        story.append(p)

    story.append(Paragraph("Selesai pakai:", ST_H2))
    for p in bullets([
        "Tutup aplikasi",
        "Laragon &rarr; <b>Stop All</b>",
    ]):
        story.append(p)

    # ── Footer lewat callback ────────────────────────────────
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.6)
        canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GREY)
        canvas.drawString(
            2 * cm, 1.0 * cm,
            "SPK Penilaian Tingkat Risiko Penyebaran Hoaks")
        canvas.drawRightString(
            A4[0] - 2 * cm, 1.0 * cm, f"Halaman {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=2 * cm,
        title="Panduan Menjalankan Aplikasi SPK Risiko Hoaks",
        author="SPK Risiko Hoaks",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"OK: {OUT}")


if __name__ == "__main__":
    build()
