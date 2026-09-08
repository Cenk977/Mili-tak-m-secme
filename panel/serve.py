#!/usr/bin/env python3
"""
panel/serve.py — HTTP server for Milli Takım Seçme Dashboard

Endpoints:
  GET  /                    — Dashboard HTML
  POST /upload              — Upload LXF file, parse, insert to DB
  GET  /api/ranking         — Get selected athletes (JSON)
  POST /clear               — Clear all athletes from DB
"""

import json
import os
import tempfile
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    init_db, insert_athlete, insert_result, get_athletes_by_filter, clear_athletes,
    get_missing_clubs_from_db, insert_fed_result, insert_fed_athlete_best, get_fed_athlete_best,
    get_athlete_rankings, get_fed_results, clear_fed_tables,
    batch_insert_fed_results, batch_insert_fed_athlete_best
)
from modules.lxf_parser import parse_lxf_file, get_birth_year
from modules.m1_normalize import normalize_for_lookup
from modules.m3_age import parse_birthdate
from modules.m4_mapping import lookup_club
from federasyon.scoring_tables import TABLES, POINTS, SELECTION_QUOTAS
from federasyon.scorer import score_event, score_athlete_row, merge_scores, best_scores_sequence, compute_ranking_key
from federasyon.ranker import rank_all, rank_group
from federasyon.multinations import is_multinations
from federasyon.yildizlar_ranker import select_all_yildizlar
from federasyon.gencler_ranker import select_all_gencler
from federasyon.pipeline import MiltiTakimPipeline
from config import DB_PATH, TARGET_AGE_GROUPS, COMPETITION_YEAR
from panel.export import create_rankings_xlsx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_manual_overrides() -> dict:
    """Load manual overrides from JSON file."""
    overrides_path = Path(__file__).parent.parent / "manual_overrides.json"
    if overrides_path.exists():
        with open(overrides_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"club_aliases": [], "name_overrides": []}


def get_name_override(name: str, birth_year: int, gender: str, overrides: dict) -> dict:
    """
    Check if name+birth_year+gender matches any name_override.
    Returns override dict or None.
    """
    for override in overrides.get("name_overrides", []):
        if (override.get("name") == name and
            override.get("birth_year") == birth_year and
            override.get("gender") == gender):
            return override
    return None


def get_club_override(club_name: str, overrides: dict) -> dict:
    """
    Check if club name matches any club_aliases.
    Returns {canonical, city, region} or None.
    """
    if not club_name:
        return None

    norm_club = normalize_for_lookup(club_name)

    for alias in overrides.get("club_aliases", []):
        if normalize_for_lookup(alias.get("raw", "")) == norm_club:
            return {
                "club": alias.get("canonical"),
                "city": alias.get("city"),
                "region": alias.get("region")
            }
    return None


def compute_and_save_best_scores(race_leg: str = 'antalya') -> int:
    """
    Read fed_results, compute best scores per (athlete, stroke, distance),
    and save to fed_athlete_best (batch). Returns count saved.
    """
    from collections import defaultdict

    results = get_fed_results(race_leg)
    logger.info(f"Computing best scores from {len(results)} fed_results")

    # Group by (athlete_name, birth_year, gender, stroke, distance)
    grouped = defaultdict(list)
    for r in results:
        key = (r['athlete_name'], r['birth_year'], r['gender'], r['stroke'], r['distance'])
        grouped[key].append(r)

    # Batch collect all best scores to insert
    best_scores_batch = []

    for (athlete_name, birth_year, gender, stroke, distance), group in grouped.items():
        # Find best (lowest) time
        valid_results = [r for r in group if r['time_seconds'] is not None]
        if not valid_results:
            continue

        best_result = min(valid_results, key=lambda r: r['time_seconds'])
        best_time_sec = best_result['time_seconds']
        best_time_txt = best_result['time_text']
        best_leg = best_result['race_leg']

        # Compute score using score_event()
        try:
            best_points = score_event(best_time_sec, birth_year, gender, stroke, distance)
        except Exception as e:
            logger.warning(f"Error scoring {athlete_name} {birth_year} {gender} {stroke} {distance}: {e}")
            best_points = 0

        # Batch collect best score
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

    # Batch insert all best scores at once
    saved_count = batch_insert_fed_athlete_best(best_scores_batch)
    logger.info(f"Batch saved {saved_count} best scores to fed_athlete_best")
    return saved_count


def apply_selection_status(athletes: list) -> list:
    """
    Apply selection status using rank_group logic.
    Adds 'selected', 'multinations', 'selected_slot' fields to each athlete.
    DEPRECATED: Use apply_selection_status_with_points() instead.
    """
    return apply_selection_status_with_points(athletes)


