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
    get_athlete_rankings, get_fed_results, clear_fed_tables
)
from modules.lxf_parser import parse_lxf_file, get_birth_year
from modules.m1_normalize import normalize_for_lookup
from modules.m3_age import parse_birthdate
from modules.m4_mapping import lookup_club
from federasyon.scoring_tables import TABLES, POINTS, SELECTION_QUOTAS
from federasyon.scorer import score_event, score_athlete_row, merge_scores, best_scores_sequence, compute_ranking_key
from federasyon.ranker import rank_all
from config import DB_PATH, TARGET_AGE_GROUPS, COMPETITION_YEAR

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
    and save to fed_athlete_best. Returns count saved.
    """
    from collections import defaultdict

    results = get_fed_results(race_leg)
    logger.info(f"Computing best scores from {len(results)} fed_results")

    # Group by (athlete_name, birth_year, gender, stroke, distance)
    grouped = defaultdict(list)
    for r in results:
        key = (r['athlete_name'], r['birth_year'], r['gender'], r['stroke'], r['distance'])
        grouped[key].append(r)

    saved_count = 0

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

        # Save to fed_athlete_best
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

        if insert_fed_athlete_best(best_dict):
            saved_count += 1

    logger.info(f"Saved {saved_count} best scores to fed_athlete_best")
    return saved_count


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
    Pipeline: parse → normalize → fed_results
    """
    try:
        # Load manual overrides
        overrides = load_manual_overrides()
        logger.info(f"Loaded overrides: {len(overrides.get('name_overrides', []))} names, {len(overrides.get('club_aliases', []))} clubs")

        # Parse LXF
        athletes, results = parse_lxf_file(file_path)
        logger.info(f"Parsed {len(athletes)} athletes, {len(results)} results from {race_leg}")

        fed_results_count = 0
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

            # Insert each result into fed_results
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

                if insert_fed_result(fed_result):
                    fed_results_count += 1

        logger.info(f"Inserted {fed_results_count} results into fed_results table")

        # Compute and save best scores
        best_saved = compute_and_save_best_scores(race_leg)

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
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/upload':
            self.handle_upload()
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

    def serve_api_ranking(self):
        """Serve ranking API endpoint."""
        try:
            # Parse query params
            qs = urlparse(self.path).query
            params = parse_qs(qs)

            birth_year = None
            gender = None
            region = None
            leg = params.get('leg', ['combined'])[0]

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

            # Get athlete rankings with full scoring (all legs computed)
            athletes = get_athlete_rankings(birth_year, gender, region)

            # Compute selection status based on combined scoring
            selections = compute_selection_status(athletes)

            # Transform to API response format
            response_athletes = []
            for athlete in athletes:
                athlete_key = (athlete['athlete_name'], athlete['birth_year'], athlete['gender'])

                # Determine which top3 to display based on leg selection
                if leg == 'antalya':
                    display_top3 = athlete['antalya_top3']
                elif leg == 'edirne':
                    display_top3 = athlete['edirne_top3']
                else:  # combined
                    display_top3 = athlete['combined_top3']

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
                    'selection_type': selections.get(athlete_key),
                })

            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()

            response_json = json.dumps(response_athletes, ensure_ascii=False, indent=2)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            logger.error(f"Error in /api/ranking: {e}", exc_info=True)
            self.send_error(500, str(e))

    def handle_clear(self):
        """Handle database clear request."""
        try:
            clear_athletes()
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))

    def handle_upload(self):
        """Handle file upload."""
        try:
            # Parse multipart form data
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No file provided")
                return

            # Read content as binary
            content = self.rfile.read(content_length)

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

            # Process LXF - detect race leg from filename
            race_leg = 'antalya'  # default
            if filename and 'edirne' in filename.lower():
                race_leg = 'edirne'

            result = process_lxf_upload(file_content_bytes, race_leg=race_leg)

            # Clean up temp file
            Path(file_content_bytes).unlink()

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()

            response_json = json.dumps(result, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling upload: {e}", exc_info=True)
            self.send_error(500, str(e))


def main():
    """Start HTTP server."""
    init_db()

    server = HTTPServer(('localhost', 8765), DashboardHandler)
    print("=" * 60)
    print("Milli Takım Seçme — Dashboard")
    print("=" * 60)
    print(f"Server running: http://localhost:8765")
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
