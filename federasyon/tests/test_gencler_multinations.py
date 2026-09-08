# -*- coding: utf-8 -*-
from federasyon.gencler_ranker import select_multinations_gencler, MULTI_GENCLER_QUOTA
from federasyon.yildizlar_ranker import YILDIZLAR_MALE_PROGRAM, select_yildizlar_multinations


def _a(aid, gender, by, et):
    return {"athlete_id": aid, "athlete_name": aid, "gender": gender,
            "birth_year": by, "antalya_events_time": et,
            "combined_events": {}, "combined_events_time": {}}


def test_only_2008_2010_eligible():
    ath = [
        _a("young", "M", 2011, {("Serbest", 50): "00:00:25.00"}),
        _a("ok",    "M", 2009, {("Serbest", 100): "00:00:55.00"}),
        _a("old",   "M", 2007, {("Kelebek", 50): "00:00:25.00"}),
    ]
    out = select_multinations_gencler(ath)
    by = {a["athlete_id"]: a for a in out}
    assert by["ok"]["selected_multinations_gencler"] is True
    assert by["young"]["selected_multinations_gencler"] is False
    assert by["old"]["selected_multinations_gencler"] is False


def test_madde5_trim_to_quota_by_depth():
    events = list(YILDIZLAR_MALE_PROGRAM)[:11]
    ath = []
    for i, ev in enumerate(events):
        et = {ev: "00:00:25.00"}
        if i < 10:
            et[events[(i + 1) % len(events)]] = "00:00:25.50"
        ath.append(_a(f"W{i+1}", "M", 2009, et))
    out = select_multinations_gencler(ath)
    by = {a["athlete_id"]: a for a in out}
    sel = [a for a in out if a["selected_multinations_gencler"]]
    assert len(sel) == MULTI_GENCLER_QUOTA
    assert by["W11"]["candidate_multinations_gencler"] is True
    assert by["W11"]["selected_multinations_gencler"] is False


def test_does_not_touch_yildizlar_fields():
    ath = [_a("x", "F", 2009, {("Serbest", 50): "00:00:25.00"})]
    select_multinations_gencler(ath)
    assert "selected_yildiz_multinations" not in ath[0]


def test_yildizlar_multinations_unaffected_by_gencler_call():
    ath = [
        {"athlete_id": "y1", "athlete_name": "y1", "gender": "F", "birth_year": 2012,
         "antalya_events_time": {("Serbest", 50): "00:00:25.00"},
         "combined_events": {}, "combined_events_time": {}},
    ]
    select_multinations_gencler(ath)
    select_yildizlar_multinations(ath)
    assert ath[0]["selected_yildiz_multinations"] is True