def apply_selection_status_with_points(athletes: list, leg: str = 'combined') -> list:
    """
    Apply selection status using rank_group logic.
    Handles events dict with time information.
    Adds 'selected', 'multinations', 'selected_slot' fields to each athlete.

    leg: 'combined' (default), 'antalya', or 'edirne'. Antalya/Edirne use that
    leg's own events (antalya_events / edirne_events, already {event: points}
    dicts) so each tab's TR/BÖLGE slot reflects a ranking scoped to that leg's
    results, the same rank_group()-based quota logic used for combined.

    Federasyon Karması rule 2: athletes already selected to the Multinations/
    Comen Cup/Central European Yıldızlar squads are excluded from TR/BÖLGE
    eligibility. Callers must run the yıldızlar selection functions (which
    set selected_yildiz_*) BEFORE calling this, so the exclusion below sees
    up-to-date flags.
    """
    from collections import defaultdict

    events_field = {'antalya': 'antalya_events', 'edirne': 'edirne_events'}.get(leg)

    # Prepare athletes for rank_group: add event_scores = points only from combined_events
    for a in athletes:
        if events_field:
            a['event_scores'] = a.get(events_field, {}) or {}
        elif 'combined_events_for_ranking' in a:
            a['event_scores'] = a.get('combined_events_for_ranking', {})
        else:
            combined_events_points = {}
            for (stroke, dist), data in a.get('combined_events', {}).items():
                points = data.get('points', 0) if isinstance(data, dict) else data
                combined_events_points[(stroke, dist)] = points
            a['event_scores'] = combined_events_points
        a['name'] = a.get('athlete_name', '')
        a['multinations'] = is_multinations(a.get('name'), a.get('birth_year'), a.get('gender', ''))

    def _yildiz_excluded(a):
        return bool(
            a.get('selected_yildiz_multinations') or
            a.get('selected_yildiz_comen_cup_aralik') or a.get('selected_yildiz_comen_cup_nisan') or
            a.get('selected_yildiz_central_europe_aralik') or a.get('selected_yildiz_central_europe_nisan')
        )

    eligible = [a for a in athletes if not _yildiz_excluded(a)]
    excluded = [a for a in athletes if _yildiz_excluded(a)]
    for a in excluded:
        a['selected'] = '-'
        a['selected_slot'] = '-'
        a['tied'] = False
        a['ranking_key'] = ()
        a['top3_total'] = a.get('top3_total', 0)

    # Group by birth_year and gender (like rank_all does)
    by_group = defaultdict(list)
    for a in eligible:
        key = (a['birth_year'], a['gender'])
        by_group[key].append(a)

    # Apply rank_group to each eligible group
    all_ranked = []
    for (birth_year, gender), group in sorted(by_group.items()):
        ranked_group = rank_group(group)
        all_ranked.extend(ranked_group)
    all_ranked.extend(excluded)

    for a in all_ranked:
        a['selected_federasyon_karma'] = a.get('selected') in ('TR', 'BÖLGE')

    return all_ranked


def compute_selection_status(athletes: list) -> dict:
    """
    Compute selection status for athletes: TR, BÖLGE, or None.
    Uses combined_top3 + ranking_key for ranking (no minimum points baraj).
    Returns dict: {athlete_key: selection_type}
    """
    from collections import defaultdict

    selections = {}

    # Group by birth_year and region
    by_year_region = defaultdict(list)
    for athlete in athletes:
        if athlete.get('combined_top3', 0) <= 0:
            continue  # Skip athletes with no valid score

        key = (athlete['birth_year'], athlete.get('region', 0))
        by_year_region[key].append(athlete)

    # For each year+region, rank by combined_top3 + ranking_key
    for (birth_year, region), group in by_year_region.items():
        if birth_year not in SELECTION_QUOTAS:
            continue

        quota = SELECTION_QUOTAS[birth_year]

        # Sort by combined_top3 (desc) then ranking_key (tiebreaker)
        ranked = sorted(group, key=lambda a: (-a.get('combined_top3', 0), a.get('ranking_key', ())))

        for idx, athlete in enumerate(ranked):
            athlete_key = (athlete['athlete_name'], athlete['birth_year'], athlete['gender'])
            top3 = athlete.get('combined_top3', 0)

            # Skip athletes with 0 score
            if top3 <= 0:
                selections[athlete_key] = None
                continue

            # Determine region-based bölge limit
            if region == 1:
                bölge_limit = quota.get('region_1', 3)
            else:
                bölge_limit = quota.get('region_other', 2)

            tr_count = quota.get('tr', 8)

            # TR selection (national team)
            if idx < tr_count:
                selections[athlete_key] = 'TR'
            # BÖLGE selection (regional)
            elif idx < tr_count + bölge_limit:
                selections[athlete_key] = 'BÖLGE'
            else:
                selections[athlete_key] = None

    return selections


