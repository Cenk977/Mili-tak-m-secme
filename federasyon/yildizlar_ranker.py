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

# Event program: SAME branş/mesafe list for all three Yıldızlar competitions
# (Multinations, Comen Cup, Central European) — confirmed against the
# antrenör baraj tables in 2026_YILDIZLAR_MILLI_TAKIM_SECILME_KRITERLERI.md,
# which are identical across all three competitions. Relay events are
# handled separately by the federation (rule: "bayrak müsabakaları için
# ... kadroya sporcu davet edebilir") and are not part of this individual
# event ranking.
YILDIZLAR_FEMALE_PROGRAM = {
    ('Serbest', 50), ('Serbest', 100), ('Serbest', 200), ('Serbest', 400), ('Serbest', 800),
    ('Sırtüstü', 50), ('Sırtüstü', 100), ('Sırtüstü', 200),
    ('Kurbağalama', 50), ('Kurbağalama', 100), ('Kurbağalama', 200),
    ('Kelebek', 50), ('Kelebek', 100), ('Kelebek', 200),
    ('Karışık', 200), ('Karışık', 400),
}

YILDIZLAR_MALE_PROGRAM = {
    ('Serbest', 50), ('Serbest', 100), ('Serbest', 200), ('Serbest', 400), ('Serbest', 1500),
    ('Sırtüstü', 50), ('Sırtüstü', 100), ('Sırtüstü', 200),
    ('Kurbağalama', 50), ('Kurbağalama', 100), ('Kurbağalama', 200),
    ('Kelebek', 50), ('Kelebek', 100), ('Kelebek', 200),
    ('Karışık', 200), ('Karışık', 400),
}

# Backward-compatible aliases (Comen/Central used to have their own, slightly
# inconsistent sets — now unified into one program shared by all three).
COMEN_CUP_FEMALE_PROGRAM = YILDIZLAR_FEMALE_PROGRAM
COMEN_CUP_MALE_PROGRAM = YILDIZLAR_MALE_PROGRAM
CENTRAL_FEMALE_PROGRAM = YILDIZLAR_FEMALE_PROGRAM
CENTRAL_MALE_PROGRAM = YILDIZLAR_MALE_PROGRAM

# Individual events that correspond to a relay leg. Relays are always swum
# at 100m per leg (medley: Sırtüstü/Kurbağalama/Kelebek/Serbest 100; free
# relay: Serbest 100) plus Serbest 200 for the 4x200 free relay. A 50m
# individual win (e.g. 50m Kelebek) does NOT indicate relay-leg speed, since
# no Yıldızlar relay is swum over 50m splits for Multinations/Central
# (Comen Cup additionally has 4x50m relays — not modeled here yet).
RELAY_LEG_EVENTS = {
    ('Sırtüstü', 100), ('Kurbağalama', 100), ('Kelebek', 100), ('Serbest', 100),
    ('Serbest', 200),
}

# Comen Cup additionally swims 4x50m relays (Serbest, Karışık), so its
# relay-leg events include the 50m distance per stroke too.
RELAY_LEG_EVENTS_COMEN = RELAY_LEG_EVENTS | {
    ('Sırtüstü', 50), ('Kurbağalama', 50), ('Kelebek', 50), ('Serbest', 50),
}

# How many top finishers per relay-leg event count as "relay candidate"
# depth. Not an official federation number — the rule text only says the
# federation "may invite" athletes for relay purposes at its own discretion
# (e.g. Multinations rule 8); this is a heuristic to surface plausible
# candidates for a human to confirm, not a hard cutoff.
RELAY_CANDIDATE_TOP_N = 6


