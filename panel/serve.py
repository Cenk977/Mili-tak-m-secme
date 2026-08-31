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

from database import init_db, insert_athlete, insert_result, get_athletes_by_filter, clear_athletes, get_missing_clubs_from_db
from modules.lxf_parser import parse_lxf_file, get_birth_year
from config import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_lxf_upload(file_path: str) -> dict:
    """
    Parse LXF file and insert athletes/results into database.
    Returns: { "status": "success|error", "count": int, "missing_clubs": list }
    """
    try:
        # Parse LXF
        athletes, results = parse_lxf_file(file_path)
        logger.info(f"Parsed {len(athletes)} athletes, {len(results)} results")

        # Insert athletes
        for athlete in athletes:
            # Add birth_year if not present
            if 'birth_year' not in athlete or not athlete['birth_year']:
                athlete['birth_year'] = get_birth_year(athlete.get('birthdate'))

            insert_athlete(athlete)

        # Insert results
        for result in results:
            result['race_source'] = 'antalya'  # Could be dynamic
            insert_result(result)

        # Get missing clubs
        missing = get_missing_clubs_from_db()

        return {
            "status": "success",
            "count": len(athletes),
            "missing_clubs": list(missing),
            "message": f"Imported {len(athletes)} athletes"
        }

    except Exception as e:
        logger.error(f"Error processing LXF: {e}")
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

            if 'birth_year' in params:
                try:
                    birth_year = int(params['birth_year'][0])
                except ValueError:
                    pass

            if 'gender' in params:
                gender = params['gender'][0] if params['gender'][0] else None

            # Query database
            athletes = get_athletes_by_filter(birth_year, gender)

            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()

            response_json = json.dumps(athletes, ensure_ascii=False, indent=2)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            logger.error(f"Error in /api/ranking: {e}")
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

            # Read content
            content = self.rfile.read(content_length)

            # Simple multipart parsing (basic, works for single file)
            # Extract filename and file content
            content_str = content.decode('utf-8', errors='ignore')

            # Split by boundary
            boundary = None
            for line in content_str.split('\n')[:5]:
                if line.startswith('--'):
                    boundary = line.strip()
                    break

            if not boundary:
                self.send_error(400, "Invalid multipart data")
                return

            # Find file content between boundaries
            parts = content_str.split(boundary)
            file_content_bytes = None
            filename = None

            for part in parts:
                if 'filename=' in part:
                    # Extract filename
                    for line in part.split('\n'):
                        if 'filename=' in line:
                            filename = line.split('filename="')[1].split('"')[0]
                            break

                    # Extract binary content
                    # Find the content after headers
                    double_newline = part.find('\n\n')
                    if double_newline != -1:
                        # Re-encode the bytes since we had to decode for parsing
                        content_start = part[double_newline + 2:]
                        # Find end before next boundary
                        content_end = content_start.rfind('\n--')
                        if content_end == -1:
                            content_end = content_start.rfind('\r\n--')
                        if content_end == -1:
                            content_end = len(content_start)

                        # Save to temp file
                        with tempfile.NamedTemporaryFile(suffix='.lxf', delete=False) as tmp:
                            tmp.write(content_start[:content_end].encode('latin-1'))
                            file_content_bytes = tmp.name
                        break

            if not file_content_bytes:
                self.send_error(400, "No file content found")
                return

            # Process LXF
            result = process_lxf_upload(file_content_bytes)

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