def normalize_athlete_data(athlete: dict, result: dict, overrides: dict) -> tuple:
    """
    Normalize athlete/result using overrides + Excel mapping.
    Returns (athlete_updated, result_updated).
    """
    # Check name override first
    name_override = get_name_override(
        athlete.get("name", ""),
        athlete.get("birth_year"),
        athlete.get("gender"),
        overrides
    )

    if name_override:
        athlete["name"] = name_override.get("canonical_name", athlete.get("name"))
        athlete["club_name"] = name_override.get("canonical_club")
        athlete["city"] = name_override.get("canonical_city")
        athlete["region"] = name_override.get("canonical_region", 0)

        result["club"] = name_override.get("canonical_club")
        result["city"] = name_override.get("canonical_city")
        result["region"] = name_override.get("canonical_region", 0)

        return athlete, result

    # Check club override
    club_override = get_club_override(athlete.get("club_name", ""), overrides)
    if club_override:
        athlete["club_name"] = club_override["club"]
        athlete["city"] = club_override["city"]
        athlete["region"] = club_override["region"]

        result["club"] = club_override["club"]
        result["city"] = club_override["city"]
        result["region"] = club_override["region"]

        return athlete, result

    # Fall back to Excel mapping
    lookup_result = lookup_club(athlete.get("club_name", ""))
    if lookup_result:
        athlete["city"] = lookup_result.get("city", "Unknown")
        athlete["region"] = lookup_result.get("region", 0)

        result["city"] = lookup_result.get("city", "Unknown")
        result["region"] = lookup_result.get("region", 0)

    return athlete, result