def _relay_candidate_ids(eligible_athletes: list, event_times_key: str, exclude_ids: set,
                          relay_events: set = RELAY_LEG_EVENTS,
                          top_n: int = RELAY_CANDIDATE_TOP_N) -> set:
    """
    Athlete IDs (not already in exclude_ids) who rank in the top `top_n` of
    ANY relay-leg event (relay_events — RELAY_LEG_EVENTS for Multinations/
    Central European, RELAY_LEG_EVENTS_COMEN for Comen Cup's extra 4x50m
    relays) among eligible_athletes.

    Rationale: relay legs are swum at fixed distances (50m/100m/200m
    depending on competition), so an athlete can be relay-valuable
    (consistently near the top at those specific distances) without ever
    winning an individual event outright — the reverse also holds: winning
    a distance that has no matching relay leg doesn't by itself indicate
    relay speed.
    """
    rankings = _build_group_rankings(eligible_athletes, event_times_key, relay_events)
    candidate_ids = set()
    for event, ranked in rankings.items():
        for entry in ranked[:top_n]:
            aid = entry['athlete_id']
            if aid not in exclude_ids:
                candidate_ids.add(aid)
    return candidate_ids


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

def _build_group_rankings(eligible_athletes: list, event_times_key: str, program_filter: set = None) -> dict:
    """
    Precompute, ONCE per group (instead of once per athlete), the ranked
    (time-sorted) athlete list for every event the group has times for.

    Performance note: the old get_first_place_events/count_events_by_rank/
    count_first_places functions each independently rescanned every event
    for every athlete in the group (O(n) group scans x O(n log n) sort,
    repeated n times => O(n^2 log n) for a group of n athletes). This
    factors that shared per-event sort out into a single O(n log n) pass
    per event, computed once and reused for every athlete's stats.

    Returns: dict event_key -> list of {'athlete_id', 'time_sec'} sorted by
    time_sec ascending (ties broken by original eligible_athletes order,
    matching Python's stable sort — identical tie-break semantics to the
    original per-athlete implementation).
    """
    all_events = set()
    for a in eligible_athletes:
        for event_key in a.get(event_times_key, {}).keys():
            if program_filter is None or event_key in program_filter:
                all_events.add(event_key)

    rankings = {}
    for event_key in all_events:
        times_list = []
        for a in eligible_athletes:
            time_str = a.get(event_times_key, {}).get(event_key)
            time_sec = parse_time(time_str)
            if time_sec != float('inf'):
                times_list.append({'athlete_id': a.get('athlete_id'), 'time_sec': time_sec})
        times_list.sort(key=lambda x: x['time_sec'])
        rankings[event_key] = times_list

    return rankings


def _compute_group_stats(eligible_athletes: list, event_times_key: str, program_filter: set = None) -> dict:
    """
    Compute, for every athlete in the group in a single pass, the same
    (first_count, second_count, third_count, first_events) stats that
    get_first_place_events/count_events_by_rank/count_first_places used to
    compute independently per athlete. See _build_group_rankings for why
    this replaces O(n^2 log n) with O(n log n).

    Returns: dict athlete_id -> {'first': int, 'second': int, 'third': int,
                                  'first_events': list[event_key]}
    first_events preserves the same set-iteration order as the original
    per-athlete get_first_place_events (built from the identical all_events
    set construction), since first_events[4:] slicing feeds selection rules.
    """
    rankings = _build_group_rankings(eligible_athletes, event_times_key, program_filter)
    stats = {a.get('athlete_id'): {'first': 0, 'second': 0, 'third': 0, 'first_events': []}
              for a in eligible_athletes}

    # Iterate event_keys in the same order _build_group_rankings inserted them
    # (dict preserves insertion order), matching the original set-iteration order.
    for event_key, ranked in rankings.items():
        if len(ranked) >= 1:
            aid = ranked[0]['athlete_id']
            if aid in stats:
                stats[aid]['first'] += 1
                stats[aid]['first_events'].append(event_key)
        if len(ranked) >= 2:
            aid = ranked[1]['athlete_id']
            if aid in stats:
                stats[aid]['second'] += 1
        if len(ranked) >= 3:
            aid = ranked[2]['athlete_id']
            if aid in stats:
                stats[aid]['third'] += 1

    return stats


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

MULTINATIONS_QUOTA = 10


