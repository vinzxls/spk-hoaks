"""MySQL connection layer for the Hoax Risk SPK desktop app.

Public API (used by all modules — do not rename):

    get_db()       Single lazy connection (autocommit=False)
    get_cursor()   Context manager yielding a DictCursor;
                   commits on clean exit, rolls back on error.
    query_all()    Run SELECT, return list of dicts.
    query_one()    Run SELECT, return one dict or None.
    execute()      Run INSERT/UPDATE/DELETE, return lastrowid.
    execute_many() Run executemany, return affected row count.
    close_db()     Close the connection and reset the singleton.
"""

from __future__ import annotations

import logging
import sys
import threading
import typing
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

# Allow importing `config.py` when running from the project root
# (e.g. `python main.py` inside spk_hoaks/).
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402

_DB_CONN: typing.Any = None
_DB_LOCK = threading.Lock()


def get_db() -> typing.Any:
    """Return the singleton MySQL connection, creating it lazily."""
    global _DB_CONN
    with _DB_LOCK:
        if _DB_CONN is None or not _is_open(_DB_CONN):
            import pymysql

            try:
                _DB_CONN = pymysql.connect(
                    host=str(config.DB_CONFIG["host"]),
                    port=int(config.DB_CONFIG["port"]),
                    user=str(config.DB_CONFIG["user"]),
                    password=str(config.DB_CONFIG["password"]),
                    database=str(config.DB_CONFIG["database"]),
                    charset=str(config.DB_CONFIG["charset"]),
                    autocommit=False,
                )
            except Exception as exc:  # pragma: no cover - DB unavailable
                logger.exception("Database connection failed")
                raise ConnectionError(
                    "Tidak dapat terhubung ke database MySQL "
                    f"({_ringkas_error(exc)})."
                ) from exc
    return _DB_CONN


def _ringkas_error(exc: BaseException) -> str:
    """Ubah error driver MySQL menjadi satu kalimat yang bisa ditindaklanjuti.

    Pesan asli pymysql panjang dan berbahasa Inggris; pengguna aplikasi
    hanya perlu tahu bagian mana yang harus diperbaiki (MySQL mati, nama
    database salah, atau user/password ditolak).
    """
    kode = exc.args[0] if exc.args else None
    if kode == 2003:
        return "MySQL belum berjalan, nyalakan Laragon lalu klik Start All"
    if kode == 1045:
        return "user/password MySQL ditolak, periksa DB_CONFIG di config.py"
    if kode == 1049:
        return "database tidak ditemukan, impor db/seed.sql"
    if kode == 1044:
        return "user MySQL tidak punya akses ke database spk_hoaks"
    if kode is not None:
        return f"kode error MySQL {kode}"
    return type(exc).__name__


def _is_open(conn: typing.Any) -> bool:
    """Best-effort check whether the connection is still alive.

    ``conn.open`` hanya menandakan flag sisi klien; koneksi yang sudah
    diputus server (MySQL restart, ``wait_timeout``, ``KILL``) tetap
    dilaporkan terbuka. Jadi ping-kan ke server.
    """
    try:
        if not conn.open:
            return False
        conn.ping(reconnect=False)
        return True
    except AttributeError:
        return True
    except Exception:
        return False


def _koneksi_mati(exc: BaseException) -> bool:
    """True bila exception menandakan koneksi perlu dibuat ulang."""
    import pymysql

    if isinstance(exc, (pymysql.err.InterfaceError, pymysql.err.OperationalError)):
        kode = exc.args[0] if exc.args else None
        # 2006 = server gone away, 2013 = lost connection, 0 = interface closed.
        return kode in (0, 2006, 2013) or isinstance(exc, pymysql.err.InterfaceError)
    return False


def _reset_db() -> None:
    """Tutup dan lupakan koneksi lama (dipakai sebelum reconnect)."""
    global _DB_CONN
    with _DB_LOCK:
        if _DB_CONN is not None:
            try:
                _DB_CONN.close()
            except Exception:
                pass
            _DB_CONN = None


@contextmanager
def get_cursor() -> typing.Generator[typing.Any, None, None]:
    """Yield a DictCursor; commit on success, rollback on error.

    Bila koneksi sudah diputus server (MySQL restart, ``wait_timeout``,
    ``KILL``), koneksi dibuang lalu dicoba SEKALI lagi dengan koneksi
    baru. Tanpa ini, satu restart MySQL membuat semua aksi gagal sampai
    aplikasi ditutup dan dibuka ulang.
    """
    import pymysql

    for percobaan in (1, 2):
        conn = get_db()
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
        except Exception as exc:
            if percobaan == 1 and _koneksi_mati(exc):
                _reset_db()
                continue
            raise
        try:
            yield cursor
            conn.commit()
            return
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            if percobaan == 1 and _koneksi_mati(exc):
                logger.warning(
                    "Koneksi database terputus; mencoba menyambung ulang."
                )
                _reset_db()
                continue
            logger.exception("Database transaction rolled back")
            raise
        finally:
            try:
                cursor.close()
            except Exception:
                pass


def query_all(
    sql: str, params: typing.Sequence[typing.Any] | None = None
) -> list[dict[str, typing.Any]]:
    """Run a SELECT and return all rows as dicts."""
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        return list(cur.fetchall())


def query_one(
    sql: str, params: typing.Sequence[typing.Any] | None = None
) -> dict[str, typing.Any] | None:
    """Run a SELECT and return the first row, or None."""
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        row = cur.fetchone()
        return dict(row) if row is not None else None


def execute(
    sql: str, params: typing.Sequence[typing.Any] | None = None
) -> int:
    """Run INSERT/UPDATE/DELETE and return the last inserted id."""
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid or 0


def execute_many(
    sql: str, seq_of_params: typing.Sequence[typing.Sequence[typing.Any]]
) -> int:
    """Run executemany and return the number of affected rows."""
    with get_cursor() as cur:
        try:
            return int(cur.executemany(sql, seq_of_params))
        except TypeError:  # pragma: no cover - driver quirks
            total = 0
            for p in seq_of_params:
                cur.execute(sql, p)
                total += 1
            return total


def close_db() -> None:
    """Close the singleton connection and reset it to None."""
    global _DB_CONN
    with _DB_LOCK:
        if _DB_CONN is not None:
            try:
                _DB_CONN.close()
            except Exception:  # pragma: no cover - defensive
                logger.warning("Error while closing DB connection", exc_info=True)
            finally:
                _DB_CONN = None
