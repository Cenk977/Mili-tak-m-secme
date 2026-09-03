"""
Yıldızlar (Youth) National Team Selection Rankings - COMPLETE REWRITE

Handles three competitions (per TYF 2026-YILDIZLAR-MILLI-TAKIM-SECILME-KRITERLERI):
- Multinations Yıldızlar: Top 10F + 10M (by 1st, 2nd, 3rd place count)
- Comen Cup Yıldızlar: All branş birincileri in COMEN program
  + 4+ birincilik rule: add 2nd place for 5th+ branş
- Central European Meet Yıldızlar: Top 12F + 12M (by 1st, 2nd, 3rd place count)
  + 4+ birincilik rule: add 2nd place for 5th+ branş
"""

import logging
from federasyon.yildizlar_multinations_barajlari import check_antrenor_baraj as check_multi_baraj
from federasyon.yildizlar_comen_cup_barajlari import check_antrenor_baraj as check_comen_baraj
from federasyon.yildizlar_central_europe_barajlari import check_antrenor_baraj as check_central_baraj

logger = logging.getLogger(__name__)

# Competition-specific event programs
COMEN_CUP_FEMALE_PROGRAM = {
    ('Serbest', 100), ('Serbest', 400), ('Serbest', 800),
    ('Sırtüstü', 50), ('Sırtüstü', 100), ('Sırtüstü', 200),
    ('Kurbağalama', 50), ('Kurbağalama', 100), ('Kurbağalama', 200),
    ('Kelebek', 50), ('Kelebek', 100), ('Kelebek', 200),
    ('Karışık', 200), ('Karışık', 400),
    ('4x50m Serbest',), ('4x100m Serbest',), ('4x50m Karışık',), ('4x100m Karışık',),
    ('4x200m Serbest',),
}

COMEN_CUP_MALE_PROGRAM = {
    ('Serbest', 50), ('Serbest', 100), ('Serbest', 400),
    ('Sırtüstü', 50), ('Sırtüstü', 100), ('Sırtüstü', 200),
    ('Kurbağalama', 50), ('Kurbağalama', 100), ('Kurbağalama', 200),
    ('Kelebek', 50), ('Kelebek', 100), ('Kelebek', 200),
    ('Karışık', 200), ('Karışık', 400),
    ('4x50m Serbest',), ('4x100m Serbest',), ('4x50m Karışık',), ('4x100m Karışık',),
    ('4x200m Serbest',),
}

# CENTRAL: Add all 50m, keep 1500m for males, remove 800m for males
CENTRAL_FEMALE_PROGRAM = COMEN_CUP_FEMALE_PROGRAM.copy()
CENTRAL_FEMALE_PROGRAM.update({
    ('Serbest', 50), ('Sırtüstü', 50), ('Kurbağalama', 50), ('Kelebek', 50),
})

CENTRAL_MALE_PROGRAM = COMEN_CUP_MALE_PROGRAM.copy()
CENTRAL_MALE_PROGRAM.update({('Serbest', 1500)})
CENTRAL_MALE_PROGRAM.discard(('Serbest', 800))

def parse_time(time_str: str) -> float:
    """Parse time string to seconds."""
    if not time_str or time_str == '-':
        return float('inf')
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return float(time_str)
    except (ValueError, TypeError):
        return float('inf')

def get_first_place_events(athlete_id: int, eligible_athletes: list, event_times_key: str, program_filter: set = None) -> list:
    """Get event_keys where athlete placed 1st (filtered by program if provided)."""
    first_place_events = []
    athlete = next((a for a in eligible_athletes if a.get('athlete_id') == athlete_id), None)
    if not athlete:
        return first_place_events

    all_events = set()
    for a in eligible_athletes:
        for event_key in a.get(event_times_key, {}).keys():
            if program_filter is None or event_key in program_filter:
                all_events.add(event_key)

    for event_key in all_events:
        best_time = float('inf')
        best_athlete_id = None
        for a in eligible_athletes:
            time_str = a.get(event_times_key, {}).get(event_key)
            time_sec = parse_time(time_str)
            if time_sec < best_time:
                best_time = time_sec
                best_athlete_id = a.get('athlete_id')
        if best_athlete_id == athlete_id:
            first_place_events.append(event_key)

    return first_place_events

