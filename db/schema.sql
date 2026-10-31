-- ============================================================
-- SPK Penilaian Risiko Penyebaran Hoaks — DDL Schema
-- Universitas Pattimura — Program Studi Ilmu Komputer
-- MySQL 8.x | Engine: InnoDB | Charset: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS spk_hoaks
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE spk_hoaks;

-- ── 1. admin ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admin (
  id_admin   INT          NOT NULL AUTO_INCREMENT,
  username   VARCHAR(50)  NOT NULL,
  password   VARCHAR(255) NOT NULL COMMENT 'SHA256(user+pass) — re-hashed on first login',
  nama       VARCHAR(100) NOT NULL,
  PRIMARY KEY (id_admin),
  UNIQUE KEY uq_admin_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── 2. mahasiswa ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mahasiswa (
  id_mahasiswa  INT          NOT NULL AUTO_INCREMENT,
  nim           VARCHAR(20)  NOT NULL COMMENT 'Nomor Induk Mahasiswa (NIM)',
  nama          VARCHAR(100) NOT NULL,
  jenis_kelamin ENUM('Laki-laki','Perempuan') NOT NULL,
  angkatan      VARCHAR(10)  NOT NULL,
  username      VARCHAR(50)  NOT NULL,
  password      VARCHAR(255) NOT NULL COMMENT 'SHA256(user+pass)',
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_mahasiswa),
  UNIQUE KEY uq_mhs_nim  (nim),
  UNIQUE KEY uq_mhs_user (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── 3. kriteria ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kriteria (
  id_kriteria   INT          NOT NULL AUTO_INCREMENT,
  kode_kriteria VARCHAR(10)  NOT NULL COMMENT 'K1–K6',
  nama_kriteria VARCHAR(150) NOT NULL,
  PRIMARY KEY (id_kriteria),
  UNIQUE KEY uq_kode_kriteria (kode_kriteria)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── 4. subkriteria ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subkriteria (
  id_subkriteria   INT          NOT NULL AUTO_INCREMENT,
  id_kriteria      INT          NOT NULL,
  kode_sub         VARCHAR(10)  NOT NULL COMMENT 'SKx.y',
  nama_subkriteria VARCHAR(255) NOT NULL,
  PRIMARY KEY (id_subkriteria),
  UNIQUE KEY uq_kode_sub (kode_sub),
  KEY idx_sub_kriteria (id_kriteria),
  CONSTRAINT fk_sub_kriteria
    FOREIGN KEY (id_kriteria) REFERENCES kriteria(id_kriteria)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── 5. jawaban_kuesioner ──────────────────────────────────
-- One row per subkriteria per mahasiswa (skor Likert 1–5)
CREATE TABLE IF NOT EXISTS jawaban_kuesioner (
  id_jawaban     INT      NOT NULL AUTO_INCREMENT,
  id_mahasiswa   INT      NOT NULL,
  id_subkriteria INT      NOT NULL,
  skor_likert    TINYINT  NOT NULL,
  tanggal_isi    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_jawaban),
  UNIQUE KEY uq_mhs_sub (id_mahasiswa, id_subkriteria),
  KEY idx_jw_mhs   (id_mahasiswa),
  KEY idx_jw_sub   (id_subkriteria),
  CONSTRAINT fk_jw_mahasiswa
    FOREIGN KEY (id_mahasiswa)   REFERENCES mahasiswa(id_mahasiswa)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_jw_subkriteria
    FOREIGN KEY (id_subkriteria) REFERENCES subkriteria(id_subkriteria)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── 6. bobot_fahp — RESULT of Fuzzy AHP calculation ──────
-- One row per criterion: the final crisp weight.
-- Populated by backend after FEA runs, NOT by admin.
CREATE TABLE IF NOT EXISTS bobot_fahp (
  id_bobot       INT           NOT NULL AUTO_INCREMENT,
  id_kriteria    INT           NOT NULL UNIQUE,
  bobot_crisp    DECIMAL(8,6)  NOT NULL,
  tanggal_hitung DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_bobot),
  KEY idx_bobot_kriteria (id_kriteria),
  CONSTRAINT fk_bobot_kriteria
    FOREIGN KEY (id_kriteria) REFERENCES kriteria(id_kriteria)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── 7. hasil_penilaian — FINAL SCORE per mahasiswa ────────
CREATE TABLE IF NOT EXISTS hasil_penilaian (
  id_hasil        INT          NOT NULL AUTO_INCREMENT,
  id_mahasiswa    INT          NOT NULL UNIQUE,
  nilai_risiko    DECIMAL(6,2) NOT NULL COMMENT 'Skor 0–100',
  kategori_risiko ENUM('Rendah','Sedang','Tinggi') NOT NULL,
  peringkat       INT          NOT NULL,
  tanggal_hitung  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_hasil),
  KEY idx_hp_mhs (id_mahasiswa),
  CONSTRAINT fk_hp_mahasiswa
    FOREIGN KEY (id_mahasiswa) REFERENCES mahasiswa(id_mahasiswa)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── 8. matriks_perbandingan — RAW pairwise input ─────────
-- NOTE: The client's ERD only shows `bobot_fahp` (the RESULT
-- of Fuzzy AHP). However, the FEA engine requires the raw
-- 6×6 crisp pairwise comparison matrix as input to compute
-- the weights. This table stores that input matrix so the
-- engine can re-run when criteria are modified.
-- VALUES: Saaty 1–9 crisp scale. Reciprocals stored as
-- DECIMAL(5,3), e.g. 1/3 = 0.333, 1/7 = 0.143.
CREATE TABLE IF NOT EXISTS matriks_perbandingan (
  id         INT          NOT NULL AUTO_INCREMENT,
  kode_baris VARCHAR(10)  NOT NULL COMMENT 'kode_kriteria (e.g. K1)',
  kode_kolom VARCHAR(10)  NOT NULL COMMENT 'kode_kriteria (e.g. K2)',
  nilai      DECIMAL(5,3) NOT NULL COMMENT 'Saaty crisp value',
  PRIMARY KEY (id),
  UNIQUE KEY uq_pair (kode_baris, kode_kolom),
  KEY idx_pair_baris (kode_baris),
  KEY idx_pair_kolom (kode_kolom)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
