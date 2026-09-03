"""
Yıldızlar (Youth) National Team Selection Rankings

Handles three competitions (per TYF 2026-YILDIZLAR-MILLI-TAKIM-SECILME-KRITERLERI):
- Multinations Yıldızlar: Top 10F + 10M (by 1st place count)
- Comen Cup Yıldızlar: All branş birincileri (athletes with any 1st place)
- Central European Meet Yıldızlar: Top 12F + 12M (by 1st place count)

Selection Rule: "Her branş ve mesafede en iyi dereceye sahip sporculardan seçilecektir"
→ Each event/distance: determine 1st place (best time)
→ Count 1st places per athlete
→ Select by 1st place count (descending)
"""

import logging
from federasyon.yildizlar_multinations_barajlari import check_antrenor_baraj as check_multi_baraj
from federasyon.yildizlar_comen_cup_barajlari import check_antrenor_baraj as check_comen_baraj
from federasyon.yildizlar_central_europe_barajlari import check_antrenor_baraj as check_central_baraj

logger = logging.getLogger(__name__)


def parse_time(time_str: str) -> float:
    """Parse time string (MM:SS.MS or SS.MS) to seconds."""
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


def get_second_place_athletes(event_key: tuple, eligible_athletes: list, event_times_key: str = 'combined_events_time') -> dict:
    """
    Get 2nd place athlete for a specific event.
    Returns: {'athlete_id': str, 'time_sec': float, 'time_text': str}
    """
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
    return times_list[1] if len(times_list) > 1 else None


def count_first_places(athlete_id: int, eligible_athletes: list, event_times_key: str = 'combined_events_time') -> int:
    """
    Count how many events (branş/mesafe) this athlete placed 1st in.

    Algorithm:
    1. Collect all events across eligible athletes (using specified event_times_key)
    2. For each event, find athlete with best (lowest) time
    3. Count how many events this athlete won

    Args:
        athlete_id: Target athlete ID
        eligible_athletes: Pool of athletes to compare against (filtered by gender/age)
        event_times_key: 'antalya_events_time' | 'edirne_events_time' | 'combined_events_time'
                        Must match the leg being evaluated (Aralık vs Nisan)
    """
    if not eligible_athletes:
        return 0

    # Find this athlete
    athlete = next((a for a in eligible_athletes if a.get('athlete_id') == athlete_id), None)
    if not athlete:
        return 0

    # Collect all events from specified source (Aralık, Nisan, or Combined)
    all_events = set()
    for a in eligible_athletes:
        for event_key in a.get(event_times_key, {}).keys():
            all_events.add(event_key)

    # For each event, check if this athlete has best time
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
    """
    Multinations Yıldızlar: Top 10F + 10M by 1st place count.
    Age: 2013–2011 (both genders)
    Selection: 20-22 Aralık 2025 only
    Source: ARALYK (antalya_events_time) - NOT combined
    """
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]

    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']

    # Count 1st places for each athlete within gender group - use ARALYK (antalya) data only
    for athlete in females:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), females, 'antalya_events_time')
    for athlete in males:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), males, 'antalya_events_time')

    # Sort by 1st place count (descending)
    females_sorted = sorted(females, key=lambda x: x.get('_temp_first_places', 0), reverse=True)
    males_sorted = sorted(males, key=lambda x: x.get('_temp_first_places', 0), reverse=True)

    selected_females = females_sorted[:10]
    selected_males = males_sorted[:10]
    selected_ids = {a.get('athlete_id') for a in selected_females + selected_males}

    for athlete in athletes:
        if athlete.get('athlete_id') in selected_ids:
            athlete['selected_yildiz_multinations'] = True

            # Check if ANY event passes baraj
            passes_baraj = False
            for (stroke, dist), points in athlete.get('combined_events', {}).items():
                time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
                if check_multi_baraj(stroke, dist, athlete.get('gender'), time_str):
                    passes_baraj = True
                    break

            athlete['coach_called_yildiz_multinations'] = passes_baraj
            logger.info(f"Multinations: {athlete.get('athlete_name')} selected (1st places: {athlete.get('_temp_first_places', 0)})")
        else:
            athlete['selected_yildiz_multinations'] = False
            athlete['coach_called_yildiz_multinations'] = False

        athlete.pop('_temp_first_places', None)

    return athletes


