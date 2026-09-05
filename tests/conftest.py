"""
tests/conftest.py
-----------------
Pytest configuration and shared fixtures for integration tests.

Provides:
  - test_db: Isolated SQLite database for each test
  - temp_lxf_file: Temporary LXF file fixture
  - sample_athletes: Sample athlete data for testing
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
import shutil
import os

# Ensure parent directory is in path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_db_path(tmp_path):
    """
    Create isolated test database path for each test.

    Returns a temporary database file path that will be cleaned up after test.
    """
    db_path = tmp_path / "test_integration.db"
    yield str(db_path)
    # Cleanup happens automatically via tmp_path


@pytest.fixture
def test_db(test_db_path):
    """
    Initialize isolated test database with full schema.

    Returns connection object with proper configuration.
    Closes connection after test.
    """
    from federasyon.db_fed import SCHEMA, migrate_add_selection_columns, get_conn
    from database.db import init_db

    # Temporarily override DB_PATH for this test
    import config
    original_db_path = config.DB_PATH
    from federasyon import db_fed
    original_fed_db_path = db_fed.DB_PATH

    # Point to test database
    config.DB_PATH = test_db_path
    db_fed.DB_PATH = Path(test_db_path)

    try:
        # Initialize database schema
        conn = sqlite3.connect(test_db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")

        # Execute full schema from db_fed.SCHEMA
        conn.executescript(SCHEMA)

        # Add selection columns
        def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, col_type: str):
            existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

        _add_column_if_missing(conn, "fed_results", "selected", "TEXT DEFAULT '-'")
        _add_column_if_missing(conn, "fed_results", "selected_slot", "TEXT DEFAULT '-'")
        _add_column_if_missing(conn, "fed_results", "tied", "BOOLEAN DEFAULT 0")
        _add_column_if_missing(conn, "fed_results", "ranking_key", "TEXT DEFAULT '-'")
        _add_column_if_missing(conn, "fed_athlete_best", "selected", "TEXT DEFAULT '-'")
        _add_column_if_missing(conn, "fed_athlete_best", "selected_slot", "TEXT DEFAULT '-'")
        _add_column_if_missing(conn, "fed_athlete_best", "top3_total", "INTEGER DEFAULT 0")
        _add_column_if_missing(conn, "fed_athlete_best", "ranking_key", "TEXT DEFAULT '-'")
        _add_column_if_missing(conn, "fed_athlete_best", "tied", "BOOLEAN DEFAULT 0")

        conn.commit()
        conn.close()

        yield test_db_path
    finally:
        # Restore original DB_PATH
        config.DB_PATH = original_db_path
        db_fed.DB_PATH = original_fed_db_path


@pytest.fixture
def temp_lxf_file():
    """
    Create temporary LXF file for testing.
    Returns path to temporary file that will be cleaned up.
    """
    with tempfile.NamedTemporaryFile(suffix='.lxf', delete=False) as f:
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def sample_athletes_data():
    """
    Provide sample athlete data for testing.

    Returns list of athlete dicts with required fields:
      name, birth_year, gender, region, city, club, event_scores
    """
    return [
        {
            'name': 'Ahmet Yılmaz',
            'birth_year': 2013,
            'gender': 'M',
            'region': 1,
            'city': 'İstanbul',
            'club': 'Test SK',
            'event_scores': {('Serbest', 50): 7, ('Serbest', 100): 6, ('Sırtüstü', 50): 5},
            'selected': 'TR',
            'selected_slot': 'TR-1',
            'ranking_key': str((-7, -6, -5)),
            'top3_total': 18,
            'tied': False
        },
        {
            'name': 'Fatma Demir',
            'birth_year': 2013,
            'gender': 'F',
            'region': 1,
            'city': 'İstanbul',
            'club': 'Test SK',
            'event_scores': {('Serbest', 50): 5, ('Serbest', 100): 4, ('Sırtüstü', 50): 3},
            'selected': 'BÖLGE',
            'selected_slot': 'B1-1',
            'ranking_key': str((-5, -4, -3)),
            'top3_total': 12,
            'tied': False
        },
        {
            'name': 'Mehmet Kaya',
            'birth_year': 2012,
            'gender': 'M',
            'region': 2,
            'city': 'Ankara',
            'club': 'Central SK',
            'event_scores': {('Serbest', 50): 6, ('Serbest', 100): 5, ('Kelebek', 50): 4},
            'selected': 'BÖLGE',
            'selected_slot': 'B2-1',
            'ranking_key': str((-6, -5, -4)),
            'top3_total': 15,
            'tied': False
        },
        {
            'name': 'Zeynep Çetin',
            'birth_year': 2012,
            'gender': 'F',
            'region': 3,
            'city': 'İzmir',
            'club': 'Ege SK',
            'event_scores': {},
            'selected': 'BARAJ_YOK',
            'selected_slot': '-',
            'ranking_key': str(()),
            'top3_total': 0,
            'tied': False
        },
    ]


@pytest.fixture
def real_test_lxf():
    """
    Path to real test LXF file if available.
    Yields path or None if not available.
    """
    lxf_path = Path(__file__).parent.parent / "data" / "antalya_millitakim_secme_sonuc.lxf"
    if lxf_path.exists():
        yield str(lxf_path)
    else:
        yield None


@pytest.fixture(autouse=True)
def isolate_db_access(test_db, monkeypatch):
    """
    Auto-isolate database access for all tests.
    Patches db module to use test database instead of production.
    Ensures database schema is initialized before each test.
    """
    import config
    from federasyon import db_fed

    # Store original values
    original_config_db = config.DB_PATH
    original_fed_db = db_fed.DB_PATH

    # Patch to test database (test_db fixture already initialized)
    config.DB_PATH = test_db
    db_fed.DB_PATH = Path(test_db)

    monkeypatch.setattr('config.DB_PATH', test_db)
    monkeypatch.setattr('federasyon.db_fed.DB_PATH', Path(test_db))

    yield test_db

    # Restore (though pytest cleanup should handle this)
    config.DB_PATH = original_config_db
    db_fed.DB_PATH = original_fed_db
