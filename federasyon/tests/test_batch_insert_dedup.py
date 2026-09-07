# -*- coding: utf-8 -*-
"""
batch_insert_fed_results: aynı (leg, sporcu, doğum yılı, branş, mesafe) için
LXF'te birden çok RESULT (seri + final) satırı gelir. ux_fed_results UNIQUE
index'i yüzünden düz INSERT ilk çakışmada TÜM transaction'ı geri alıyordu
(temiz DB'ye import = 0 satır). Beklenen: çakışmada en hızlı derece kalır.
"""
from pathlib import Path

import pytest

from federasyon.db_fed import SCHEMA


@pytest.fixture
def fed_db(tmp_path, monkeypatch):
    db_path = tmp_path / "fed.db"
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    import config
    from database import db as db_module
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))
    return str(db_path)


def _row(time_sec, time_txt):
    return {
        "race_leg": "antalya", "athlete_name": "Aliye Pazar", "birth_year": 2013,
        "gender": "F", "region": 3, "city": "Antalya", "club": "Ferdi",
        "stroke": "Serbest", "distance": 800,
        "time_text": time_txt, "time_seconds": time_sec,
    }


def test_duplicate_event_rows_keep_fastest_time(fed_db):
    from database.db import batch_insert_fed_results
    import sqlite3

    # Seri (yavaş) önce, final (hızlı) sonra
    batch_insert_fed_results([_row(600.0, "00:10:00.00"), _row(595.5, "00:09:55.50")])

    conn = sqlite3.connect(fed_db)
    rows = conn.execute(
        "SELECT time_seconds FROM fed_results WHERE athlete_name='Aliye Pazar'"
    ).fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0][0] == 595.5


def test_faster_first_then_slower_still_keeps_fastest(fed_db):
    from database.db import batch_insert_fed_results
    import sqlite3

    batch_insert_fed_results([_row(595.5, "00:09:55.50"), _row(600.0, "00:10:00.00")])

    conn = sqlite3.connect(fed_db)
    rows = conn.execute(
        "SELECT time_seconds FROM fed_results WHERE athlete_name='Aliye Pazar'"
    ).fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0][0] == 595.5
