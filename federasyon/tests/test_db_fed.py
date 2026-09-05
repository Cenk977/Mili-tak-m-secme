import pytest
from federasyon.db_fed import migrate_add_selection_columns, get_conn

def test_migrate_adds_selection_columns_to_fed_results():
    """migrate_add_selection_columns adds selection columns to fed_results"""
    # Call migration
    migrate_add_selection_columns()

    # Verify columns exist by inserting a row with them
    conn = get_conn()
    cursor = conn.cursor()

    # Clean up any existing test data first
    cursor.execute("DELETE FROM fed_results WHERE athlete_name = ?", ('Test Athlete',))
    conn.commit()

    try:
        cursor.execute("""
            INSERT INTO fed_results
            (race_leg, athlete_name, birth_year, gender, stroke, distance, points,
             selected, selected_slot, tied, ranking_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('test', 'Test Athlete', 2013, 'M', 'Serbest', 50, 7, 'TR', 'TR-1', 0, '(-7)'))

        conn.commit()

        # Query back
        cursor.execute("SELECT selected, selected_slot, tied, ranking_key FROM fed_results WHERE athlete_name = ?", ('Test Athlete',))
        row = cursor.fetchone()

        assert row is not None, "Row not inserted"
        assert row[0] == 'TR', f"selected column has wrong value: {row[0]}"
        assert row[1] == 'TR-1', f"selected_slot column has wrong value: {row[1]}"
        assert row[2] == 0, f"tied column has wrong value: {row[2]}"
        assert row[3] == '(-7)', f"ranking_key column has wrong value: {row[3]}"

    finally:
        # Clean up test data — runs even if assertions fail
        cursor.execute("DELETE FROM fed_results WHERE athlete_name = ?", ('Test Athlete',))
        conn.commit()
        conn.close()