def _select_branch_winners_core(eligible, quota, event_times_key,
                                female_program, male_program,
                                relay_events=RELAY_LEG_EVENTS):
    """Branş-birinciliği tabanlı seçim çekirdeği (Multi Yıldızlar + Multi
    Gençler ortak). eligible: tek yaş-grubu-filtreli sporcu listesi.
    Döner: (selected_ids, candidate_ids, relay_candidate_ids).
    Yan etki: eligible sporculara _first/_second/_third eklenir."""
    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']

    for glist, prog in ((females, female_program), (males, male_program)):
        stats = _compute_group_stats(glist, event_times_key, prog)
        for a in glist:
            s = stats.get(a.get('athlete_id'), {'first': 0, 'second': 0, 'third': 0})
            a['_first'] = s['first']
            a['_second'] = s['second']
            a['_third'] = s['third']
            a['_first_events'] = list(s.get('first_events', []))

    def _grp(group):
        with_first = [a for a in group if a.get('_first', 0) > 0]
        without_first = [a for a in group if a.get('_first', 0) == 0]
        return _split_winners_by_quota(with_first, without_first, quota)

    sel_f, cand_f = _grp(females)
    sel_m, cand_m = _grp(males)
    sel_ids = {a.get('athlete_id') for a in sel_f + sel_m}
    cand_ids = {a.get('athlete_id') for a in cand_f + cand_m}
    relay_ids = (
        _relay_candidate_ids(females, event_times_key, sel_ids, relay_events) |
        _relay_candidate_ids(males, event_times_key, sel_ids, relay_events)
    )
    return sel_ids, cand_ids, relay_ids


def _split_winners_by_quota(with_first, without_first, quota):
    """Multinations / Central European kota mantığı (PDF madde 4 + 5).

      - branş birincisi sayısı > kota → madde 5: (1.lik, 2.lik, 3.lük)
        sayısına göre azalan sırala, ilk `quota` kişi KESİN, gerisi ADAY.
        (Deterministik; federasyonun "2. ve 3.lüklere bakılır" ifadesi.)
      - branş birincisi sayısı < kota → madde 4: 2./3.lük sahiplerinden
        en iyileri ADAY olarak eklenir (otomatik seçilmez).
      - tam kotada → herkes KESİN.

    `sorted` kararlıdır; eşit anahtarlarda giriş sırası korunur
    (get_athlete_rankings satırları id'ye göre sıraladığı için deterministik).

    Döner: (selected, candidates)
    """
    if len(with_first) > quota:
        ranked = sorted(
            with_first,
            key=lambda a: (a.get('_first', 0), a.get('_second', 0), a.get('_third', 0)),
            reverse=True,
        )
        return ranked[:quota], ranked[quota:]

    if len(with_first) < quota:
        pool = sorted(
            without_first,
            key=lambda a: (a.get('_second', 0), a.get('_third', 0)),
            reverse=True,
        )[:quota - len(with_first)]
        return with_first, [a for a in pool
                            if a.get('_second', 0) > 0 or a.get('_third', 0) > 0]

    return with_first, []


