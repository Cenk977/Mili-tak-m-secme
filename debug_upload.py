#!/usr/bin/env python3
"""Debug upload performance - time each step."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, batch_insert_fed_results, batch_insert_fed_athlete_best, get_fed_results, clear_fed_tables
from modules.lxf_parser import parse_lxf_file, get_birth_year
from modules.m4_mapping import lookup_club
from federasyon.scorer import score_event

def normalize_athlete_data(athlete, result, overrides):
    """Minimal normalization for testing."""
    return athlete, result

# Test file
test_file = "data/antalya_millitakim_secme_sonuc.lxf"

print("=" * 60)
print("UPLOAD PERFORMANCE DEBUG")
print("=" * 60)

# Initialize
init_db()
clear_fed_tables()

# Time parsing
t0 = time.time()
athletes, results = parse_lxf_file(test_file)
t_parse = time.time() - t0
print(f"✓ Parse LXF: {t_parse:.2f}s ({len(athletes)} athletes, {len(results)} results)")

# Time fed_results insertion (batch)
t0 = time.time()
fed_results_batch = []
fed_athletes = {}

for athlete in athletes:
    if 'birth_year' not in athlete or not athlete['birth_year']:
        athlete['birth_year'] = get_birth_year(athlete.get('birthdate'))

    athlete_results = [r for r in results if r.get('athlete_id') == athlete.get('athlete_id')]
    if not athlete_results:
        continue

    for result in athlete_results:
        athlete, result = normalize_athlete_data(athlete, result, {})

    full_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
    athlete['name'] = full_name

    athlete_key = (full_name, athlete.get('birth_year'), athlete.get('gender'))
    if athlete_key not in fed_athletes:
        fed_athletes[athlete_key] = {
            'athlete_name': full_name,
            'birth_year': athlete.get('birth_year'),
            'gender': athlete.get('gender'),
            'region': athlete.get('region', 0),
            'city': athlete.get('city', 'Unknown'),
            'club': athlete.get('club_name', 'Unknown'),
        }

    for result in athlete_results:
        fed_result = {
            'race_leg': 'antalya',
            'race_date': None,
            'athlete_name': full_name,
            'birth_year': athlete.get('birth_year'),
            'gender': athlete.get('gender'),
            'region': athlete.get('region', 0),
            'city': athlete.get('city', 'Unknown'),
            'club': athlete.get('club_name', 'Unknown'),
            'stroke': result.get('stroke'),
            'distance': result.get('distance'),
            'time_text': result.get('time_text'),
            'time_seconds': result.get('time_seconds'),
            'points': None,
            'source_pdf_seq': None,
        }
        fed_results_batch.append(fed_result)

fed_results_count = batch_insert_fed_results(fed_results_batch)
t_insert = time.time() - t0
print(f"✓ Batch insert fed_results: {t_insert:.2f}s ({fed_results_count} rows)")

# Time best scores computation
t0 = time.time()
from collections import defaultdict

results_fetched = get_fed_results('antalya')
print(f"  Fetched {len(results_fetched)} results from DB")

grouped = defaultdict(list)
for r in results_fetched:
    key = (r['athlete_name'], r['birth_year'], r['gender'], r['stroke'], r['distance'])
    grouped[key].append(r)

print(f"  Grouped into {len(grouped)} groups")

best_scores_batch = []
for (athlete_name, birth_year, gender, stroke, distance), group in grouped.items():
    valid_results = [r for r in group if r['time_seconds'] is not None]
    if not valid_results:
        continue

    best_result = min(valid_results, key=lambda r: r['time_seconds'])
    best_time_sec = best_result['time_seconds']
    best_time_txt = best_result['time_text']
    best_leg = best_result['race_leg']

    try:
        best_points = score_event(best_time_sec, birth_year, gender, stroke, distance)
    except Exception as e:
        best_points = 0

    best_dict = {
        'athlete_name': athlete_name,
        'birth_year': birth_year,
        'gender': gender,
        'region': best_result['region'],
        'city': best_result['city'],
        'club': best_result['club'],
        'stroke': stroke,
        'distance': distance,
        'best_points': best_points,
        'best_time_sec': best_time_sec,
        'best_time_txt': best_time_txt,
        'best_leg': best_leg,
    }
    best_scores_batch.append(best_dict)

saved_count = batch_insert_fed_athlete_best(best_scores_batch)
t_best = time.time() - t0
print(f"✓ Batch compute & save best scores: {t_best:.2f}s ({saved_count} saved)")

print("=" * 60)
print(f"TOTAL: {t_parse + t_insert + t_best:.2f}s")
print(f"  Parsing:  {t_parse:.2f}s ({t_parse/(t_parse+t_insert+t_best)*100:.1f}%)")
print(f"  Insert:   {t_insert:.2f}s ({t_insert/(t_parse+t_insert+t_best)*100:.1f}%)")
print(f"  Best:     {t_best:.2f}s ({t_best/(t_parse+t_insert+t_best)*100:.1f}%)")
print("=" * 60)
