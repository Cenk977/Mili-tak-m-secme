"""
Database layer for Milli Takım Seçme
SQLite3 backend, UTF-8 encoding
"""

import sqlite3
from pathlib import Path
from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Get SQLite connection with UTF-8 row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database, create tables if missing."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    # Athletes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS athletes (
            athlete_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            firstname TEXT,
            lastname TEXT,
            birthdate TEXT,
            birth_year INTEGER,
            gender TEXT,
            club_id TEXT,
            club_name TEXT,
            city TEXT DEFAULT 'Unknown',
            region INTEGER DEFAULT 0,
            best_score INTEGER,
            selected BOOLEAN DEFAULT 0,
            selection_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Results table (for tracking individual race results)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            athlete_id TEXT NOT NULL,
            event_id TEXT,
            distance INTEGER,
            stroke TEXT,
            time_text TEXT,
            time_seconds REAL,
            place INTEGER,
            points TEXT,
            race_source TEXT,
            FOREIGN KEY (athlete_id) REFERENCES athletes(athlete_id)
        )
    """)

    # Sync log (for tracking Excel imports)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            rows_loaded INTEGER,
            rows_skipped INTEGER,
            notes TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Federation scoring: raw results (used for scoring)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fed_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_leg TEXT NOT NULL,
            race_date TEXT,
            athlete_name TEXT NOT NULL,
            birth_year INTEGER NOT NULL,
            gender TEXT NOT NULL,
            region INTEGER,
            city TEXT,
            club TEXT,
            stroke TEXT NOT NULL,
            distance INTEGER NOT NULL,
            time_text TEXT,
            time_seconds REAL,
            points INTEGER,
            source_pdf_seq INTEGER,
            UNIQUE(race_leg, athlete_name, birth_year, stroke, distance)
        )
    """)

    # Federation scoring: best per event (materialized from fed_results)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fed_athlete_best (
            athlete_name TEXT NOT NULL,
            birth_year INTEGER NOT NULL,
            gender TEXT NOT NULL,
            region INTEGER,
            city TEXT,
            club TEXT,
            stroke TEXT NOT NULL,
            distance INTEGER NOT NULL,
            best_points INTEGER,
            best_time_sec REAL,
            best_time_txt TEXT,
            best_leg TEXT,
            PRIMARY KEY(athlete_name, birth_year, stroke, distance)
        )
    """)

    conn.commit()
    conn.close()


def insert_athlete(athlete_dict: dict) -> bool:
    """Insert or replace athlete record."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO athletes (
                athlete_id, name, firstname, lastname, birthdate, birth_year,
                gender, club_id, club_name, city, region, best_score,
                selected, selection_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            athlete_dict.get('athlete_id'),
            f"{athlete_dict.get('firstname', '')} {athlete_dict.get('lastname', '')}".strip(),
            athlete_dict.get('firstname'),
            athlete_dict.get('lastname'),
            athlete_dict.get('birthdate'),
            athlete_dict.get('birth_year'),
            athlete_dict.get('gender'),
            athlete_dict.get('club_id'),
            athlete_dict.get('club_name', 'Unknown'),
            athlete_dict.get('city', 'Unknown'),
            athlete_dict.get('region', 0),
            athlete_dict.get('best_score'),
            athlete_dict.get('selected', 0),
            athlete_dict.get('selection_type'),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting athlete: {e}")
        return False
    finally:
        conn.close()


