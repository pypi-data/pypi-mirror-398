"""
The Packer/Unpacker for handling the physical storage of the
SQLite database within the FITS file.

This module uses astropy.io.fits to interact with FITS files.
It is responsible for:
1. Finding and extracting the raw byte stream of the SQLite DB.
2. Writing the raw byte stream back into the FITS file.
3. Handling block padding and other FITS-specific details.
4. Supporting configurable HDU names for the embedded database.
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
from astropy.io import fits

DB_HDU_NAME = "EMBEDDED_DB"
SQLITE_MAGIC_HEADER = b"SQLite format 3\x00"


def extract_db_from_fits(
    fits_path: Union[str, Path], hdu_name: str = DB_HDU_NAME
) -> Optional[bytes]:
    """
    Extracts the SQLite database bytes from the designated HDU.

    Discovery Logic:
    1. Primary: Looks for a BinTableHDU with EXTNAME = 'EMBEDDED_DB' (or specified hdu_name).
    2. Fallback: Scans all HDUs for the SQLite "Magic Number".

    Args:
        fits_path (Union[str, Path]): The path to the FITS file.
        hdu_name (str): The name of the HDU to look for. Defaults to DB_HDU_NAME.

    Returns:
        Optional[bytes]: The raw bytes of the SQLite database, or None if not found.
    """
    if not Path(fits_path).exists():
        return None

    with fits.open(fits_path) as hdul:
        if hdu_name in hdul:
            hdu = hdul[hdu_name]
            if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                db_bytes = hdu.data[0][0].tobytes()
                return db_bytes.rstrip(b"\x00")

        for hdu in hdul:
            if hdu.data is not None:
                try:
                    data_bytes = np.asarray(hdu.data).tobytes()
                    if data_bytes.startswith(SQLITE_MAGIC_HEADER):
                        return data_bytes.rstrip(b"\x00")
                except (AttributeError, TypeError):
                    continue
    return None


def write_db_to_fits(
    fits_path: Union[str, Path], db_bytes: bytes, hdu_name: str = DB_HDU_NAME
) -> None:
    """
    Writes the SQLite database bytes into a BinTableHDU in the FITS file.

    If the designated HDU exists, it's overwritten. If not, it's created.
    This function will handle creating the FITS file if it doesn't exist.

    Args:
        fits_path (Union[str, Path]): The path to the FITS file.
        db_bytes (bytes): The raw bytes of the SQLite database.
        hdu_name (str): The name of the HDU to write to. Defaults to DB_HDU_NAME.
    """
    byte_array = np.frombuffer(db_bytes, dtype=np.uint8)

    column = fits.Column(
        name="db_data",
        format=f"{len(byte_array)}B",
        array=[byte_array],
    )
    db_hdu = fits.BinTableHDU.from_columns([column], name=hdu_name)

    if not Path(fits_path).exists():
        primary_hdu = fits.PrimaryHDU()
        hdul = fits.HDUList([primary_hdu, db_hdu])
        hdul.writeto(fits_path)
    else:
        with fits.open(fits_path, mode="update") as hdul:
            if hdu_name in hdul:
                hdul[hdu_name] = db_hdu
            else:
                hdul.append(db_hdu)