def select_yildizlar_multinations(athletes):
    """Multinations: quota is 10F+10M, but per the rule text the squad is
    only padded to quota — or trimmed below it — "Türkiye Yüzme Federasyonu
    tarafından" (at the federation's discretion), not automatically:
      - Kesin (definite): every athlete with >=1 actual 1st place. Always
        selected, regardless of whether that count is above or below quota
        (trimming an over-quota field down to exactly 10 is itself a
        federation judgment call this app doesn't make).
      - Aday (candidate): only when there are FEWER than 10 winners, the
        next-best athletes by (2nd, 3rd place count) that the federation
        MAY invite to approach the quota. Flagged separately
        (candidate_yildiz_multinations) — never auto-selected — so the
        dashboard can show them as "aday" for a human decision, including
        completing relay teams.

    Comparing this against the real 2026MULTIYILDIZ.pdf roster confirmed
    the old always-pad-to-10 behavior over-selected: the federation kept
    the men's squad at 8 real winners rather than padding to 10.
    """
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    sel_ids, cand_ids, relay_cand_ids = _select_branch_winners_core(
        eligible, MULTINATIONS_QUOTA, 'antalya_events_time',
        YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)

    for athlete in athletes:
        aid = athlete.get('athlete_id')
        athlete['candidate_relay_yildiz_multinations'] = aid in relay_cand_ids
        if aid in sel_ids:
            athlete['selected_yildiz_multinations'] = True
            athlete['candidate_yildiz_multinations'] = False
            athlete['multinations_events'] = list(athlete.get('_first_events', []))
            passes_baraj = any(check_multi_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_multinations'] = passes_baraj
        elif aid in cand_ids:
            athlete['selected_yildiz_multinations'] = False
            athlete['candidate_yildiz_multinations'] = True
            athlete['multinations_events'] = list(athlete.get('_first_events', []))
            athlete['coach_called_yildiz_multinations'] = False
        else:
            athlete['selected_yildiz_multinations'] = False
            athlete['candidate_yildiz_multinations'] = False
            athlete['multinations_events'] = []
            athlete['coach_called_yildiz_multinations'] = False
        for k in ['_first', '_second', '_third', '_first_events']:
            athlete.pop(k, None)

    return athletes

def select_yildizlar_comen_cup_aralik(athletes):
    """COMEN Cup: winners are determined by the BEST result across BOTH
    selection meets combined (Aralık/Antalya + Nisan/Edirne), pooled into
    one ranking per event — not two independent per-meet winner checks.
    (Named "_aralik" for historical/field-naming reasons; it and
    select_yildizlar_comen_cup_nisan() compute the identical combined
    result, same as Central European's _aralik/_nisan pair already did.)

    All 1st-place-in-program winners are selected. 4+ rule: an athlete who
    wins more than 4 events keeps their best 4; for the 5th+ win, the
    2nd-place finisher in that specific event is invited instead (rule
    text: mandatory "davet edilir", not discretionary).

    Regression: using 'antalya_events_time' alone here (and
    'edirne_events_time' alone in the old _nisan) let an athlete "win" a
    meet-local comparison even though a teammate's true combined-best time
    across both meets was faster — comparing against the real 2026 Comen
    Cup Mediterranean roster (11 athletes) showed exactly this: 6 extra
    "winners" that don't exist once results are correctly pooled."""
    females = [a for a in athletes if a['gender'] == 'F' and 2011 <= a.get('birth_year') <= 2013]
    males = [a for a in athletes if a['gender'] == 'M' and 2010 <= a.get('birth_year') <= 2012]

    stats_f = _compute_group_stats(females, 'combined_events_time', COMEN_CUP_FEMALE_PROGRAM)
    for athlete in females:
        s = stats_f.get(athlete['athlete_id'], {'first_events': [], 'first': 0})
        athlete['_first_events'] = s['first_events']
        athlete['_first_count'] = s['first']

    stats_m = _compute_group_stats(males, 'combined_events_time', COMEN_CUP_MALE_PROGRAM)
    for athlete in males:
        s = stats_m.get(athlete['athlete_id'], {'first_events': [], 'first': 0})
        athlete['_first_events'] = s['first_events']
        athlete['_first_count'] = s['first']

    sel_f = [a for a in females if a['_first_count'] > 0]
    sel_m = [a for a in males if a['_first_count'] > 0]

    sel_ids = {a['athlete_id'] for a in sel_f + sel_m}
    second_adds = set()

    for athlete in sel_f + sel_m:
        if athlete['_first_count'] > 4:
            for event_key in athlete['_first_events'][4:]:
                gender_group = females if athlete['gender'] == 'F' else males
                second = get_second_place_athlete(event_key, gender_group, 'combined_events_time')
                if second:
                    second_adds.add(second['athlete_id'])

    sel_ids.update(second_adds)

    relay_cand_ids = (
        _relay_candidate_ids(females, 'combined_events_time', sel_ids, RELAY_LEG_EVENTS_COMEN) |
        _relay_candidate_ids(males, 'combined_events_time', sel_ids, RELAY_LEG_EVENTS_COMEN)
    )

    for athlete in athletes:
        athlete['candidate_relay_yildiz_comen_cup_aralik'] = athlete['athlete_id'] in relay_cand_ids
        if athlete['athlete_id'] in sel_ids:
            athlete['selected_yildiz_comen_cup_aralik'] = True
            athlete['comen_cup_events'] = sorted(
                set(athlete.get('comen_cup_events', [])) | set(athlete.get('_first_events', []))
            )
            passes_baraj = any(check_comen_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_comen_cup_aralik'] = passes_baraj
        else:
            athlete['selected_yildiz_comen_cup_aralik'] = False
            athlete.setdefault('comen_cup_events', [])
            athlete['coach_called_yildiz_comen_cup_aralik'] = False
        for k in ['_first_events', '_first_count']:
            athlete.pop(k, None)

    return athletes

def select_yildizlar_comen_cup_nisan(athletes):
    """COMEN Cup: identical combined-best-result computation as
    select_yildizlar_comen_cup_aralik() — see that docstring. Kept as a
    separate function only because the persisted field name
    (selected_yildiz_comen_cup_nisan) already exists across the codebase;
    both functions must stay in sync."""
    females = [a for a in athletes if a['gender'] == 'F' and 2011 <= a.get('birth_year') <= 2013]
    males = [a for a in athletes if a['gender'] == 'M' and 2010 <= a.get('birth_year') <= 2012]

    stats_f = _compute_group_stats(females, 'combined_events_time', COMEN_CUP_FEMALE_PROGRAM)
    for athlete in females:
        s = stats_f.get(athlete['athlete_id'], {'first_events': [], 'first': 0})
        athlete['_first_events'] = s['first_events']
        athlete['_first_count'] = s['first']

    stats_m = _compute_group_stats(males, 'combined_events_time', COMEN_CUP_MALE_PROGRAM)
    for athlete in males:
        s = stats_m.get(athlete['athlete_id'], {'first_events': [], 'first': 0})
        athlete['_first_events'] = s['first_events']
        athlete['_first_count'] = s['first']

    sel_f = [a for a in females if a['_first_count'] > 0]
    sel_m = [a for a in males if a['_first_count'] > 0]

    sel_ids = {a['athlete_id'] for a in sel_f + sel_m}
    second_adds = set()

    for athlete in sel_f + sel_m:
        if athlete['_first_count'] > 4:
            for event_key in athlete['_first_events'][4:]:
                gender_group = females if athlete['gender'] == 'F' else males
                second = get_second_place_athlete(event_key, gender_group, 'combined_events_time')
                if second:
                    second_adds.add(second['athlete_id'])

    sel_ids.update(second_adds)

    relay_cand_ids = (
        _relay_candidate_ids(females, 'combined_events_time', sel_ids, RELAY_LEG_EVENTS_COMEN) |
        _relay_candidate_ids(males, 'combined_events_time', sel_ids, RELAY_LEG_EVENTS_COMEN)
    )

    for athlete in athletes:
        athlete['candidate_relay_yildiz_comen_cup_nisan'] = athlete['athlete_id'] in relay_cand_ids
        if athlete['athlete_id'] in sel_ids:
            athlete['selected_yildiz_comen_cup_nisan'] = True
            athlete['comen_cup_events'] = sorted(
                set(athlete.get('comen_cup_events', [])) | set(athlete.get('_first_events', []))
            )
            passes_baraj = any(check_comen_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_comen_cup_nisan'] = passes_baraj
        else:
            athlete['selected_yildiz_comen_cup_nisan'] = False
            athlete.setdefault('comen_cup_events', [])
            athlete['coach_called_yildiz_comen_cup_nisan'] = False
        for k in ['_first_events', '_first_count']:
            athlete.pop(k, None)

    return athletes

CENTRAL_EUROPE_QUOTA = 12


def select_yildizlar_central_europe_aralik(athletes):
    """CENTRAL Aralık: quota 12F+12M, same discretionary-pad caveat as
    Multinations — every real 1st-place winner is 'kesin' (definite)
    regardless of whether that count is above or below 12; only when there
    are FEWER than 12 winners are the next-best (2nd/3rd place) athletes
    flagged as 'aday' (candidate_yildiz_central_europe_aralik), never
    auto-selected. Relay-leg depth candidates (independent of quota fill)
    are flagged the same way as Multinations — see RELAY_LEG_EVENTS.
    4+ rule: an athlete with >4 wins gets kept to 4 individual events; the
    5th+ event's 2nd-place finisher is invited in their place (rule text
    uses mandatory "davet edilir", not discretionary — so this IS
    auto-applied, unlike the quota pad/trim above)."""
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    females = [a for a in eligible if a['gender'] == 'F']
    males = [a for a in eligible if a['gender'] == 'M']

    stats_f = _compute_group_stats(females, 'combined_events_time', CENTRAL_FEMALE_PROGRAM)
    for athlete in females:
        s = stats_f.get(athlete['athlete_id'], {'first_events': [], 'first': 0, 'second': 0, 'third': 0})
        athlete['_first_events'] = s['first_events']
        athlete['_first'] = s['first']
        athlete['_second'] = s['second']
        athlete['_third'] = s['third']

    stats_m = _compute_group_stats(males, 'combined_events_time', CENTRAL_MALE_PROGRAM)
    for athlete in males:
        s = stats_m.get(athlete['athlete_id'], {'first_events': [], 'first': 0, 'second': 0, 'third': 0})
        athlete['_first_events'] = s['first_events']
        athlete['_first'] = s['first']
        athlete['_second'] = s['second']
        athlete['_third'] = s['third']

    def select_group(group):
        with_first = [a for a in group if a.get('_first', 0) > 0]
        without_first = [a for a in group if a.get('_first', 0) == 0]
        return _split_winners_by_quota(with_first, without_first, CENTRAL_EUROPE_QUOTA)

    sel_f, cand_f = select_group(females)
    sel_m, cand_m = select_group(males)
    sel_ids = {a['athlete_id'] for a in sel_f + sel_m}
    cand_ids = {a['athlete_id'] for a in cand_f + cand_m}
    second_adds = set()

    for athlete in sel_f + sel_m:
        if athlete['_first'] > 4:
            for event_key in athlete['_first_events'][4:]:
                gender_group = females if athlete['gender'] == 'F' else males
                second = get_second_place_athlete(event_key, gender_group, 'combined_events_time')
                if second:
                    second_adds.add(second['athlete_id'])

    sel_ids.update(second_adds)
    cand_ids -= sel_ids

    relay_cand_ids = (
        _relay_candidate_ids(females, 'combined_events_time', sel_ids) |
        _relay_candidate_ids(males, 'combined_events_time', sel_ids)
    )

    for athlete in athletes:
        aid = athlete['athlete_id']
        athlete['candidate_relay_yildiz_central_europe_aralik'] = aid in relay_cand_ids
        if aid in sel_ids:
            athlete['selected_yildiz_central_europe_aralik'] = True
            athlete['candidate_yildiz_central_europe_aralik'] = False
            athlete['central_europe_events'] = sorted(
                set(athlete.get('central_europe_events', [])) | set(athlete.get('_first_events', []))
            )
            passes_baraj = any(check_central_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_central_europe_aralik'] = passes_baraj
        elif aid in cand_ids:
            athlete['selected_yildiz_central_europe_aralik'] = False
            athlete['candidate_yildiz_central_europe_aralik'] = True
            athlete['central_europe_events'] = sorted(
                set(athlete.get('central_europe_events', [])) | set(athlete.get('_first_events', []))
            )
            athlete['coach_called_yildiz_central_europe_aralik'] = False
        else:
            athlete['selected_yildiz_central_europe_aralik'] = False
            athlete['candidate_yildiz_central_europe_aralik'] = False
            athlete.setdefault('central_europe_events', [])
            athlete['coach_called_yildiz_central_europe_aralik'] = False
        for k in ['_first_events', '_first', '_second', '_third']:
            athlete.pop(k, None)

    return athletes

def select_yildizlar_central_europe_nisan(athletes):
    """CENTRAL Nisan: Same as Aralık (both use combined data)."""
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    females = [a for a in eligible if a['gender'] == 'F']
    males = [a for a in eligible if a['gender'] == 'M']

    stats_f = _compute_group_stats(females, 'combined_events_time', CENTRAL_FEMALE_PROGRAM)
    for athlete in females:
        s = stats_f.get(athlete['athlete_id'], {'first_events': [], 'first': 0, 'second': 0, 'third': 0})
        athlete['_first_events'] = s['first_events']
        athlete['_first'] = s['first']
        athlete['_second'] = s['second']
        athlete['_third'] = s['third']

    stats_m = _compute_group_stats(males, 'combined_events_time', CENTRAL_MALE_PROGRAM)
    for athlete in males:
        s = stats_m.get(athlete['athlete_id'], {'first_events': [], 'first': 0, 'second': 0, 'third': 0})
        athlete['_first_events'] = s['first_events']
        athlete['_first'] = s['first']
        athlete['_second'] = s['second']
        athlete['_third'] = s['third']

    def select_group(group):
        with_first = [a for a in group if a.get('_first', 0) > 0]
        without_first = [a for a in group if a.get('_first', 0) == 0]
        return _split_winners_by_quota(with_first, without_first, CENTRAL_EUROPE_QUOTA)

    sel_f, cand_f = select_group(females)
    sel_m, cand_m = select_group(males)
    sel_ids = {a['athlete_id'] for a in sel_f + sel_m}
    cand_ids = {a['athlete_id'] for a in cand_f + cand_m}
    second_adds = set()

    for athlete in sel_f + sel_m:
        if athlete['_first'] > 4:
            for event_key in athlete['_first_events'][4:]:
                gender_group = females if athlete['gender'] == 'F' else males
                second = get_second_place_athlete(event_key, gender_group, 'combined_events_time')
                if second:
                    second_adds.add(second['athlete_id'])

    sel_ids.update(second_adds)
    cand_ids -= sel_ids

    relay_cand_ids = (
        _relay_candidate_ids(females, 'combined_events_time', sel_ids) |
        _relay_candidate_ids(males, 'combined_events_time', sel_ids)
    )

    for athlete in athletes:
        aid = athlete['athlete_id']
        athlete['candidate_relay_yildiz_central_europe_nisan'] = aid in relay_cand_ids
        if aid in sel_ids:
            athlete['selected_yildiz_central_europe_nisan'] = True
            athlete['candidate_yildiz_central_europe_nisan'] = False
            athlete['central_europe_events'] = sorted(
                set(athlete.get('central_europe_events', [])) | set(athlete.get('_first_events', []))
            )
            passes_baraj = any(check_central_baraj(s, d, athlete['gender'], athlete.get('combined_events_time', {}).get((s, d), '99:99'))
                             for (s, d) in athlete.get('combined_events', {}))
            athlete['coach_called_yildiz_central_europe_nisan'] = passes_baraj
        elif aid in cand_ids:
            athlete['selected_yildiz_central_europe_nisan'] = False
            athlete['candidate_yildiz_central_europe_nisan'] = True
            athlete['central_europe_events'] = sorted(
                set(athlete.get('central_europe_events', [])) | set(athlete.get('_first_events', []))
            )
            athlete['coach_called_yildiz_central_europe_nisan'] = False
        else:
            athlete['selected_yildiz_central_europe_nisan'] = False
            athlete['candidate_yildiz_central_europe_nisan'] = False
            athlete.setdefault('central_europe_events', [])
            athlete['coach_called_yildiz_central_europe_nisan'] = False
        for k in ['_first_events', '_first', '_second', '_third']:
            athlete.pop(k, None)

    return athletes

def select_all_yildizlar(athletes):
    """Apply the three independent Yıldızlar competition selections
    (Multinations, COMEN, CENTRAL). Athletes can be selected for multiple
    competitions based on their performance.

    Federasyon Karması (TR-*/B*-* point-based ranking, excluding athletes
    selected here) is computed separately by
    panel.serve.apply_selection_status_with_points() — it is NOT part of
    this function. It used to be (via select_federasyon_karma(), now
    removed): that version ranked by first-place count instead of the
    federation's actual point-based top-3 rule, and it overwrote
    selected_slot after rank_group() had already set it correctly, producing
    inconsistent selected/selected_slot pairs (e.g. selected='TR' with
    selected_slot='B2-1'). See FEDERASYON-KARMASI-TAKIM-SECILME-KRITERLERI.md.
    """
    athletes = select_yildizlar_multinations(athletes)
    athletes = select_yildizlar_comen_cup_aralik(athletes)
    athletes = select_yildizlar_comen_cup_nisan(athletes)
    athletes = select_yildizlar_central_europe_aralik(athletes)
    athletes = select_yildizlar_central_europe_nisan(athletes)

    logger.info(f"Yıldızlar selection complete: {len(athletes)} athletes")
    return athletes