def count_events_by_rank(athlete_id: int, eligible_athletes: list, event_times_key: str, rank: int, program_filter: set = None) -> int:
    """Count events where athlete placed at specific rank."""
    if not eligible_athletes:
        return 0
    athlete = next((a for a in eligible_athletes if a.get('athlete_id') == athlete_id), None)
    if not athlete:
        return 0

    all_events = set()
    for a in eligible_athletes:
        for event_key in a.get(event_times_key, {}).keys():
            if program_filter is None or event_key in program_filter:
                all_events.add(event_key)

    rank_count = 0
    for event_key in all_events:
        times_list = []
        for a in eligible_athletes:
            time_str = a.get(event_times_key, {}).get(event_key)
            time_sec = parse_time(time_str)
            if time_sec != float('inf'):
                times_list.append({'athlete_id': a.get('athlete_id'), 'time_sec': time_sec})

        if len(times_list) >= rank:
            times_list.sort(key=lambda x: x['time_sec'])
            if times_list[rank - 1]['athlete_id'] == athlete_id:
                rank_count += 1

    return rank_count

def get_second_place_athlete(event_key: tuple, eligible_athletes: list, event_times_key: str = 'combined_events_time'):
    """Get 2nd place athlete for specific event."""
    times_list = []
    for a in eligible_athletes:
        time_str = a.get(event_times_key, {}).get(event_key)
        time_sec = parse_time(time_str)
        if time_sec != float('inf'):
            times_list.append({
                'athlete_id': a.get('athlete_id'),
                'time_sec': time_sec,
                'time_text': time_str,
                'athlete_name': a.get('athlete_name')
            })

    if len(times_list) < 2:
        return None
    times_list.sort(key=lambda x: x['time_sec'])
    return times_list[1]

def count_first_places(athlete_id: int, eligible_athletes: list, event_times_key: str = 'combined_events_time') -> int:
    """Count 1st places (all events)."""
    if not eligible_athletes:
        return 0
    athlete = next((a for a in eligible_athletes if a.get('athlete_id') == athlete_id), None)
    if not athlete:
        return 0

    all_events = set()
    for a in eligible_athletes:
        for event_key in a.get(event_times_key, {}).keys():
            all_events.add(event_key)

    first_place_count = 0
    for event_key in all_events:
        best_time = float('inf')
        best_athlete_id = None
        for a in eligible_athletes:
            time_str = a.get(event_times_key, {}).get(event_key)
            time_sec = parse_time(time_str)
            if time_sec < best_time:
                best_time = time_sec
                best_athlete_id = a.get('athlete_id')
        if best_athlete_id == athlete_id:
            first_place_count += 1

    return first_place_count

