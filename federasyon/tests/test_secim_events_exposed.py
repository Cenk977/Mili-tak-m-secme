# -*- coding: utf-8 -*-
"""Seçim fonksiyonları, karar veren branş-birinciliği yarışlarını public alana yazmalı."""
from federasyon.yildizlar_ranker import (
    select_yildizlar_multinations,
    select_yildizlar_comen_cup_aralik, select_yildizlar_comen_cup_nisan,
    select_yildizlar_central_europe_aralik, select_yildizlar_central_europe_nisan,
)
from federasyon.gencler_ranker import select_multinations_gencler


def _a(aid, gender, by, antalya=None, edirne=None):
    at = antalya or {}
    ed = edirne or {}
    combined = dict(at)
    for k, v in ed.items():
        combined[k] = v
    return {
        "athlete_id": aid, "athlete_name": aid, "gender": gender, "birth_year": by,
        "antalya_events_time": at, "edirne_events_time": ed,
        "combined_events_time": combined,
        "combined_events": {k: 1 for k in combined},
        "antalya_events": {k: 1 for k in at}, "edirne_events": {k: 1 for k in ed},
    }


def test_multinations_events_populated_for_winner_empty_for_loser():
    winner = _a("W", "M", 2012, antalya={("Serbest", 50): "00:00:24.00", ("Kelebek", 100): "00:00:55.00"})
    loser = _a("L", "M", 2012, antalya={("Serbest", 50): "00:00:30.00"})
    out = select_yildizlar_multinations([winner, loser])
    by = {a["athlete_id"]: a for a in out}
    assert set(by["W"]["multinations_events"]) == {("Serbest", 50), ("Kelebek", 100)}
    assert by["L"]["multinations_events"] == []


def test_multinations_events_only_swum_events():
    w = _a("W", "F", 2012, antalya={("Serbest", 50): "00:00:24.00"})
    out = select_yildizlar_multinations([w])
    ev = out[0]["multinations_events"]
    assert all(e in w["antalya_events"] for e in ev)


def test_multinations_gencler_events_populated():
    w = _a("W", "M", 2009, antalya={("Kurbağalama", 100): "00:01:05.00"})
    out = select_multinations_gencler([w])
    assert ("Kurbağalama", 100) in out[0]["multinations_gencler_events"]


def test_comen_events_union_of_aralik_and_nisan_wins():
    # Aralık'ta Serbest 50 birinci, Nisan'da Kelebek 100 birinci
    w = _a("W", "F", 2012,
           antalya={("Serbest", 50): "00:00:24.00"},
           edirne={("Kelebek", 100): "00:00:58.00"})
    other = _a("O", "F", 2012,
               antalya={("Serbest", 50): "00:00:40.00"},
               edirne={("Kelebek", 100): "00:01:30.00"})
    ath = [w, other]
    ath = select_yildizlar_comen_cup_aralik(ath)
    ath = select_yildizlar_comen_cup_nisan(ath)
    by = {a["athlete_id"]: a for a in ath}
    assert set(by["W"]["comen_cup_events"]) == {("Serbest", 50), ("Kelebek", 100)}
    assert by["O"]["comen_cup_events"] == []


def test_central_events_populated():
    w = _a("W", "M", 2012, antalya={("Sırtüstü", 200): "00:02:05.00"})
    o = _a("O", "M", 2012, antalya={("Sırtüstü", 200): "00:03:00.00"})
    ath = select_yildizlar_central_europe_aralik([w, o])
    ath = select_yildizlar_central_europe_nisan(ath)
    by = {a["athlete_id"]: a for a in ath}
    assert ("Sırtüstü", 200) in by["W"]["central_europe_events"]
    assert by["O"]["central_europe_events"] == []
