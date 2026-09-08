# -*- coding: utf-8 -*-
"""
2026 Gençler Milli Takım seçimleri (Multinations Gençler + Avrupa Gençler).
Additive: Yıldızlar / Federasyon Karması çıktılarına dokunmaz, çapraz dışlama yok.
"""
from federasyon.yildizlar_ranker import (
    _select_branch_winners_core, parse_time,
    YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM,
    _relay_candidate_ids,
)
from federasyon.gencler_barajlari import (
    MULTI_GENCLER_ANTRENOR, AVRUPA_GENCLER_SPORCU, AVRUPA_GENCLER_ANTRENOR,
    check_baraj, passes_any,
)

MULTI_GENCLER_QUOTA = 10
MULTI_GENCLER_AGES = (2008, 2010)
AVRUPA_GENCLER_AGES = (2008, 2012)


def select_multinations_gencler(athletes):
    """Multinations Gençler (2008-2010): 20-22 Aralık seçme (antalya_events_time),
    branş birincisi + kota 10/10 + madde 4/5. Multi Yıldızlar ile aynı çekirdek."""
    lo, hi = MULTI_GENCLER_AGES
    eligible = [a for a in athletes
                if a.get('birth_year') is not None and lo <= a['birth_year'] <= hi]
    sel_ids, cand_ids, relay_ids = _select_branch_winners_core(
        eligible, MULTI_GENCLER_QUOTA, 'antalya_events_time',
        YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)

    for athlete in athletes:
        aid = athlete.get('athlete_id')
        athlete['candidate_relay_multinations_gencler'] = aid in relay_ids
        if aid in sel_ids:
            athlete['selected_multinations_gencler'] = True
            athlete['candidate_multinations_gencler'] = False
            athlete['coach_called_multinations_gencler'] = passes_any(
                MULTI_GENCLER_ANTRENOR, athlete, 'antalya_events_time')
        elif aid in cand_ids:
            athlete['selected_multinations_gencler'] = False
            athlete['candidate_multinations_gencler'] = True
            athlete['coach_called_multinations_gencler'] = False
        else:
            athlete['selected_multinations_gencler'] = False
            athlete['candidate_multinations_gencler'] = False
            athlete['coach_called_multinations_gencler'] = False
        for k in ('_first', '_second', '_third'):
            athlete.pop(k, None)
    return athletes
