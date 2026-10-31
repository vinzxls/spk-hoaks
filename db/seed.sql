-- ============================================================
-- SPK Penilaian Risiko Penyebaran Hoaks — Seed Data
-- Idempotent: safe to re-run (DELETE then INSERT).
-- ============================================================

USE spk_hoaks;

-- ── ADMIN ─────────────────────────────────────────────────
-- Password: admin123  |  Hash = SHA2(CONCAT('admin','admin123'), 256)
-- The application re-hashes on first login for runtime security.
DELETE FROM admin;
INSERT INTO admin (username, password, nama)
VALUES ('admin', SHA2(CONCAT('admin','admin123'), 256), 'Administrator');

-- ── KRITERIA (6 items) ───────────────────────────────────
DELETE FROM kriteria;
INSERT INTO kriteria (kode_kriteria, nama_kriteria) VALUES
  ('K1', 'Penggunaan Media Sosial'),
  ('K2', 'Literasi Digital'),
  ('K3', 'Verifikasi Informasi'),
  ('K4', 'Pemahaman Hoaks'),
  ('K5', 'Perilaku Penyebaran Informasi'),
  ('K6', 'Kemampuan Berpikir Kritis');

-- ── SUBKRITERIA (30 items: 5 per kriteria) ────────────────
DELETE FROM subkriteria;
INSERT INTO subkriteria (id_kriteria, kode_sub, nama_subkriteria) VALUES
  -- K1
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K1'), 'SK1.1', 'Aktivitas berbagi informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K1'), 'SK1.2', 'Intensitas penggunaan media sosial'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K1'), 'SK1.3', 'Paparan informasi di media sosial'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K1'), 'SK1.4', 'Ketergantungan pada media sosial untuk memperoleh berita'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K1'), 'SK1.5', 'Kecenderungan berbagi konten tanpa verifikasi'),
  -- K2
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K2'), 'SK2.1', 'Pemahaman informasi digital'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K2'), 'SK2.2', 'Evaluasi sumber informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K2'), 'SK2.3', 'Sikap terhadap informasi digital'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K2'), 'SK2.4', 'Kemampuan memahami konteks informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K2'), 'SK2.5', 'Kesadaran terhadap informasi digital yang dimanipulasi'),
  -- K3
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K3'), 'SK3.1', 'Pemeriksaan sumber informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K3'), 'SK3.2', 'Verifikasi detail informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K3'), 'SK3.3', 'Pemeriksaan fakta informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K3'), 'SK3.4', 'Konsultasi kepada pihak lain sebelum menerima informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K3'), 'SK3.5', 'Kebiasaan mengevaluasi kredibilitas sumber'),
  -- K4
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K4'), 'SK4.1', 'Kemampuan mengenali berita hoaks'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K4'), 'SK4.2', 'Pengalaman terhadap hoaks'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K4'), 'SK4.3', 'Kemampuan membedakan informasi yang benar dan salah'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K4'), 'SK4.4', 'Pengetahuan tentang ciri-ciri hoaks'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K4'), 'SK4.5', 'Kesadaran akan dampak hoaks dalam masyarakat'),
  -- K5
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K5'), 'SK5.1', 'Kebiasaan berbagi informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K5'), 'SK5.2', 'Kehati-hatian dalam berbagi informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K5'), 'SK5.3', 'Pengaruh daya tarik informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K5'), 'SK5.4', 'Selektivitas dalam menyebarkan informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K5'), 'SK5.5', 'Tanggung jawab atas informasi yang dibagikan'),
  -- K6
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K6'), 'SK6.1', 'Analisis informasi (memahami isi informasi secara logis)'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K6'), 'SK6.2', 'Menilai kebenaran suatu informasi'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K6'), 'SK6.3', 'Pertimbangan konsekuensi (kemampuan memikirkan dampak dan akibat sebelum membagi informasi)'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K6'), 'SK6.4', 'Kemampuan menganalisis argumen secara kritis'),
  ((SELECT id_kriteria FROM kriteria WHERE kode_kriteria='K6'), 'SK6.5', 'Bersikap skeptis terhadap informasi yang tidak terverifikasi');

-- ── MATRIKS PERBANDINGAN (6×6 = 36 rows) ────────────────
--
-- Defensible default matrix for hoax risk assessment.
-- Priority rationale: K5 (spreading behavior) and K1 (media usage)
-- are the strongest direct risk indicators. K6 (critical thinking)
-- and K4 (hoax understanding) are protective factors. K2 (digital
-- literacy) and K3 (verification) are weaker differentiators.
--
-- Scale: Saaty 1–9. All reciprocals verified (a_ij × a_ji = 1).
-- Values: integers 1–9 and reciprocals 0.111–0.500.
--
--       K1    K2    K3    K4    K5    K6
-- K1    1     2     3     2    1/2    1
-- K2   1/2    1     2     1    1/3   1/2
-- K3   1/3   1/2    1    1/2   1/4   1/3
-- K4   1/2    1     2     1    1/3   1/2
-- K5    2     3     4     3     1     2
-- K6    1     2     3     2    1/2    1
--
DELETE FROM matriks_perbandingan;
INSERT INTO matriks_perbandingan (kode_baris, kode_kolom, nilai) VALUES
  -- K1 vs all
  ('K1','K1', 1.000), ('K1','K2', 2.000), ('K1','K3', 3.000),
  ('K1','K4', 2.000), ('K1','K5', 0.500), ('K1','K6', 1.000),
  -- K2 vs all
  ('K2','K1', 0.500), ('K2','K2', 1.000), ('K2','K3', 2.000),
  ('K2','K4', 1.000), ('K2','K5', 0.333), ('K2','K6', 0.500),
  -- K3 vs all
  ('K3','K1', 0.333), ('K3','K2', 0.500), ('K3','K3', 1.000),
  ('K3','K4', 0.500), ('K3','K5', 0.250), ('K3','K6', 0.333),
  -- K4 vs all
  ('K4','K1', 0.500), ('K4','K2', 1.000), ('K4','K3', 2.000),
  ('K4','K4', 1.000), ('K4','K5', 0.333), ('K4','K6', 0.500),
  -- K5 vs all
  ('K5','K1', 2.000), ('K5','K2', 3.000), ('K5','K3', 4.000),
  ('K5','K4', 3.000), ('K5','K5', 1.000), ('K5','K6', 2.000),
  -- K6 vs all
  ('K6','K1', 1.000), ('K6','K2', 2.000), ('K6','K3', 3.000),
  ('K6','K4', 2.000), ('K6','K5', 0.500), ('K6','K6', 1.000);