def select_yildizlar_comen_cup_aralik(athletes):
    """
    Comen Cup December selection (20-22 Aralık 2025).
    Age: F 2013–2011, M 2012–2010
    Selection: All branş birincileri (athletes with at least 1 first place)
    Source: ARALYK (antalya_events_time) - NOT combined
    Extra rule: Athletes with >4 first places → add 2nd place for 5th+ birincilik
    """
    females = [
        a for a in athletes
        if a.get('gender') == 'F' and 2011 <= a.get('birth_year') <= 2013
    ]
    males = [
        a for a in athletes
        if a.get('gender') == 'M' and 2010 <= a.get('birth_year') <= 2012
    ]

    # Count 1st places within gender group - use ARALYK (antalya) data only
    for athlete in females:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), females, 'antalya_events_time')
    for athlete in males:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), males, 'antalya_events_time')

    # Select only those with at least 1 first place (branş birincileri)
    selected_females = [f for f in females if f.get('_temp_first_places', 0) > 0]
    selected_males = [m for m in males if m.get('_temp_first_places', 0) > 0]

    # Sort by 1st place count for reference
    selected_females.sort(key=lambda x: x.get('_temp_first_places', 0), reverse=True)
    selected_males.sort(key=lambda x: x.get('_temp_first_places', 0), reverse=True)

    # Extra rule: Athletes with >4 first places → add 2nd place for 5th+ birincilik
    # "4'ten fazla birincilik alan sporcu olur ise, dört yarış dışında kalan yarış için ikinci olan sporcu kadroya davet edilir"
    second_place_additions = set()

    for athlete in selected_females + selected_males:
        first_place_count = athlete.get('_temp_first_places', 0)
        if first_place_count > 4:
            # This athlete has >4 first places
            # For 5th+ first place, add the 2nd place finisher
            event_keys = list(athlete.get('antalya_events_time', {}).keys())

            first_place_events = []
            for event_key in event_keys:
                # Check if this athlete is 1st in this event (within gender + age group)
                best_time = float('inf')
                best_athlete_id = None
                for a in (females if athlete['gender'] == 'F' else males):
                    time_str = a.get('antalya_events_time', {}).get(event_key)
                    time_sec = parse_time(time_str)
                    if time_sec < best_time:
                        best_time = time_sec
                        best_athlete_id = a.get('athlete_id')

                if best_athlete_id == athlete.get('athlete_id'):
                    first_place_events.append(event_key)

            # For events beyond 4th first place, add 2nd place finisher
            if len(first_place_events) > 4:
                for i, event_key in enumerate(first_place_events[4:], start=5):  # 5th onward
                    second_place = get_second_place_athletes(event_key, females if athlete['gender'] == 'F' else males, 'antalya_events_time')
                    if second_place:
                        second_place_additions.add(second_place['athlete_id'])
                        logger.info(f"Extra: Added 2nd place {second_place['athlete_name']} for {event_key[0]} {event_key[1]}m (athlete {athlete['athlete_name']} has {first_place_count} 1st places)")

    eligible_ids = {a.get('athlete_id') for a in selected_females + selected_males}
    eligible_ids.update(second_place_additions)

    for athlete in athletes:
        if athlete.get('athlete_id') in eligible_ids:
            athlete['selected_yildiz_comen_cup_aralik'] = True

            passes_baraj = False
            for (stroke, dist), points in athlete.get('combined_events', {}).items():
                time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
                if check_comen_baraj(stroke, dist, athlete.get('gender'), time_str):
                    passes_baraj = True
                    break

            athlete['coach_called_yildiz_comen_cup_aralik'] = passes_baraj
            logger.info(f"Comen Cup Aralık: {athlete.get('athlete_name')} selected (1st places: {athlete.get('_temp_first_places', 0)})")
        else:
            athlete['selected_yildiz_comen_cup_aralik'] = False
            athlete['coach_called_yildiz_comen_cup_aralik'] = False

        athlete.pop('_temp_first_places', None)

    return athletes


