# -*- coding: utf-8 -*-
from federasyon.gencler_barajlari import (
    MULTI_GENCLER_ANTRENOR, AVRUPA_GENCLER_SPORCU, AVRUPA_GENCLER_ANTRENOR,
    check_baraj, passes_any,
)

STROKES = ["Serbest", "Sırtüstü", "Kurbağalama", "Kelebek", "Karışık"]


def test_all_tables_have_17_event_rows():
    for tbl in (MULTI_GENCLER_ANTRENOR, AVRUPA_GENCLER_SPORCU, AVRUPA_GENCLER_ANTRENOR):
        assert len(tbl) == 17
        for (stroke, dist), row in tbl.items():
            assert stroke in STROKES
            assert set(row.keys()) == {"M", "F"}


def test_check_baraj_equal_time_passes():
    # Avrupa sporcu K 50 Serbest = 25.81
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", "00:00:25.81") is True


def test_check_baraj_faster_passes_slower_fails():
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", "00:00:25.80") is True
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", "00:00:25.82") is False


def test_check_baraj_missing_event_or_gender_or_time():
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 999, "F", "00:00:25.00") is False
    # Erkek 800 Serbest MULTI_GENCLER_ANTRENOR'da None
    assert check_baraj(MULTI_GENCLER_ANTRENOR, "Serbest", 800, "M", "00:08:00.00") is False
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", None) is False
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", "-") is False


def test_mmss_and_hhmmss_formats_parse():
    # 1:02.09 (K 100 Sırtüstü antrenör) vs athlete "00:01:02.09"
    assert check_baraj(AVRUPA_GENCLER_ANTRENOR, "Sırtüstü", 100, "F", "00:01:02.09") is True
    assert check_baraj(AVRUPA_GENCLER_ANTRENOR, "Sırtüstü", 100, "F", "00:01:02.10") is False


def test_passes_any_true_when_one_event_passes():
    athlete = {
        "gender": "F",
        "combined_events": {("Serbest", 50): 9, ("Kelebek", 100): 3},
        "combined_events_time": {("Serbest", 50): "00:00:25.00",  # geçer
                                 ("Kelebek", 100): "00:01:30.00"},  # geçmez
    }
    assert passes_any(AVRUPA_GENCLER_SPORCU, athlete) is True


def test_passes_any_false_when_none_pass():
    athlete = {
        "gender": "F",
        "combined_events": {("Serbest", 50): 1},
        "combined_events_time": {("Serbest", 50): "00:00:40.00"},
    }
    assert passes_any(AVRUPA_GENCLER_SPORCU, athlete) is False
