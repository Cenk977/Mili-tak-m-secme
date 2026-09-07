# -*- coding: utf-8 -*-
"""
best_scores_sequence / compute_ranking_key: "en fazla 1 adet 50m" kısıtı
YALNIZCA puanlanan ilk 3 yarışa uygulanır. Eşitlik-bozma (4./5./6. yarış)
sırasında sporcunun ikinci/üçüncü 50m yarışı da sayılır.

Gerçek vaka (2012 Erkek TR-10):
  Kaan Balta   — Kelebek50=7, Serbest50=7, Serbest100=9, Serbest200=7
  Doruk E. D.  — Serbest50=6, Serbest100=7, Serbest200=9, Karışık200=7
  İkisi de top3=23. Kaan'ın top4'ü 30 (ikinci 50m sayılır), Doruk'unki 29.
  => Kaan, Doruk'un ÖNÜNDE sıralanmalı.
"""
from federasyon.scorer import best_scores_sequence, compute_ranking_key

KAAN = {
    ("Kelebek", 50): 7,
    ("Serbest", 50): 7,
    ("Serbest", 100): 9,
    ("Serbest", 200): 7,
}
DORUK = {
    ("Serbest", 50): 6,
    ("Serbest", 100): 7,
    ("Serbest", 200): 9,
    ("Karışık", 200): 7,
}


def test_top3_still_caps_at_one_50m():
    # top3 = 9 (100) + 7 (200) + 7 (bir tek 50m) = 23
    assert sum(best_scores_sequence(KAAN)[:3]) == 23


def test_second_50m_counts_as_fourth_race_for_tiebreak():
    seq = best_scores_sequence(KAAN)
    assert seq[:4] == [9, 7, 7, 7]
    assert sum(seq[:4]) == 30


def test_ranking_key_orders_kaan_before_doruk():
    # ranking_key ascending sıralanır; küçük olan (daha iyi) önce gelir
    assert compute_ranking_key(KAAN) < compute_ranking_key(DORUK)


def test_single_50m_athlete_unaffected():
    seq = best_scores_sequence(DORUK)
    assert seq[:4] == [9, 7, 7, 6]
    assert sum(seq[:4]) == 29


def test_two_50m_but_only_two_scoring_races_keeps_top3_capped():
    # 50m=9, 100m=6, 50m=8 -> top3 sadece 9+6 (tek 50m) = 15, ikinci 50m 4. sırada
    scores = {("Serbest", 50): 9, ("Serbest", 100): 6, ("Kelebek", 50): 8}
    seq = best_scores_sequence(scores)
    assert sum(seq[:3]) == 15
    assert 8 in seq[3:]