def select_yildizlar_comen_cup_nisan(athletes):
    """
    Comen Cup April selection (17-19 Nisan 2026).
    Age: F 2013–2011, M 2012–2010
    Selection: All branş birincileri from combined (Aralık + Nisan)
    Source: NİSAN (edirne_events_time) - NOT combined (Aralık + Nisan combined seçim olsa bile, her yarış kendi verilerine bakılır)
    """
    females = [
        a for a in athletes
        if a.get('gender') == 'F' and 2011 <= a.get('birth_year') <= 2013
    ]
    males = [
        a for a in athletes
        if a.get('gender') == 'M' and 2010 <= a.get('birth_year') <= 2012
    ]

    # Count 1st places within gender group - use NİSAN (edirne) data only
    for athlete in females:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), females, 'edirne_events_time')
    for athlete in males:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), males, 'edirne_events_time')

    # Select only those with at least 1 first place (branş birincileri)
    selected_females = [f for f in females if f.get('_temp_first_places', 0) > 0]
    selected_males = [m for m in males if m.get('_temp_first_places', 0) > 0]

    # Sort by 1st place count
    selected_females.sort(key=lambda x: x.get('_temp_first_places', 0), reverse=True)
    selected_males.sort(key=lambda x: x.get('_temp_first_places', 0), reverse=True)

    # Extra rule: Athletes with >4 first places → add 2nd place for 5th+ birincilik
    # "4'ten fazla birincilik alan sporcu olur ise, dört yarış dışında kalan yarış için ikinci olan sporcu kadroya davet edilir"
    second_place_additions = set()

    for athlete in selected_females + selected_males:
        first_place_count = athlete.get('_temp_first_places', 0)
        if first_place_count > 4:
            # This athlete has >4 first places
            # For 5th+ first place, add the 2nd place finisher
            event_keys = list(athlete.get('edirne_events_time', {}).keys())

            first_place_events = []
            for event_key in event_keys:
                # Check if this athlete is 1st in this event
                best_time = float('inf')
                best_athlete_id = None
                for a in (females if athlete['gender'] == 'F' else males):
                    time_str = a.get('edirne_events_time', {}).get(event_key)
                    time_sec = parse_time(time_str)
                    if time_sec < best_time:
                        best_time = time_sec
                        best_athlete_id = a.get('athlete_id')

                if best_athlete_id == athlete.get('athlete_id'):
                    first_place_events.append(event_key)

            # For events beyond 4th first place, add 2nd place finisher
            if len(first_place_events) > 4:
                for i, event_key in enumerate(first_place_events[4:], start=5):  # 5th onward
                    second_place = get_second_place_athletes(event_key, females if athlete['gender'] == 'F' else males, 'edirne_events_time')
                    if second_place:
                        second_place_additions.add(second_place['athlete_id'])
                        logger.info(f"Extra: Added 2nd place {second_place['athlete_name']} for {event_key[0]} {event_key[1]}m (athlete {athlete['athlete_name']} has {first_place_count} 1st places)")

    eligible_ids = {a.get('athlete_id') for a in selected_females + selected_males}
    eligible_ids.update(second_place_additions)

    for athlete in athletes:
        if athlete.get('athlete_id') in eligible_ids:
            athlete['selected_yildiz_comen_cup_nisan'] = True

            passes_baraj = False
            for (stroke, dist), points in athlete.get('combined_events', {}).items():
                time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
                if check_comen_baraj(stroke, dist, athlete.get('gender'), time_str):
                    passes_baraj = True
                    break

            athlete['coach_called_yildiz_comen_cup_nisan'] = passes_baraj
            logger.info(f"Comen Cup Nisan: {athlete.get('athlete_name')} selected (1st places: {athlete.get('_temp_first_places', 0)})")
        else:
            athlete['selected_yildiz_comen_cup_nisan'] = False
            athlete['coach_called_yildiz_comen_cup_nisan'] = False

        athlete.pop('_temp_first_places', None)

    return athletes


