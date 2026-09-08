# -*- coding: utf-8 -*-
from federasyon.gencler_ranker import select_avrupa_gencler, select_all_gencler


def _a(aid, gender, by, cet):
    return {"athlete_id": aid, "athlete_name": aid, "gender": gender,
            "birth_year": by,
            "combined_events": {k: 1 for k in cet},
            "combined_events_time": cet,
            "antalya_events_time": {}}


def test_meeting_sporcu_baraj_selects():
    # K 100 Serbest sporcu barajı = 56.02
    ath = [_a("q", "F", 2011, {("Serbest", 100): "00:00:56.02"})]  # eşit → geçer
    out = select_avrupa_gencler(ath)
    assert out[0]["selected_avrupa_gencler"] is True
    assert ("Serbest", 100) in out[0]["avrupa_gencler_events"]


def test_missing_baraj_by_001_not_selected():
    ath = [_a("slow", "F", 2011, {("Serbest", 100): "00:00:56.03"})]
    out = select_avrupa_gencler(ath)
    assert out[0]["selected_avrupa_gencler"] is False
    assert out[0]["avrupa_gencler_events"] == []


def test_antrenor_baraj_implies_sporcu_baraj():
    # E 50 Kelebek: antrenör 24.10, sporcu 24.25. 24.05 ikisini de geçer.
    ath = [_a("elite", "M", 2009, {("Kelebek", 50): "00:00:24.05"})]
    out = select_avrupa_gencler(ath)
    assert out[0]["selected_avrupa_gencler"] is True
    assert out[0]["coach_called_avrupa_gencler"] is True


def test_age_window_2008_2012():
    ath = [
        _a("in1", "F", 2008, {("Serbest", 50): "00:00:25.00"}),
        _a("in2", "F", 2012, {("Serbest", 50): "00:00:25.00"}),
        _a("out_young", "F", 2013, {("Serbest", 50): "00:00:25.00"}),
        _a("out_old", "F", 2007, {("Serbest", 50): "00:00:25.00"}),
    ]
    out = select_avrupa_gencler(ath)
    by = {a["athlete_id"]: a for a in out}
    assert by["in1"]["selected_avrupa_gencler"] is True
    assert by["in2"]["selected_avrupa_gencler"] is True
    assert by["out_young"]["selected_avrupa_gencler"] is False
    assert by["out_old"]["selected_avrupa_gencler"] is False


def test_no_quota_trim_all_qualifiers_selected():
    ath = [_a(f"s{i}", "F", 2011, {("Serbest", 50): "00:00:25.00"}) for i in range(15)]
    out = select_avrupa_gencler(ath)
    assert sum(1 for a in out if a["selected_avrupa_gencler"]) == 15


def test_select_all_gencler_sets_both_competitions():
    ath = [{"athlete_id": "z", "athlete_name": "z", "gender": "F", "birth_year": 2009,
            "antalya_events_time": {("Serbest", 50): "00:00:25.00"},
            "combined_events": {("Serbest", 50): 1},
            "combined_events_time": {("Serbest", 50): "00:00:25.00"}}]
    out = select_all_gencler(ath)
    assert "selected_multinations_gencler" in out[0]
    assert "selected_avrupa_gencler" in out[0]
