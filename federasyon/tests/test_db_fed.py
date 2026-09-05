import pytest
from federasyon.db_fed import (
    migrate_add_selection_columns,
    get_conn,
    upsert_fed_results,
    update_athlete_selection,
    get_selected_athletes,
)

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


def test_upsert_fed_results_inserts_event_results():
    """upsert_fed_results inserts each event as a separate row"""
    migrate_add_selection_columns()

    athlete = {
        'name': 'Ahmet Test',
        'birth_year': 2013,
        'gender': 'M',
        'region': 1,
        'city': 'İstanbul',
        'club': 'Test SK',
        'event_scores': {
            ('Serbest', 50): 7,
            ('Serbest', 100): 5,
            ('Sırtüstü', 50): 6
        },
        'top3_total': 18,
        'selected': 'TR',
        'selected_slot': 'TR-1',
        'ranking_key': '(-18, -23)',
        'tied': False
    }

    upsert_fed_results(athlete, race_leg='milli_takim')

    # Verify 3 rows inserted (one per event)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM fed_results WHERE athlete_name = ? AND race_leg = ?",
        ('Ahmet Test', 'milli_takim')
    )
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 3, f"Expected 3 results, got {count}"

    # Cleanup
    conn = get_conn()
    conn.execute("DELETE FROM fed_results WHERE athlete_name = ?", ('Ahmet Test',))
    conn.commit()
    conn.close()


def test_update_athlete_selection_updates_slot():
    """update_athlete_selection updates selected/selected_slot in fed_athlete_best"""
    migrate_add_selection_columns()

    athlete = {
        'name': 'Fatma Test',
        'birth_year': 2013,
        'gender': 'F',
        'region': 2,
        'city': 'Bursa',
        'club': 'Bursa SK',
        'event_scores': {('Serbest', 50): 7},
        'selected': 'BÖLGE',
        'selected_slot': 'B2-1'
    }

    upsert_fed_results(athlete, race_leg='milli_takim')
    update_athlete_selection(athlete)

    # Query fed_athlete_best
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT selected, selected_slot FROM fed_athlete_best WHERE athlete_name = ? AND birth_year = ?",
        ('Fatma Test', 2013)
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None, "Athlete not in fed_athlete_best"
    assert row[0] == 'BÖLGE', f"Wrong selected value: {row[0]}"
    assert row[1] == 'B2-1', f"Wrong slot: {row[1]}"

    # Cleanup
    conn = get_conn()
    conn.execute("DELETE FROM fed_results WHERE athlete_name = ?", ('Fatma Test',))
    conn.execute("DELETE FROM fed_athlete_best WHERE athlete_name = ?", ('Fatma Test',))
    conn.commit()
    conn.close()


def test_get_selected_athletes_filters_by_birth_year_and_status():
    """get_selected_athletes queries by birth_year and selected status"""
    migrate_add_selection_columns()

    # Setup: insert 3 test athletes (2 TR, 1 BÖLGE)
    for i in range(3):
        athlete = {
            'name': f'Athlete {i}',
            'birth_year': 2013,
            'gender': 'M' if i % 2 == 0 else 'F',
            'region': 1 if i == 0 else 2,
            'city': 'İstanbul' if i == 0 else 'Bursa',
            'club': 'Test SK',
            'event_scores': {('Serbest', 50): 7},
            'selected': 'TR' if i < 2 else 'BÖLGE',
            'selected_slot': f'TR-{i}' if i < 2 else 'B2-1'
        }
        upsert_fed_results(athlete, race_leg='milli_takim')
        update_athlete_selection(athlete)

    # Query TR only
    tr_selected = get_selected_athletes(birth_year=2013, selected='TR')
    assert len(tr_selected) == 2, f"Expected 2 TR, got {len(tr_selected)}"

    # Query BÖLGE only
    bolge_selected = get_selected_athletes(birth_year=2013, selected='BÖLGE')
    assert len(bolge_selected) == 1, f"Expected 1 BÖLGE, got {len(bolge_selected)}"

    # Cleanup
    for i in range(3):
        conn = get_conn()
        conn.execute("DELETE FROM fed_results WHERE athlete_name = ?", (f'Athlete {i}',))
        conn.execute("DELETE FROM fed_athlete_best WHERE athlete_name = ?", (f'Athlete {i}',))
        conn.commit()
        conn.close()
