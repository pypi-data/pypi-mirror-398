"""
The Python Shim for interacting with the embedded SQLite database.
"""

import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Union

from . import _packer as packer


@contextmanager
def connect(
    fits_path: Union[str, Path], hdu_name: str = packer.DB_HDU_NAME, **kwargs: Any
) -> Iterator[sqlite3.Connection]:
    """
    A context manager to securely connect to an SQLite database
    embedded within a FITS file.

    This function extracts the SQLite database from a specific HDU in the
    FITS file, writes it to a file within a temporary directory, and yields
    a standard sqlite3 connection object.

    Using a temporary directory ensures that any auxiliary files created by
    SQLite (such as -wal or -journal files) are automatically cleaned up
    when the context exits.

    When the context is exited, the (potentially modified) database is
    written back into the FITS file.

    Args:
        fits_path (Union[str, Path]): The path to the FITS file.
        hdu_name (str): The name of the HDU to look for. Defaults to DB_HDU_NAME.
        **kwargs: Additional keyword arguments to pass to sqlite3.connect().

    Yields:
        sqlite3.Connection: A standard Python sqlite3 connection object.

    Example:
        >>> with fits_sqlite.connect('my_data.fits') as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        ...     print(cursor.fetchall())
    """
    db_bytes = None
    temp_dir = None
    conn = None

    try:
        db_bytes = packer.extract_db_from_fits(fits_path, hdu_name=hdu_name)

        temp_dir = tempfile.TemporaryDirectory()
        temp_db_path = Path(temp_dir.name) / "sqlite.db"

        if db_bytes:
            temp_db_path.write_bytes(db_bytes)

        conn = sqlite3.connect(temp_db_path, **kwargs)
        yield conn

    finally:
        if conn:
            conn.commit()
            conn.close()

        if temp_dir and temp_db_path.exists():
            updated_db_bytes = temp_db_path.read_bytes()

            if updated_db_bytes != db_bytes:
                packer.write_db_to_fits(fits_path, updated_db_bytes, hdu_name=hdu_name)

        if temp_dir:
            temp_dir.cleanup()