def process_lxf_upload(file_path: str, race_leg: str = 'antalya') -> dict:
    """
    Parse LXF file, normalize, and insert into fed_results table.
    Pipeline: parse → normalize → fed_results (batch)
    """
    import time
    try:
        t0_total = time.time()

        # Load manual overrides
        t0 = time.time()
        overrides = load_manual_overrides()
        logger.info(f"Loaded overrides: {len(overrides.get('name_overrides', []))} names, {len(overrides.get('club_aliases', []))} clubs (took {time.time()-t0:.2f}s)")

        # Parse LXF
        t0 = time.time()
        athletes, results = parse_lxf_file(file_path)
        t_parse = time.time() - t0
        logger.info(f"Parsed {len(athletes)} athletes, {len(results)} results from {race_leg} (took {t_parse:.2f}s)")

        # DEBUG: write parsing results to file
        debug_file = Path(tempfile.gettempdir()) / 'parse_debug.txt'
        with open(debug_file, 'w') as f:
            f.write(f"Parsed {len(athletes)} athletes, {len(results)} results\n")
            f.write(f"Sample athletes:\n")
            for i, a in enumerate(athletes[:5]):
                f.write(f"  [{i}] {a.get('firstname')} {a.get('lastname')} (ID: {a.get('athlete_id')})\n")

            # Find Cem Eren
            for a in athletes:
                if 'CEM' in a.get('firstname', '').upper() and 'EREN' in a.get('lastname', '').upper():
                    f.write(f"\nFOUND CEM EREN: ID {a.get('athlete_id')}\n")
                    # Count his results
                    count = len([r for r in results if r.get('athlete_id') == a.get('athlete_id')])
                    f.write(f"  Results count: {count}\n")

        # Batch collect all fed_results to insert
        fed_results_batch = []
        fed_athletes = {}  # Track unique athletes for fed_athlete_best later

        # Process each athlete
        for athlete in athletes:
            # Add birth_year if missing
            if 'birth_year' not in athlete or not athlete['birth_year']:
                athlete['birth_year'] = get_birth_year(athlete.get('birthdate'))

            # Find this athlete's results
            athlete_results = [r for r in results if r.get('athlete_id') == athlete.get('athlete_id')]

            if not athlete_results:
                continue

            # DEBUG: check if this is Cem Eren (with any encoding)
            full_check = f"{athlete.get('firstname', '')} {athlete.get('lastname', ''.upper())}".upper()
            if 'CEM' in full_check and 'EREN' in full_check:
                debug_file = Path(tempfile.gettempdir()) / 'cem_eren_debug.txt'
                with open(debug_file, 'w') as f:
                    f.write(f"FOUND CEM EREN!\n")
                    f.write(f"Raw name: firstname='{athlete.get('firstname', '')}' lastname='{athlete.get('lastname', '')}'\n")
                    f.write(f"Athlete results: {len(athlete_results)} items\n")
                    for i, r in enumerate(athlete_results):
                        f.write(f"  [{i}] {r.get('stroke')} {r.get('distance')}m: {r.get('time_text')} ({r.get('time_seconds')}s)\n")

            # Normalize and insert results
            for result in athlete_results:
                athlete, result = normalize_athlete_data(athlete, result, overrides)

            # Build full name
            full_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
            athlete['name'] = full_name

            # Store athlete key for fed_athlete_best
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

            # Batch collect each result into fed_results (without filtering - SQL will deduplicate later)
            for result in athlete_results:
                fed_result = {
                    'race_leg': race_leg,
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

        # Batch insert all fed_results at once
        t0 = time.time()
        fed_results_count = batch_insert_fed_results(fed_results_batch)
        t_insert = time.time() - t0
        logger.info(f"Batch inserted {fed_results_count} results into fed_results table (took {t_insert:.2f}s)")

        # Deduplicate fed_results: keep only best (fastest) time for each (athlete, stroke, distance)
        try:
            from database import get_connection
            conn = get_connection()

            # For each (athlete_name, stroke, distance), find and keep only the one with lowest time_seconds
            conn.execute("""
                DELETE FROM fed_results WHERE id IN (
                    SELECT r1.id FROM fed_results r1
                    INNER JOIN (
                        SELECT athlete_name, stroke, distance, MIN(time_seconds) as min_time
                        FROM fed_results
                        WHERE race_leg = ?
                        GROUP BY athlete_name, stroke, distance
                        HAVING COUNT(*) > 1
                    ) dup ON r1.athlete_name = dup.athlete_name
                           AND r1.stroke = dup.stroke
                           AND r1.distance = dup.distance
                           AND r1.time_seconds > dup.min_time
                    WHERE r1.race_leg = ?
                )
            """, (race_leg, race_leg))

            conn.commit()
            deleted = conn.total_changes
            conn.close()
            logger.info(f"Deduplicated fed_results: deleted {deleted} slower duplicate times")
        except Exception as e:
            logger.warning(f"Deduplication failed: {e}")

        # Compute and save best scores
        t0 = time.time()
        best_saved = compute_and_save_best_scores(race_leg)
        t_best = time.time() - t0
        logger.info(f"Computed and saved {best_saved} best scores (took {t_best:.2f}s)")

        t_total = time.time() - t0_total
        logger.info(f"TOTAL UPLOAD PROCESS: {t_total:.2f}s (parse: {t_parse:.2f}s, insert: {t_insert:.2f}s, best: {t_best:.2f}s)")

        return {
            "status": "success",
            "count": len(athletes),
            "results_imported": fed_results_count,
            "best_scores_computed": best_saved,
            "leg": race_leg,
            "message": f"Imported {len(athletes)} athletes, {fed_results_count} results, {best_saved} best scores"
        }

    except Exception as e:
        logger.error(f"Error processing LXF: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        logger.info(format % args)

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self.serve_index()
        elif self.path.startswith('/api/ranking'):
            self.serve_api_ranking()
        elif self.path.startswith('/api/regional'):
            self.serve_api_regional()
        elif self.path.startswith('/api/export'):
            self.handle_export()
        else:
            self.serve_static_file()

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/upload':
            self.handle_upload()
        elif self.path == '/api/delete-leg':
            self.handle_delete_leg()
        elif self.path == '/clear':
            self.handle_clear()
        else:
            self.send_error(404, "Not found")

    def serve_index(self):
        """Serve dashboard HTML."""
        try:
            html_path = Path(__file__).parent / "index.html"
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-length', len(html.encode('utf-8')))
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "index.html not found")

    def serve_static_file(self):
        """Serve static files from panel directory (CSS, JS, etc)."""
        # Remove leading slash and prevent directory traversal
        file_path = self.path.lstrip('/')
        if '..' in file_path or file_path.startswith('/'):
            self.send_error(403, "Forbidden")
            return

        file_full_path = Path(__file__).parent / file_path

        # Check if file exists and is in the panel directory
        try:
            file_full_path = file_full_path.resolve()
            panel_dir = Path(__file__).parent.resolve()
            if not str(file_full_path).startswith(str(panel_dir)):
                self.send_error(403, "Forbidden")
                return
        except (OSError, ValueError):
            self.send_error(403, "Forbidden")
            return

        if not file_full_path.exists() or not file_full_path.is_file():
            self.send_error(404, "Not found")
            return

        try:
            with open(file_full_path, 'rb') as f:
                content = f.read()

            # Determine content type
            content_type = 'application/octet-stream'
            if file_path.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif file_path.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            elif file_path.endswith('.html'):
                content_type = 'text/html; charset=utf-8'
            elif file_path.endswith('.json'):
                content_type = 'application/json; charset=utf-8'
            elif file_path.endswith('.png'):
                content_type = 'image/png'
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif file_path.endswith('.svg'):
                content_type = 'image/svg+xml'

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except IOError:
            self.send_error(500, "Error reading file")

    def serve_api_ranking(self):
        """Serve ranking API endpoint."""
        import time
        start_time = time.time()

        try:
            # Parse query params
            qs = urlparse(self.path).query
            params = parse_qs(qs)

            birth_year = None
            gender = None
            region = None
            leg = params.get('leg', ['combined'])[0]

            timing = {}

            if 'birth_year' in params:
                try:
                    birth_year = int(params['birth_year'][0])
                except ValueError:
                    pass

            if 'gender' in params:
                gender = params['gender'][0] if params['gender'][0] else None

            if 'region' in params:
                try:
                    region = int(params['region'][0])
                except ValueError:
                    pass

            # Get athlete rankings with full scoring (all legs computed).
            # IMPORTANT: do NOT pass birth_year or region here. Multinations/
            # Comen Cup/Central European Yıldızlar pool athletes across
            # multiple birth years (e.g. Multinations = 2011+2012+2013
            # combined), and Federasyon Karması's TR tier ranks nationally
            # across all regions — both need to see the FULL population
            # before select_all_yildizlar()/apply_selection_status_with_points()
            # run. Pre-filtering by birth_year or region here would silently
            # shrink those pools and produce wrong selections (e.g. a "2013
            # only" dashboard filter would compute Multinations from 2013
            # girls alone instead of the real 2011-2013 pool). gender is safe
            # to pre-filter since every selection rule already splits by
            # gender internally.
            t1 = time.time()
            athletes = get_athlete_rankings(None, gender, None)
            timing['get_rankings'] = time.time() - t1
            logger.info(f"API /ranking: get_athlete_rankings took {timing['get_rankings']:.2f}s (leg={leg}, gender={gender})")

            # Apply yıldızlar selections on the FULL population — see note above.
            t1 = time.time()
            athletes = select_all_yildizlar(athletes)
            athletes = select_all_gencler(athletes)
            timing['selections'] = time.time() - t1
            logger.info(f"API /ranking: select_all_yildizlar+gencler took {timing['selections']:.2f}s")

            # **Filter by leg/birth_year/region** for display only, now that
            # every selection has been computed on the full pool.
            t1 = time.time()
            if leg == 'antalya':
                athletes = [a for a in athletes if len(a['antalya_events']) > 0]
            elif leg == 'edirne':
                athletes = [a for a in athletes if len(a['edirne_events']) > 0]
            # for 'combined', show all athletes with any events
            #
            # birth_year is safe to filter here: Federasyon Karması TR/BÖLGE
            # quotas are entirely separate per birth_year (rank_group() never
            # compares across years), so narrowing now doesn't change the
            # outcome for the remaining year.
            #
            # region is NOT filtered here — TR is a single NATIONAL ranking
            # across all 6 regions for a given birth_year+gender. Filtering
            # by region before apply_selection_status_with_points() would
            # rank athletes only against their own region, handing TR slots
            # to athletes who wouldn't make the real national cutoff (this
            # was a real bug: passing region=1 put 8 Istanbul athletes in TR
            # who are actually only BÖLGE per the official roster). The
            # region filter is applied further below, after selection.
            if birth_year is not None:
                athletes = [a for a in athletes if a.get('birth_year') == birth_year]
            timing['filter_by_leg'] = time.time() - t1
            logger.info(f"API /ranking: filter_by_leg took {timing['filter_by_leg']:.2f}s, {len(athletes)} athletes")

            # Apply Federasyon Karması TR/BÖLGE selection status for every leg
            # (antalya/edirne/combined) — each tab shows its own slot, scoped
            # to that leg's events, excluding athletes already selected above
            # to Multinations/Comen Cup/Central European Yıldızlar.
            try:
                t1 = time.time()
                if leg == 'combined':
                    for a in athletes:
                        combined_events_points_only = {}
                        for (stroke, dist), data in a.get('combined_events', {}).items():
                            points = data.get('points', 0) if isinstance(data, dict) else data
                            combined_events_points_only[(stroke, dist)] = points
                        a['combined_events_for_ranking'] = combined_events_points_only

                athletes = apply_selection_status_with_points(athletes, leg=leg)

                timing['selection_status'] = time.time() - t1
                logger.info(f"API /ranking: apply_selection_status took {timing['selection_status']:.2f}s (leg={leg})")
            except Exception as e:
                logger.warning(f"Error applying selection status: {e}")
                # Fallback: set default values
                for a in athletes:
                    a['selected'] = '-'
                    a['selected_slot'] = '-'
                    a['multinations'] = False

            # Region filter for display, now that TR (national) has already
            # been computed against the full cross-region pool.
            if region is not None:
                athletes = [a for a in athletes if a.get('region') == region]

            # Transform to API response format
            response_athletes = []
            for athlete in athletes:
                # Determine which top3 to display based on leg selection
                if leg == 'antalya':
                    display_top3 = athlete['antalya_top3']
                elif leg == 'edirne':
                    display_top3 = athlete['edirne_top3']
                else:  # combined
                    display_top3 = athlete['combined_top3']

                # Convert events dicts: tuples → JSON arrays, include time
                def events_to_json(events_dict, times_dict=None):
                    result = {}
                    for (stroke, distance), points in events_dict.items():
                        key = json.dumps([stroke, distance])
                        time_text = times_dict.get((stroke, distance), '-') if times_dict else '-'
                        result[key] = {'points': points, 'time': time_text}
                    return result

                antalya_events_json = events_to_json(athlete['antalya_events'], athlete.get('antalya_events_time', {}))
                edirne_events_json = events_to_json(athlete['edirne_events'], athlete.get('edirne_events_time', {}))
                combined_events_json = events_to_json(athlete['combined_events'], athlete.get('combined_events_time', {}))

                # Show points for all birth years (federation selections apply to all ages)
                birth_year = athlete['birth_year']
                # display_top3 was already set above based on leg filter - don't override it
                selected = athlete.get('selected', '-')
                selected_slot = athlete.get('selected_slot', '-')
                multinations = athlete.get('multinations', False)

                response_athletes.append({
                    'athlete_name': athlete['athlete_name'],
                    'birth_year': athlete['birth_year'],
                    'gender': athlete['gender'],
                    'region': athlete['region'],
                    'city': athlete['city'],
                    'club': athlete['club'],
                    'antalya_top3': athlete['antalya_top3'],
                    'edirne_top3': athlete['edirne_top3'],
                    'combined_top3': athlete['combined_top3'],
                    'display_top3': display_top3,
                    'antalya_events': antalya_events_json,
                    'edirne_events': edirne_events_json,
                    'combined_events': combined_events_json,
                    'selected': selected,
                    'selected_slot': selected_slot,
                    'multinations': multinations,
                    'selected_yildiz_multinations': athlete.get('selected_yildiz_multinations', False),
                    'candidate_yildiz_multinations': athlete.get('candidate_yildiz_multinations', False),
                    'candidate_relay_yildiz_multinations': athlete.get('candidate_relay_yildiz_multinations', False),
                    'coach_called_yildiz_multinations': athlete.get('coach_called_yildiz_multinations', False),
                    'selected_yildiz_comen_cup_aralik': athlete.get('selected_yildiz_comen_cup_aralik', False),
                    'selected_yildiz_comen_cup_nisan': athlete.get('selected_yildiz_comen_cup_nisan', False),
                    'candidate_relay_yildiz_comen_cup_aralik': athlete.get('candidate_relay_yildiz_comen_cup_aralik', False),
                    'candidate_relay_yildiz_comen_cup_nisan': athlete.get('candidate_relay_yildiz_comen_cup_nisan', False),
                    'coach_called_yildiz_comen_cup_aralik': athlete.get('coach_called_yildiz_comen_cup_aralik', False),
                    'coach_called_yildiz_comen_cup_nisan': athlete.get('coach_called_yildiz_comen_cup_nisan', False),
                    'selected_yildiz_central_europe_aralik': athlete.get('selected_yildiz_central_europe_aralik', False),
                    'selected_yildiz_central_europe_nisan': athlete.get('selected_yildiz_central_europe_nisan', False),
                    'candidate_yildiz_central_europe_aralik': athlete.get('candidate_yildiz_central_europe_aralik', False),
                    'candidate_yildiz_central_europe_nisan': athlete.get('candidate_yildiz_central_europe_nisan', False),
                    'candidate_relay_yildiz_central_europe_aralik': athlete.get('candidate_relay_yildiz_central_europe_aralik', False),
                    'candidate_relay_yildiz_central_europe_nisan': athlete.get('candidate_relay_yildiz_central_europe_nisan', False),
                    'coach_called_yildiz_central_europe_aralik': athlete.get('coach_called_yildiz_central_europe_aralik', False),
                    'coach_called_yildiz_central_europe_nisan': athlete.get('coach_called_yildiz_central_europe_nisan', False),
                    'selected_multinations_gencler': athlete.get('selected_multinations_gencler', False),
                    'candidate_multinations_gencler': athlete.get('candidate_multinations_gencler', False),
                    'candidate_relay_multinations_gencler': athlete.get('candidate_relay_multinations_gencler', False),
                    'coach_called_multinations_gencler': athlete.get('coach_called_multinations_gencler', False),
                    'selected_avrupa_gencler': athlete.get('selected_avrupa_gencler', False),
                    'coach_called_avrupa_gencler': athlete.get('coach_called_avrupa_gencler', False),
                    'candidate_relay_avrupa_gencler': athlete.get('candidate_relay_avrupa_gencler', False),
                    'avrupa_gencler_event_count': len(athlete.get('avrupa_gencler_events', [])),
                })

            # All athletes visible (scoring applies to all age groups)

            # Send JSON response
            t1 = time.time()
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()

            response_json = json.dumps(response_athletes, ensure_ascii=False, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            timing['json_response'] = time.time() - t1

            total_time = time.time() - start_time
            logger.info(f"API /api/ranking TOTAL: {total_time:.2f}s | get_rankings={timing.get('get_rankings', 0):.2f}s | filter={timing.get('filter_by_leg', 0):.2f}s | selection={timing.get('selection_status', 0):.2f}s | selections={timing.get('selections', 0):.2f}s | json={timing.get('json_response', 0):.2f}s")

        except Exception as e:
            logger.error(f"Error in /api/ranking: {e}", exc_info=True)
            self.send_error(500, str(e))

    def serve_api_regional(self):
        """Serve regional rankings API endpoint."""
        try:
            # Parse query params
            qs = urlparse(self.path).query
            params = parse_qs(qs)

            region = None
            leg = params.get('leg', ['combined'])[0]

            if 'region' in params:
                try:
                    region = int(params['region'][0])
                except ValueError:
                    pass

            # Get the FULL population (region NOT passed here — TR is a
            # national ranking across all 6 regions; filtering by region
            # before selection would rank athletes only against their own
            # region and hand TR slots to athletes who wouldn't make the
            # real national cutoff — same bug already fixed in
            # serve_api_ranking()).
            athletes = get_athlete_rankings(None, None, None)

            # Yıldızlar selections on the full population, before anything
            # narrows the pool (same reasoning as serve_api_ranking()).
            athletes = select_all_yildizlar(athletes)
            athletes = select_all_gencler(athletes)

            # Filter by leg
            if leg == 'antalya':
                athletes = [a for a in athletes if len(a['antalya_events']) > 0]
            elif leg == 'edirne':
                athletes = [a for a in athletes if len(a['edirne_events']) > 0]

            # Apply selection status (similar to main ranking) on the full,
            # cross-region pool.
            for a in athletes:
                combined_events_points = {}
                for (stroke, dist), data in a.get('combined_events', {}).items():
                    points = data.get('points', 0) if isinstance(data, dict) else data
                    combined_events_points[(stroke, dist)] = points
                a['combined_events_for_ranking'] = combined_events_points

            athletes = apply_selection_status_with_points(athletes, leg=leg)

            # NOW filter to the requested region, for display only.
            if region is not None:
                athletes = [a for a in athletes if a.get('region') == region]

            # Sort by top3 within region
            if leg == 'antalya':
                athletes = sorted(athletes, key=lambda a: -a['antalya_top3'])
            elif leg == 'edirne':
                athletes = sorted(athletes, key=lambda a: -a['edirne_top3'])
            else:
                athletes = sorted(athletes, key=lambda a: -a['combined_top3'])

            # Build response (same format as main ranking)
            response_athletes = []
            for athlete in athletes:
                if leg == 'antalya':
                    display_top3 = athlete['antalya_top3']
                elif leg == 'edirne':
                    display_top3 = athlete['edirne_top3']
                else:
                    display_top3 = athlete['combined_top3']

                response_athletes.append({
                    'athlete_name': athlete['athlete_name'],
                    'birth_year': athlete['birth_year'],
                    'gender': athlete['gender'],
                    'region': athlete['region'],
                    'city': athlete['city'],
                    'club': athlete['club'],
                    'display_top3': display_top3,
                    'selected': athlete.get('selected', '-'),
                    'selected_slot': athlete.get('selected_slot', '-'),
                    'multinations': athlete.get('multinations', False),
                })

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()

            response_json = json.dumps(response_athletes, ensure_ascii=False, indent=2)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            logger.error(f"Error in /api/regional: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_export(self):
        """Handle export request - generate and return XLSX file."""
        try:
            # Parse query params
            qs = urlparse(self.path).query
            params = parse_qs(qs)

            leg = params.get('leg', ['combined'])[0]
            birth_year = None
            gender = None

            if 'birth_year' in params:
                try:
                    birth_year = int(params['birth_year'][0])
                except ValueError:
                    pass

            if 'gender' in params:
                gender = params['gender'][0] if params['gender'][0] else None

            # Get athlete rankings. birth_year is intentionally NOT passed here
            # — see the matching note in serve_api_ranking(): Multinations/
            # Comen Cup/Central European pool multiple birth years together,
            # so filtering before select_all_yildizlar() would compute those
            # selections from the wrong, narrowed pool.
            athletes = get_athlete_rankings(None, gender, None)

            # Yıldızlar selections FIRST, on the full population (same reason
            # as /api/ranking: nationwide quotas must see every eligible
            # athlete before the leg filter shrinks the pool).
            athletes = select_all_yildizlar(athletes)
            athletes = select_all_gencler(athletes)

            # Filter by leg/birth_year for display, now that every selection
            # has been computed on the full pool.
            if leg == 'antalya':
                athletes = [a for a in athletes if len(a['antalya_events']) > 0]
            elif leg == 'edirne':
                athletes = [a for a in athletes if len(a['edirne_events']) > 0]
            if birth_year is not None:
                athletes = [a for a in athletes if a.get('birth_year') == birth_year]

            # Apply selection status BEFORE converting to JSON (tuple keys needed)
            try:
                # Extract points only from combined_events for rank_group (ignore time)
                for a in athletes:
                    combined_events_points_only = {}
                    for (stroke, dist), data in a.get('combined_events', {}).items():
                        points = data.get('points', 0) if isinstance(data, dict) else data
                        combined_events_points_only[(stroke, dist)] = points
                    a['combined_events_for_ranking'] = combined_events_points_only

                athletes = apply_selection_status_with_points(athletes, leg=leg)
            except Exception as e:
                logger.warning(f"Error applying selection status: {e}")
                # Fallback: set default values
                for a in athletes:
                    a['selected'] = '-'
                    a['selected_slot'] = '-'
                    a['multinations'] = False

            # Sort and prepare for export
            athletes_for_export = []
            for idx, athlete in enumerate(athletes, 1):
                if leg == 'antalya':
                    display_top3 = athlete['antalya_top3']
                elif leg == 'edirne':
                    display_top3 = athlete['edirne_top3']
                else:
                    display_top3 = athlete['combined_top3']

                athletes_for_export.append({
                    'athlete_name': athlete['athlete_name'],
                    'birth_year': athlete['birth_year'],
                    'gender': athlete['gender'],
                    'city': athlete['city'],
                    'region': athlete['region'],
                    'display_top3': display_top3,
                    'selected': athlete.get('selected', '-'),
                })

            # Generate XLSX
            xlsx_bytes = create_rankings_xlsx(athletes_for_export, leg)

            # Send file
            self.send_response(200)
            self.send_header('Content-type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Disposition', f'attachment; filename="siralama_{leg}.xlsx"')
            self.send_header('Content-Length', len(xlsx_bytes))
            self.end_headers()

            self.wfile.write(xlsx_bytes)

            logger.info(f"Exported {len(athletes_for_export)} athletes to Excel ({leg})")

        except Exception as e:
            logger.error(f"Error exporting: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_clear(self):
        """Handle database clear request - clear both old and federated tables."""
        try:
            clear_athletes()
            clear_fed_tables()
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))

    def handle_delete_leg(self):
        """Delete all results for a specific race leg."""
        try:
            # Read JSON body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Empty body")
                return

            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            leg = data.get('leg', '').lower()

            if leg not in ['antalya', 'edirne']:
                self.send_error(400, "Invalid leg. Must be 'antalya' or 'edirne'")
                return

            # Delete from both tables
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM fed_results WHERE race_leg = ?", (leg,))
            deleted_results = cursor.rowcount

            cursor.execute("DELETE FROM fed_athlete_best WHERE best_leg = ?", (leg,))
            deleted_best = cursor.rowcount

            conn.commit()
            conn.close()

            total_deleted = deleted_results + deleted_best
            logger.info(f"Deleted {deleted_results} results and {deleted_best} best scores for leg '{leg}'")

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()

            response = {
                "status": "success",
                "message": f"Deleted all results for {leg}",
                "deleted_count": total_deleted
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error deleting leg: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_upload(self):
        """Handle file upload."""
        import time
        t0_total = time.time()
        try:
            # Parse multipart form data
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No file provided")
                return

            # Read content as binary
            t0 = time.time()
            content = self.rfile.read(content_length)
            t_read = time.time() - t0
            logger.info(f"Read {content_length} bytes in {t_read:.2f}s")

            # Parse multipart form data (binary-safe)
            # Extract boundary from content-type header
            content_type = self.headers.get('Content-Type', '')
            boundary = None
            if 'boundary=' in content_type:
                boundary = '--' + content_type.split('boundary=')[1].strip()

            if not boundary:
                self.send_error(400, "Invalid multipart data")
                return

            # Find file content between boundaries (binary-safe)
            file_content_bytes = None
            filename = None
            boundary_bytes = boundary.encode('utf-8')

            # Split by boundary
            parts = content.split(boundary_bytes)

            for part in parts:
                if b'filename=' in part:
                    # Extract filename (text parsing is safe here)
                    part_str = part.decode('utf-8', errors='ignore')
                    for line in part_str.split('\n'):
                        if 'filename=' in line:
                            try:
                                filename = line.split('filename="')[1].split('"')[0]
                            except IndexError:
                                pass
                            break

                    # Extract binary content (keep as bytes)
                    # Find the double newline that separates headers from content
                    content_start = None

                    # Try CRLF first (Windows style)
                    idx = part.find(b'\r\n\r\n')
                    if idx != -1:
                        content_start = part[idx + 4:]  # Skip the 4 bytes of \r\n\r\n
                    else:
                        # Try LF only (Unix style)
                        idx = part.find(b'\n\n')
                        if idx != -1:
                            content_start = part[idx + 2:]  # Skip the 2 bytes of \n\n

                    if content_start is not None:
                        # Remove trailing CRLF or LF before next boundary
                        if content_start.endswith(b'\r\n'):
                            content_start = content_start[:-2]
                        elif content_start.endswith(b'\n'):
                            content_start = content_start[:-1]

                        # Save to temp file (binary mode, don't delete on close)
                        with tempfile.NamedTemporaryFile(suffix='.lxf', delete=False) as tmp:
                            tmp.write(content_start)
                            file_content_bytes = tmp.name
                        break

            if not file_content_bytes:
                self.send_error(400, "No file content found")
                return

            # Process LXF using MiltiTakimPipeline (with cleanup in finally block)
            result = None
            t_process = 0
            try:
                race_leg = 'antalya'  # default
                if filename and 'edirne' in filename.lower():
                    race_leg = 'edirne'

                t0 = time.time()
                pipeline = MiltiTakimPipeline()
                result = pipeline.process(file_content_bytes, race_leg=race_leg)
                t_process = time.time() - t0
                logger.info(f"MiltiTakimPipeline.process took {t_process:.2f}s")
            finally:
                # Clean up temp file (always happens, even on exception)
                Path(file_content_bytes).unlink(missing_ok=True)

            # Send response
            t0 = time.time()
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()

            response_json = json.dumps(result, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
            t_response = time.time() - t0

            t_total_http = time.time() - t0_total
            logger.info(f"TOTAL HTTP UPLOAD: {t_total_http:.2f}s (read: {t_read:.2f}s, process: {t_process:.2f}s, response: {t_response:.2f}s)")

        except Exception as e:
            logger.error(f"Error handling upload: {e}", exc_info=True)
            # Send JSON error response with 400 status (not HTML error page)
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()

            error_response = {'success': False, 'error': str(e)}
            response_json = json.dumps(error_response, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))


def main():
    """Start HTTP server."""
    init_db()

    # Run database migrations
    from federasyon.db_fed import migrate_add_selection_columns
    migrate_add_selection_columns()

    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8765))
    server = HTTPServer((host, port), DashboardHandler)
    print("=" * 60)
    print("Milli Takım Seçme — Dashboard")
    print("=" * 60)
    print(f"Server running: http://{host}:{port}")
    print(f"Database: {DB_PATH}")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