def select_yildizlar_multinations(athletes):
    """Multinations: Top 10F+10M. Rules: if <10 1st places, add 2nd/3rd. If ≥10, rank by (1st,2nd,3rd)."""
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']

    for athlete_list in [females, males]:
        for athlete in athlete_list:
            aid = athlete.get('athlete_id')
            athlete['_first'] = count_first_places(aid, athlete_list, 'antalya_events_time')
            athlete['_second'] = count_events_by_rank(aid, athlete_list, 'antalya_events_time', 2)
            athlete['_third'] = count_events_by_rank(aid, athlete_list, 'antalya_events_time', 3)

    def select_group(group):
        with_first = [a for a in group if a.get('_first', 0) > 0]
        without_first = [a for a in group if a.get('_first', 0) == 0]
        if len(with_first) < 10:
            without_first.sort(key=lambda x: (x.get('_second', 0), x.get('_third', 0)), reverse=True)
            return with_first + without_first[:10 - len(with_first)]
        else:
            with_first.sort(key=lambda x: (x.get('_first', 0), x.get('_second', 0), x.get('_third', 0)), reverse=True)
            return with_first[:10]

    sel_f = select_group(females)
    sel_m = select_group(males)
    sel_ids = {a.get('athlete_id') for a in sel_f + sel_m}

    for athlete in athletes:
        if athlete.get('athlete_id') in sel_ids:
            athlete['selected_yildiz_multinations'] = True
            passes_baraj = any(check_multi_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_multinations'] = passes_baraj
        else:
            athlete['selected_yildiz_multinations'] = False
            athlete['coach_called_yildiz_multinations'] = False
        for k in ['_first', '_second', '_third']:
            athlete.pop(k, None)

    return athletes

def select_yildizlar_comen_cup_aralik(athletes):
    """COMEN Aralık: All 1st in program. 4+ rule: keep best 4, add 2nd for 5th+."""
    females = [a for a in athletes if a['gender'] == 'F' and 2011 <= a.get('birth_year') <= 2013]
    males = [a for a in athletes if a['gender'] == 'M' and 2010 <= a.get('birth_year') <= 2012]

    for athlete in females:
        first_events = get_first_place_events(athlete['athlete_id'], females, 'antalya_events_time', COMEN_CUP_FEMALE_PROGRAM)
        athlete['_first_events'] = first_events
        athlete['_first_count'] = len(first_events)

    for athlete in males:
        first_events = get_first_place_events(athlete['athlete_id'], males, 'antalya_events_time', COMEN_CUP_MALE_PROGRAM)
        athlete['_first_events'] = first_events
        athlete['_first_count'] = len(first_events)

    sel_f = [a for a in females if a['_first_count'] > 0]
    sel_m = [a for a in males if a['_first_count'] > 0]

    sel_ids = {a['athlete_id'] for a in sel_f + sel_m}
    second_adds = set()

    for athlete in sel_f + sel_m:
        if athlete['_first_count'] > 4:
            for event_key in athlete['_first_events'][4:]:
                prog = COMEN_CUP_FEMALE_PROGRAM if athlete['gender'] == 'F' else COMEN_CUP_MALE_PROGRAM
                gender_group = females if athlete['gender'] == 'F' else males
                second = get_second_place_athlete(event_key, gender_group, 'antalya_events_time')
                if second:
                    second_adds.add(second['athlete_id'])

    sel_ids.update(second_adds)

    for athlete in athletes:
        if athlete['athlete_id'] in sel_ids:
            athlete['selected_yildiz_comen_cup_aralik'] = True
            passes_baraj = any(check_comen_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_comen_cup_aralik'] = passes_baraj
        else:
            athlete['selected_yildiz_comen_cup_aralik'] = False
            athlete['coach_called_yildiz_comen_cup_aralik'] = False
        for k in ['_first_events', '_first_count']:
            athlete.pop(k, None)

    return athletes

def select_yildizlar_comen_cup_nisan(athletes):
    """COMEN Nisan: All 1st in program (edirne data). 4+ rule: keep best 4, add 2nd for 5th+."""
    females = [a for a in athletes if a['gender'] == 'F' and 2011 <= a.get('birth_year') <= 2013]
    males = [a for a in athletes if a['gender'] == 'M' and 2010 <= a.get('birth_year') <= 2012]

    for athlete in females:
        first_events = get_first_place_events(athlete['athlete_id'], females, 'edirne_events_time', COMEN_CUP_FEMALE_PROGRAM)
        athlete['_first_events'] = first_events
        athlete['_first_count'] = len(first_events)

    for athlete in males:
        first_events = get_first_place_events(athlete['athlete_id'], males, 'edirne_events_time', COMEN_CUP_MALE_PROGRAM)
        athlete['_first_events'] = first_events
        athlete['_first_count'] = len(first_events)

    sel_f = [a for a in females if a['_first_count'] > 0]
    sel_m = [a for a in males if a['_first_count'] > 0]

    sel_ids = {a['athlete_id'] for a in sel_f + sel_m}
    second_adds = set()

    for athlete in sel_f + sel_m:
        if athlete['_first_count'] > 4:
            for event_key in athlete['_first_events'][4:]:
                gender_group = females if athlete['gender'] == 'F' else males
                second = get_second_place_athlete(event_key, gender_group, 'edirne_events_time')
                if second:
                    second_adds.add(second['athlete_id'])

    sel_ids.update(second_adds)

    for athlete in athletes:
        if athlete['athlete_id'] in sel_ids:
            athlete['selected_yildiz_comen_cup_nisan'] = True
            passes_baraj = any(check_comen_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_comen_cup_nisan'] = passes_baraj
        else:
            athlete['selected_yildiz_comen_cup_nisan'] = False
            athlete['coach_called_yildiz_comen_cup_nisan'] = False
        for k in ['_first_events', '_first_count']:
            athlete.pop(k, None)

    return athletes

def select_yildizlar_central_europe_aralik(athletes):
    """CENTRAL Aralık: Top 12F+12M in program. If >12 1st places, rank by (1st,2nd,3rd). 4+ rule: add 2nd for 5th+."""
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    females = [a for a in eligible if a['gender'] == 'F']
    males = [a for a in eligible if a['gender'] == 'M']

    for athlete in females:
        first_events = get_first_place_events(athlete['athlete_id'], females, 'combined_events_time', CENTRAL_FEMALE_PROGRAM)
        athlete['_first_events'] = first_events
        athlete['_first'] = len(first_events)
        athlete['_second'] = count_events_by_rank(athlete['athlete_id'], females, 'combined_events_time', 2, CENTRAL_FEMALE_PROGRAM)
        athlete['_third'] = count_events_by_rank(athlete['athlete_id'], females, 'combined_events_time', 3, CENTRAL_FEMALE_PROGRAM)

    for athlete in males:
        first_events = get_first_place_events(athlete['athlete_id'], males, 'combined_events_time', CENTRAL_MALE_PROGRAM)
        athlete['_first_events'] = first_events
        athlete['_first'] = len(first_events)
        athlete['_second'] = count_events_by_rank(athlete['athlete_id'], males, 'combined_events_time', 2, CENTRAL_MALE_PROGRAM)
        athlete['_third'] = count_events_by_rank(athlete['athlete_id'], males, 'combined_events_time', 3, CENTRAL_MALE_PROGRAM)

    females.sort(key=lambda x: (x['_first'], x['_second'], x['_third']), reverse=True)
    males.sort(key=lambda x: (x['_first'], x['_second'], x['_third']), reverse=True)

    sel_f = females[:12]
    sel_m = males[:12]
    sel_ids = {a['athlete_id'] for a in sel_f + sel_m}
    second_adds = set()

    for athlete in sel_f + sel_m:
        if athlete['_first'] > 4:
            for event_key in athlete['_first_events'][4:]:
                gender_group = females if athlete['gender'] == 'F' else males
                second = get_second_place_athlete(event_key, gender_group, 'combined_events_time')
                if second:
                    second_adds.add(second['athlete_id'])

    sel_ids.update(second_adds)

    for athlete in athletes:
        if athlete['athlete_id'] in sel_ids:
            athlete['selected_yildiz_central_europe_aralik'] = True
            passes_baraj = any(check_central_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_central_europe_aralik'] = passes_baraj
        else:
            athlete['selected_yildiz_central_europe_aralik'] = False
            athlete['coach_called_yildiz_central_europe_aralik'] = False
        for k in ['_first_events', '_first', '_second', '_third']:
            athlete.pop(k, None)

    return athletes

def select_yildizlar_central_europe_nisan(athletes):
    """CENTRAL Nisan: Same as Aralık (both use combined data)."""
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    females = [a for a in eligible if a['gender'] == 'F']
    males = [a for a in eligible if a['gender'] == 'M']

    for athlete in females:
        first_events = get_first_place_events(athlete['athlete_id'], females, 'combined_events_time', CENTRAL_FEMALE_PROGRAM)
        athlete['_first_events'] = first_events
        athlete['_first'] = len(first_events)
        athlete['_second'] = count_events_by_rank(athlete['athlete_id'], females, 'combined_events_time', 2, CENTRAL_FEMALE_PROGRAM)
        athlete['_third'] = count_events_by_rank(athlete['athlete_id'], females, 'combined_events_time', 3, CENTRAL_FEMALE_PROGRAM)

    for athlete in males:
        first_events = get_first_place_events(athlete['athlete_id'], males, 'combined_events_time', CENTRAL_MALE_PROGRAM)
        athlete['_first_events'] = first_events
        athlete['_first'] = len(first_events)
        athlete['_second'] = count_events_by_rank(athlete['athlete_id'], males, 'combined_events_time', 2, CENTRAL_MALE_PROGRAM)
        athlete['_third'] = count_events_by_rank(athlete['athlete_id'], males, 'combined_events_time', 3, CENTRAL_MALE_PROGRAM)

    females.sort(key=lambda x: (x['_first'], x['_second'], x['_third']), reverse=True)
    males.sort(key=lambda x: (x['_first'], x['_second'], x['_third']), reverse=True)

    sel_f = females[:12]
    sel_m = males[:12]
    sel_ids = {a['athlete_id'] for a in sel_f + sel_m}
    second_adds = set()

    for athlete in sel_f + sel_m:
        if athlete['_first'] > 4:
            for event_key in athlete['_first_events'][4:]:
                gender_group = females if athlete['gender'] == 'F' else males
                second = get_second_place_athlete(event_key, gender_group, 'combined_events_time')
                if second:
                    second_adds.add(second['athlete_id'])

    sel_ids.update(second_adds)

    for athlete in athletes:
        if athlete['athlete_id'] in sel_ids:
            athlete['selected_yildiz_central_europe_nisan'] = True
            passes_baraj = any(check_central_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_central_europe_nisan'] = passes_baraj
        else:
            athlete['selected_yildiz_central_europe_nisan'] = False
            athlete['coach_called_yildiz_central_europe_nisan'] = False
        for k in ['_first_events', '_first', '_second', '_third']:
            athlete.pop(k, None)

    return athletes

def select_federasyon_karma(athletes):
    """Select federasyon karma from athletes NOT selected to Multi/COMEN/CENTRAL.

    Rule: "Federasyon karması kuralları. Kadro, Multinations-Comen-Central European Yıldızlar
    Milli Takımlarının ana kadrosuna giremeyen sporculardan seçilecektir."

    Selection by birth year + region + gender:
    - 13 yaş (2013): 1. Bölge 6F+6M, 2-6. Bölgeler 3F+3M
    - 14 yaş (2012): 1. Bölge 4F+4M, 2-6. Bölgeler 2F+2M
    - 15 yaş (2011): 1. Bölge 2F+2M, 2-6. Bölgeler 1F+1M
    """
    REGION_QUOTAS = {
        2013: {1: (6, 6), 2: (3, 3), 3: (3, 3), 4: (3, 3), 5: (3, 3), 6: (3, 3)},
        2012: {1: (4, 4), 2: (2, 2), 3: (2, 2), 4: (2, 2), 5: (2, 2), 6: (2, 2)},
        2011: {1: (2, 2), 2: (1, 1), 3: (1, 1), 4: (1, 1), 5: (1, 1), 6: (1, 1)},
    }

    # Find athletes NOT selected to any yıldızlar competition
    not_selected = []
    for a in athletes:
        is_multi = a.get('selected_yildiz_multinations', False)
        is_comen = a.get('selected_yildiz_comen_cup_aralik', False) or a.get('selected_yildiz_comen_cup_nisan', False)
        is_central = a.get('selected_yildiz_central_europe_aralik', False) or a.get('selected_yildiz_central_europe_nisan', False)

        if not (is_multi or is_comen or is_central):
            not_selected.append(a)

    # Group by birth_year and region
    for birth_year in [2013, 2012, 2011]:
        year_athletes = [a for a in not_selected if a.get('birth_year') == birth_year]
        quotas = REGION_QUOTAS.get(birth_year, {})

        for region in range(1, 7):  # 6 regions
            region_athletes = [a for a in year_athletes if a.get('region') == region]
            quota_f, quota_m = quotas.get(region, (0, 0))

            if not region_athletes:
                continue

            # Separate by gender and rank by 1st place count
            females = [a for a in region_athletes if a['gender'] == 'F']
            males = [a for a in region_athletes if a['gender'] == 'M']

            # Count first places using combined_events_time
            eligible = [x for x in athletes if x.get('birth_year') == birth_year and x.get('region') == region]

            for a in females:
                same_gender = [x for x in eligible if x['gender'] == 'F']
                a['_karma_first_count'] = count_first_places(a['athlete_id'], same_gender, 'combined_events_time')

            for a in males:
                same_gender = [x for x in eligible if x['gender'] == 'M']
                a['_karma_first_count'] = count_first_places(a['athlete_id'], same_gender, 'combined_events_time')

            # Sort by first count desc, then name (tiebreaker)
            females.sort(key=lambda a: (-a.get('_karma_first_count', 0), a['athlete_name']))
            males.sort(key=lambda a: (-a.get('_karma_first_count', 0), a['athlete_name']))

            # Select top N per gender by quota
            for i, female in enumerate(females[:quota_f]):
                female['selected_federasyon_karma_b1'] = True

            for i, male in enumerate(males[:quota_m]):
                male['selected_federasyon_karma_b1'] = True

    # Cleanup temp fields
    for a in athletes:
        a.pop('_karma_first_count', None)

    return athletes

def select_all_yildizlar(athletes):
    """Apply all selections.

    Three independent competitions (Multinations, COMEN, CENTRAL).
    Athletes can be selected for multiple competitions based on their performance.
    Federasyon karma: athletes NOT selected to Multi/COMEN/CENTRAL
    """
    athletes = select_yildizlar_multinations(athletes)
    athletes = select_yildizlar_comen_cup_aralik(athletes)
    athletes = select_yildizlar_comen_cup_nisan(athletes)
    athletes = select_yildizlar_central_europe_aralik(athletes)
    athletes = select_yildizlar_central_europe_nisan(athletes)
    athletes = select_federasyon_karma(athletes)

    logger.info(f"Yıldızlar selection complete: {len(athletes)} athletes")
    return athletes
