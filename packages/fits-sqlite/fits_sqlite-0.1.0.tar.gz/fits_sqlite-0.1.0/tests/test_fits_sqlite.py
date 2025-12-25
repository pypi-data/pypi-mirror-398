import unittest
import sqlite3
import tempfile
from pathlib import Path
from astropy.io import fits
import fits_sqlite
from fits_sqlite import _packer


class TestFitsSqlite(unittest.TestCase):
    def setUp(self):
        """Set up test files in a temporary directory."""
        # Use TemporaryDirectory wrapper for better cleanup guarantees
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir_obj.name

        self.fits_file = Path(self.test_dir) / "test.fits"
        self.existing_fits_file = Path(self.test_dir) / "existing.fits"

        # Create a dummy FITS file to test appending to
        primary_hdu = fits.PrimaryHDU(data=[[1, 2], [3, 4]])
        hdul = fits.HDUList([primary_hdu])
        hdul.writeto(self.existing_fits_file)
        hdul.close()

    def tearDown(self):
        """Clean up the temporary directory."""
        # Explicit cleanup, though the object would also do it on GC/exit
        self.temp_dir_obj.cleanup()

    def test_create_new_db(self):
        """Test creating a new DB in a non-existent FITS file."""
        with fits_sqlite.connect(self.fits_file) as conn:
            self.assertIsInstance(conn, sqlite3.Connection)
            conn.execute("CREATE TABLE test (id INT, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'hello')")

        # Verify the file was created and has the DB HDU
        self.assertTrue(self.fits_file.exists())
        with fits.open(self.fits_file) as hdul:
            self.assertIn(_packer.DB_HDU_NAME, hdul)

    def test_read_write_cycle(self):
        """Test writing data, closing, reopening, and reading back."""
        # Write
        with fits_sqlite.connect(self.fits_file) as conn:
            conn.execute("CREATE TABLE data (val REAL)")
            conn.execute("INSERT INTO data VALUES (123.456)")

        # Read
        with fits_sqlite.connect(self.fits_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT val FROM data")
            result = cursor.fetchone()[0]
            self.assertAlmostEqual(result, 123.456, places=3)

    def test_append_to_existing_fits(self):
        """Test adding a DB to an existing FITS file with other HDUs."""
        with fits_sqlite.connect(self.existing_fits_file) as conn:
            conn.execute("CREATE TABLE new_data (info TEXT)")

        with fits.open(self.existing_fits_file) as hdul:
            # Should have Primary HDU + DB HDU
            self.assertEqual(len(hdul), 2)
            self.assertIn(_packer.DB_HDU_NAME, hdul)
            # Verify original data is intact
            self.assertEqual(hdul[0].data[0][0], 1)

    def test_context_manager_error_handling(self):
        """Test that resources are cleaned up if an error occurs."""
        try:
            with fits_sqlite.connect(self.fits_file) as conn:
                conn.execute("CREATE TABLE foo (bar INT)")
                raise ValueError("Simulating an error")
        except ValueError:
            # Error was propagated, which is good.
            pass

        # Now, check if the file was still written (it should be)
        # The shim's finally block ensures data is written back even on error
        self.assertTrue(self.fits_file.exists())

        # Verify data was written before the error
        with fits_sqlite.connect(self.fits_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            self.assertIn(("foo",), tables)

    def test_no_change_no_write(self):
        """Test that the FITS file is not rewritten if the DB is not changed."""
        # Create the file first
        with fits_sqlite.connect(self.fits_file) as conn:
            conn.execute("CREATE TABLE initial (id INT)")

        initial_mod_time = self.fits_file.stat().st_mtime

        # Open and close without changes
        with fits_sqlite.connect(self.fits_file):
            pass  # Do nothing

        final_mod_time = self.fits_file.stat().st_mtime

        # Timestamps should be identical because the file wasn't re-written
        self.assertEqual(initial_mod_time, final_mod_time)

    def test_custom_hdu_name(self):
        """Test specifying a custom HDU name."""
        custom_name = "MY_CUSTOM_DB"
        with fits_sqlite.connect(self.fits_file, hdu_name=custom_name) as conn:
            conn.execute("CREATE TABLE custom (val INT)")
            conn.execute("INSERT INTO custom VALUES (42)")

        # Verify it exists under the custom name
        with fits.open(self.fits_file) as hdul:
            self.assertIn(custom_name, hdul)
            self.assertNotIn(_packer.DB_HDU_NAME, hdul)

        # Verify we can read it back using the custom name
        with fits_sqlite.connect(self.fits_file, hdu_name=custom_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT val FROM custom")
            self.assertEqual(cursor.fetchone()[0], 42)


if __name__ == "__main__":
    unittest.main()
