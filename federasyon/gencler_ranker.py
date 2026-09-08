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


def select_avrupa_gencler(athletes):
    """Avrupa Gençler (2008-2012): kendi branş/mesafesindeki SPORCU BARAJI'nı
    (eşit dahil) geçen her sporcu kesin. Kota yok. Veri: combined_events_time
    (geniş pencere → en iyi derece; elimizde yalnız Aralık+Nisan → kısmi)."""
    lo, hi = AVRUPA_GENCLER_AGES
    for athlete in athletes:
        by = athlete.get('birth_year')
        in_age = by is not None and lo <= by <= hi
        gender = athlete.get('gender')
        ets = athlete.get('combined_events_time', {})
        qual, coach = [], False
        if in_age:
            for (s, d) in athlete.get('combined_events', {}):
                t = ets.get((s, d))
                if check_baraj(AVRUPA_GENCLER_SPORCU, s, d, gender, t):
                    qual.append((s, d))
                if check_baraj(AVRUPA_GENCLER_ANTRENOR, s, d, gender, t):
                    coach = True
        athlete['avrupa_gencler_events'] = qual
        athlete['selected_avrupa_gencler'] = len(qual) > 0
        athlete['coach_called_avrupa_gencler'] = coach

    elig = [a for a in athletes
            if a.get('birth_year') is not None and lo <= a['birth_year'] <= hi]
    sel_ids = {a['athlete_id'] for a in elig if a['selected_avrupa_gencler']}
    fem = [a for a in elig if a.get('gender') == 'F']
    mal = [a for a in elig if a.get('gender') == 'M']
    relay_ids = (_relay_candidate_ids(fem, 'combined_events_time', sel_ids) |
                 _relay_candidate_ids(mal, 'combined_events_time', sel_ids))
    for athlete in athletes:
        athlete['candidate_relay_avrupa_gencler'] = athlete.get('athlete_id') in relay_ids
    return athletes


def select_all_gencler(athletes):
    """Tüm Gençler seçimlerini uygula (additive)."""
    athletes = select_multinations_gencler(athletes)
    athletes = select_avrupa_gencler(athletes)
    return athletes