def insert_result(result_dict: dict) -> bool:
    """Insert race result."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO results (
                athlete_id, event_id, distance, stroke, time_text,
                time_seconds, place, points, race_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_dict.get('athlete_id'),
            result_dict.get('event_id'),
            result_dict.get('distance'),
            result_dict.get('stroke'),
            result_dict.get('time_text'),
            result_dict.get('time_seconds'),
            result_dict.get('place'),
            result_dict.get('points'),
            result_dict.get('race_source', 'unknown'),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting result: {e}")
        return False
    finally:
        conn.close()


def get_athletes_by_filter(birth_year: int = None, gender: str = None) -> list:
    """
    Get athletes filtered by birth_year and/or gender.
    Returns list of dicts with all columns.
    """
    conn = get_connection()
    query = "SELECT * FROM athletes WHERE 1=1"
    params = []

    if birth_year:
        query += " AND birth_year = ?"
        params.append(birth_year)

    if gender:
        query += " AND gender = ?"
        params.append(gender)

    query += " ORDER BY best_score DESC"

    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_all_athletes() -> list:
    """Get all athletes from database."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM athletes ORDER BY best_score DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_athlete_ranking(athlete_id: str, score: int, selected: bool, selection_type: str = None) -> bool:
    """Update athlete's score and selection status."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE athletes
            SET best_score = ?, selected = ?, selection_type = ?, updated_at = CURRENT_TIMESTAMP
            WHERE athlete_id = ?
        """, (score, selected, selection_type, athlete_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating athlete: {e}")
        return False
    finally:
        conn.close()


def clear_athletes() -> bool:
    """Delete all athlete records (for re-import)."""
    conn = get_connection()
    try:
        # Delete results first (has foreign key to athletes)
        conn.execute("DELETE FROM results")
        # Then delete athletes
        conn.execute("DELETE FROM athletes")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing athletes: {e}")
        return False
    finally:
        conn.close()


def get_missing_clubs_from_db() -> list:
    """Get list of unique clubs with region=0 (unmapped)."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT club_name FROM athletes
            WHERE region = 0
            ORDER BY club_name
        """)
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def insert_fed_result(result_dict: dict) -> bool:
    """Insert federation result into fed_results table."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO fed_results (
                race_leg, race_date, athlete_name, birth_year, gender,
                region, city, club, stroke, distance,
                time_text, time_seconds, points, source_pdf_seq
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_dict.get('race_leg', 'antalya'),
            result_dict.get('race_date'),
            result_dict.get('athlete_name'),
            result_dict.get('birth_year'),
            result_dict.get('gender'),
            result_dict.get('region', 0),
            result_dict.get('city'),
            result_dict.get('club'),
            result_dict.get('stroke'),
            result_dict.get('distance'),
            result_dict.get('time_text'),
            result_dict.get('time_seconds'),
            result_dict.get('points'),
            result_dict.get('source_pdf_seq'),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting fed_result: {e}")
        return False
    finally:
        conn.close()


def insert_fed_athlete_best(best_dict: dict) -> bool:
    """Insert or update federation athlete best into fed_athlete_best table."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO fed_athlete_best (
                athlete_name, birth_year, gender, region, city, club,
                stroke, distance, best_points, best_time_sec, best_time_txt, best_leg
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            best_dict.get('athlete_name'),
            best_dict.get('birth_year'),
            best_dict.get('gender'),
            best_dict.get('region', 0),
            best_dict.get('city'),
            best_dict.get('club'),
            best_dict.get('stroke'),
            best_dict.get('distance'),
            best_dict.get('best_points'),
            best_dict.get('best_time_sec'),
            best_dict.get('best_time_txt'),
            best_dict.get('best_leg'),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting fed_athlete_best: {e}")
        return False
    finally:
        conn.close()


def get_fed_athlete_best(birth_year: int = None, gender: str = None) -> list:
    """Get fed_athlete_best filtered by birth_year and/or gender."""
    conn = get_connection()
    query = "SELECT * FROM fed_athlete_best WHERE 1=1"
    params = []

    if birth_year:
        query += " AND birth_year = ?"
        params.append(birth_year)

    if gender:
        query += " AND gender = ?"
        params.append(gender)

    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_fed_results(race_leg: str = None) -> list:
    """Get fed_results, optionally filtered by race_leg."""
    conn = get_connection()
    query = "SELECT * FROM fed_results WHERE 1=1"
    params = []

    if race_leg:
        query += " AND race_leg = ?"
        params.append(race_leg)

    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def clear_fed_tables() -> bool:
    """Clear fed_results and fed_athlete_best tables (for re-import)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM fed_results")
        conn.execute("DELETE FROM fed_athlete_best")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing fed tables: {e}")
        return False
    finally:
        conn.close()
