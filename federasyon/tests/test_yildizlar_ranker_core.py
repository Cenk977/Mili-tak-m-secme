# -*- coding: utf-8 -*-
from federasyon.yildizlar_ranker import (
    _select_branch_winners_core, YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM,
)


def _a(aid, gender, et):
    return {"athlete_id": aid, "athlete_name": aid, "gender": gender,
            "birth_year": 2012, "antalya_events_time": et,
            "combined_events": {}, "combined_events_time": {}}


def test_core_returns_winner_as_selected():
    males = [
        _a("M1", "M", {("Serbest", 50): "00:00:25.00"}),   # kazanır
        _a("M2", "M", {("Serbest", 50): "00:00:26.00"}),   # 2.
    ]
    sel, cand, relay = _select_branch_winners_core(
        males, 10, "antalya_events_time",
        YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)
    assert "M1" in sel
    assert "M1" not in cand


def test_core_over_quota_trims_by_depth():
    events = list(YILDIZLAR_MALE_PROGRAM)[:11]
    males = []
    for i, ev in enumerate(events):
        et = {ev: "00:00:25.00"}
        if i < 10:
            et[events[(i + 1) % len(events)]] = "00:00:25.50"  # derinlik (2.lik)
        males.append(_a(f"W{i+1}", "M", et))
    sel, cand, relay = _select_branch_winners_core(
        males, 10, "antalya_events_time",
        YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)
    assert len(sel) == 10
    assert "W11" in cand  # derinliksiz birinci kırpıldı


def test_core_sets_first_events_on_winners():
    from federasyon.yildizlar_ranker import _select_branch_winners_core, YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM
    males = [
        {"athlete_id": "M1", "athlete_name": "M1", "gender": "M", "birth_year": 2012,
         "antalya_events_time": {("Serbest", 50): "00:00:25.00"}},
        {"athlete_id": "M2", "athlete_name": "M2", "gender": "M", "birth_year": 2012,
         "antalya_events_time": {("Serbest", 50): "00:00:26.00"}},
    ]
    _select_branch_winners_core(males, 10, "antalya_events_time",
                                YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)
    assert ("Serbest", 50) in males[0]["_first_events"]