def select_yildizlar_central_europe_aralik(athletes):
    """
    Central European December selection (20-22 Aralık 2025).
    Age: 2013–2011 (both genders)
    Cadre: Top 12F + 12M by 1st place count
    Source: COMBINED (combined_events_time) - "her branş ve mesafede en iyi dereceye sahip sporculardan"
    Note: 4+ birincilik kuralı combined veriler üzerinden calculate edilir (Aralık + Nisan merged)
    """
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]

    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']

    # Count 1st places within gender group - use COMBINED data (Aralık + Nisan merged)
    for athlete in females:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), females, 'combined_events_time')
    for athlete in males:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), males, 'combined_events_time')

    # Sort by 1st place count
    females_sorted = sorted(females, key=lambda x: x.get('_temp_first_places', 0), reverse=True)
    males_sorted = sorted(males, key=lambda x: x.get('_temp_first_places', 0), reverse=True)

    selected = females_sorted[:12] + males_sorted[:12]
    selected_ids = {a.get('athlete_id') for a in selected}

    # Extra rule: Athletes with >4 first places (combined) → add 2nd place for 5th+ birincilik
    # "4'ten fazla birincilik alan sporcu olur ise, dört yarış dışında kalan yarış için ikinci olan sporcu kadroya davet edilir"
    second_place_additions = set()

    for athlete in selected:
        first_place_count = athlete.get('_temp_first_places', 0)
        if first_place_count > 4:
            # This athlete has >4 first places (from COMBINED data)
            # For 5th+ first place, add the 2nd place finisher
            event_keys = list(athlete.get('combined_events_time', {}).keys())

            first_place_events = []
            for event_key in event_keys:
                # Check if this athlete is 1st in this event (within gender + age group, using COMBINED data)
                best_time = float('inf')
                best_athlete_id = None
                for a in (females if athlete['gender'] == 'F' else males):
                    time_str = a.get('combined_events_time', {}).get(event_key)
                    time_sec = parse_time(time_str)
                    if time_sec < best_time:
                        best_time = time_sec
                        best_athlete_id = a.get('athlete_id')

                if best_athlete_id == athlete.get('athlete_id'):
                    first_place_events.append(event_key)

            # For events beyond 4th first place, add 2nd place finisher (using COMBINED data)
            if len(first_place_events) > 4:
                for i, event_key in enumerate(first_place_events[4:], start=5):  # 5th onward
                    second_place = get_second_place_athletes(event_key, females if athlete['gender'] == 'F' else males, 'combined_events_time')
                    if second_place:
                        second_place_additions.add(second_place['athlete_id'])
                        logger.info(f"Extra: Added 2nd place {second_place['athlete_name']} for {event_key[0]} {event_key[1]}m (athlete {athlete['athlete_name']} has {first_place_count} 1st places)")

    selected_ids.update(second_place_additions)

    for athlete in athletes:
        if athlete.get('athlete_id') in selected_ids:
            athlete['selected_yildiz_central_europe_aralik'] = True

            passes_baraj = False
            for (stroke, dist), points in athlete.get('combined_events', {}).items():
                time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
                if check_central_baraj(stroke, dist, athlete.get('gender'), time_str):
                    passes_baraj = True
                    break

            athlete['coach_called_yildiz_central_europe_aralik'] = passes_baraj
            logger.info(f"Central Europe Aralık: {athlete.get('athlete_name')} selected (1st places: {athlete.get('_temp_first_places', 0)})")
        else:
            athlete['selected_yildiz_central_europe_aralik'] = False
            athlete['coach_called_yildiz_central_europe_aralik'] = False

        athlete.pop('_temp_first_places', None)

    return athletes


