# fits-sqlite

A Python library for embedding a portable SQLite database inside a FITS (Flexible Image Transport System) file.

## Core Concept

`fits-sqlite` provides a mechanism to create "Self-Contained Experiment Files" where raw scientific data (the FITS image) and its analysis history (a relational SQLite DB) travel together. This is ideal for sharing data and analysis results without requiring a connection to a central database server.

The library does not store redundant pixel data. Instead, the embedded database stores metadata, coordinates, and analysis results, treating the FITS file as the single source of truth for image data.

## Installation

### From Source (Current)
To install the library directly from the repository:

```bash
git clone https://github.com/coredumped/fits_sqlite.git
cd fits_sqlite
pip install .
```

### From PyPI
*(Coming soon)*
```bash
pip install fits-sqlite
```

## Usage

The library provides a high-level Python context manager that mimics the standard `sqlite3` interface, abstracting away the underlying FITS file structure. It uses a temporary directory to safely manage the database and any associated sidecar files (like WAL or journals), ensuring clean cleanup after use.

### Creating a new FITS file with an embedded database

```python
import fits_sqlite
import os

FITS_FILE = 'exposure_01.fits'

# Define a schema for your analysis data
TABLE_SCHEMA = """
CREATE TABLE clusters (
    cluster_id INT PRIMARY KEY,
    x INT,
    y INT,
    width INT,
    height INT,
    energy REAL,
    class_score REAL
);
"""

# Sample data
TEST_DATA = [
    (1, 100, 150, 20, 20, 512.5, 0.95),
    (2, 300, 400, 25, 25, 1024.0, 0.88),
]

# The context manager handles creating the file if it doesn't exist
with fits_sqlite.connect(FITS_FILE) as conn:
    cursor = conn.cursor()
    print("Creating table 'clusters'...")
    cursor.execute(TABLE_SCHEMA)
    
    print(f"Inserting {len(TEST_DATA)} rows...")
    cursor.executemany("INSERT INTO clusters VALUES (?, ?, ?, ?, ?, ?, ?);", TEST_DATA)

print(f"Database created and embedded in {FITS_FILE}")
```

### Reading from an existing FITS file

```python
import fits_sqlite

FITS_FILE = 'exposure_01.fits'

with fits_sqlite.connect(FITS_FILE) as conn:
    cursor = conn.cursor()
    
    print("Querying for clusters with energy > 900...")
    cursor.execute("SELECT * FROM clusters WHERE energy > 900 ORDER BY cluster_id")
    results = cursor.fetchall()
    
    print(f"Found {len(results)} matching rows:")
    for row in results:
        print(row)

```

### Using a Custom HDU Name

By default, the database is stored in a binary table HDU named `EMBEDDED_DB`. You can specify a custom HDU name if needed:

```python
with fits_sqlite.connect('my_data.fits', hdu_name='MY_CUSTOM_DB') as conn:
    # The database will be stored in/read from the 'MY_CUSTOM_DB' HDU
    pass
```

## Examples

The `examples/` directory contains a complete sample script `basic_example.py` that demonstrates a real-world workflow:
1.  Downloads a sample astronomical image (`HorseHead.fits`).
2.  Calculates image statistics (mean, stddev, max) using Astropy.
3.  Creates an embedded SQLite table to store this analysis history.
4.  Saves the stats and queries them back.

To run the example:
```bash
python3 examples/basic_example.py
```
