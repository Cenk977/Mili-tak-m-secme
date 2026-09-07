# -*- coding: utf-8 -*-
"""
PDF madde 5 (Multinations / Central European): branş birincilerinin sayısı
kota'dan (10F+10M / 12F+12M) fazla olduğunda kadro, sporcuların ikincilik
ve üçüncülüklerine bakılarak kotaya indirilir.

Bu deterministik bir kural (takdir değil): (1.lik, 2.lik, 3.lük) sayısına
göre azalan sırala, ilk `kota` kişi kesin; gerisi aday olur (otomatik
seçilmez, Federasyon Karması'ndan dışlanmaz).

Gerçek vaka: Talya Tok 2011-2013 K'da yalnızca 50m Kelebek branş birincisi,
hiç 2./3.lüğü yok → 11 birinci içinde en zayıf derinlik → kesilir. Resmi
2026 Multinations kadrosunda da yok.
"""
from federasyon.yildizlar_ranker import (
    select_yildizlar_multinations,
    MULTINATIONS_QUOTA,
)

FLY = "Kelebek"
BACK = "Sırtüstü"
BREAST = "Kurbağalama"
FREE = "Serbest"

# 16 kişilik (birbirinden bağımsız) branş dağıtımı için yeterli program eventi
_EVENTS = [
    (FREE, 50), (FREE, 100), (FREE, 200), (FREE, 400), (FREE, 1500),
    (BACK, 50), (BACK, 100), (BACK, 200),
    (BREAST, 50), (BREAST, 100), (BREAST, 200),
    (FLY, 50), (FLY, 100), (FLY, 200),
    ("Karışık", 200), ("Karışık", 400),
]


def _athlete(aid, events_time):
    return {
        "athlete_id": aid,
        "athlete_name": aid,
        "gender": "M",
        "birth_year": 2012,
        "antalya_events_time": events_time,
        "combined_events": {},
        "combined_events_time": {},
    }


def test_over_quota_winners_trimmed_to_quota_by_depth():
    quota = MULTINATIONS_QUOTA  # 10
    athletes = []

    # quota+1 = 11 branş birincisi. W1..W10 kendi eventini kazanır VE
    # ayrıca komşu eventte 2.lik alır (derinlik). W11 sadece 1 event kazanır,
    # hiç 2./3.lüğü yok — kesilecek olan.
    for i in range(quota + 1):
        win_ev = _EVENTS[i]
        et = {win_ev: "00:00:25.00"}
        if i < quota:
            second_ev = _EVENTS[(i + 1) % len(_EVENTS)]
            et[second_ev] = "00:00:25.50"  # o eventte biri 25.00 yüzecek -> bu 2.
        athletes.append(_athlete(f"W{i+1}", et))

    # Her eventte bir "kazanan" zaten var (yukarıdaki W'ler). W1..W10'un
    # 2.lik aldığı eventlerde asıl kazanan komşu W. W11'in kazandığı event
    # başkası tarafından yüzülmediğinden onun 1.liği net.

    result = select_yildizlar_multinations(list(athletes))
    by = {a["athlete_id"]: a for a in result}

    selected = [a["athlete_id"] for a in result if a["selected_yildiz_multinations"]]
    assert len(selected) == quota, f"kotaya inmeli, {len(selected)} seçildi"

    # En zayıf derinlikli birinci (W11: 1.lik=1, 2.lik=0, 3.lük=0) kesilmeli
    assert by["W11"]["selected_yildiz_multinations"] is False
    assert by["W11"]["candidate_yildiz_multinations"] is True

    # Derinlikli birinciler kesin kalmalı
    assert by["W1"]["selected_yildiz_multinations"] is True


def test_exactly_quota_winners_all_kesin():
    quota = MULTINATIONS_QUOTA
    athletes = [_athlete(f"W{i+1}", {_EVENTS[i]: "00:00:25.00"}) for i in range(quota)]
    result = select_yildizlar_multinations(list(athletes))
    selected = [a for a in result if a["selected_yildiz_multinations"]]
    assert len(selected) == quota