def select_yildizlar_central_europe_nisan(athletes):
    """
    Central European April selection (17-19 Nisan 2026).
    Age: 2013–2011 (both genders)
    Cadre: Top 12F + 12M by 1st place count (combined Aralık + Nisan)
    Source: COMBINED (combined_events_time) - "her branş ve mesafede en iyi dereceye sahip sporculardan"
    Extra rule: Athletes with >4 first places (combined) → add 2nd place for 5th+ birincilik
    """
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]

    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']

    # Count 1st places within gender group - use COMBINED data (Aralık + Nisan merged)
    for athlete in females:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), females, 'combined_events_time')
    for athlete in males:
        athlete['_temp_first_places'] = count_first_places(athlete.get('athlete_id'), males, 'combined_events_time')

    # Sort by 1st place count
    females_sorted = sorted(females, key=lambda x: x.get('_temp_first_places', 0), reverse=True)
    males_sorted = sorted(males, key=lambda x: x.get('_temp_first_places', 0), reverse=True)

    selected = females_sorted[:12] + males_sorted[:12]
    selected_ids = {a.get('athlete_id') for a in selected}

    # Extra rule: Athletes with >4 first places → add 2nd place for 5th+ birincilik
    # "4'ten fazla birincilik alan sporcu olur ise, dört yarış dışında kalan yarış için ikinci olan sporcu kadroya davet edilir"
    second_place_additions = set()

    for athlete in selected:
        first_place_count = athlete.get('_temp_first_places', 0)
        if first_place_count > 4:
            # This athlete has >4 first places (from COMBINED data)
            # For 5th+ first place, add the 2nd place finisher
            event_keys = list(athlete.get('combined_events_time', {}).keys())

            first_place_events = []
            for event_key in event_keys:
                # Check if this athlete is 1st in this event (within gender + age group, using COMBINED data)
                best_time = float('inf')
                best_athlete_id = None
                for a in (females if athlete['gender'] == 'F' else males):
                    time_str = a.get('combined_events_time', {}).get(event_key)
                    time_sec = parse_time(time_str)
                    if time_sec < best_time:
                        best_time = time_sec
                        best_athlete_id = a.get('athlete_id')

                if best_athlete_id == athlete.get('athlete_id'):
                    first_place_events.append(event_key)

            # For events beyond 4th first place, add 2nd place finisher (using COMBINED data)
            if len(first_place_events) > 4:
                for i, event_key in enumerate(first_place_events[4:], start=5):  # 5th onward
                    second_place = get_second_place_athletes(event_key, females if athlete['gender'] == 'F' else males, 'combined_events_time')
                    if second_place:
                        second_place_additions.add(second_place['athlete_id'])
                        logger.info(f"Extra: Added 2nd place {second_place['athlete_name']} for {event_key[0]} {event_key[1]}m (athlete {athlete['athlete_name']} has {first_place_count} 1st places)")

    selected_ids.update(second_place_additions)

    for athlete in athletes:
        if athlete.get('athlete_id') in selected_ids:
            athlete['selected_yildiz_central_europe_nisan'] = True

            passes_baraj = False
            for (stroke, dist), points in athlete.get('combined_events', {}).items():
                time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
                if check_central_baraj(stroke, dist, athlete.get('gender'), time_str):
                    passes_baraj = True
                    break

            athlete['coach_called_yildiz_central_europe_nisan'] = passes_baraj
            logger.info(f"Central Europe Nisan: {athlete.get('athlete_name')} selected (1st places: {athlete.get('_temp_first_places', 0)})")
        else:
            athlete['selected_yildiz_central_europe_nisan'] = False
            athlete['coach_called_yildiz_central_europe_nisan'] = False

        athlete.pop('_temp_first_places', None)

    return athletes


def select_all_yildizlar(athletes):
    """Apply all yıldızlar selections to athletes list."""
    athletes = select_yildizlar_multinations(athletes)
    athletes = select_yildizlar_comen_cup_aralik(athletes)
    athletes = select_yildizlar_comen_cup_nisan(athletes)
    athletes = select_yildizlar_central_europe_aralik(athletes)
    athletes = select_yildizlar_central_europe_nisan(athletes)

    logger.info(f"Yıldızlar selection complete: {len(athletes)} athletes processed")
    return athletes
