# Phase 2 Implementation Plan: API + City/Region Mapping

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate city/region mapping from Excel, build HTTP API endpoint, and enable LXF file upload with athlete ranking computation.

**Architecture:** Minimal, config-driven. Parser extracts athletes → mapping module looks up city/region → database stores → API serves JSON. No external servers, SQLite only.

**Tech Stack:** Python 3.9+, openpyxl (Excel), sqlite3 (built-in), http.server (built-in)

**Spec:** `docs/superpowers/specs/2026-08-31-phase2-api-mapping-design.md`

---

## Global Constraints

- Encoding: UTF-8 everywhere (file I/O, JSON output)
- Database: SQLite, path `config.DB_PATH` = `data/selection.db`
- JSON output: `ensure_ascii=False` (Turkish characters)
- Simplicity: No database sync, no conflict resolution (Phase 3)
- Error handling: Log missing clubs, fallback to `region=0`
- Testing: Manual HTTP + curl (no automated test suite yet)

---

## File Structure

**Create:**
- `database/db.py` — Database schema, initialization, CRUD operations
- `modules/m4_mapping.py` — Excel → club lookup with caching
- `panel/serve.py` — HTTP server, `/upload`, `/api/ranking`, `/` endpoints
- `panel/index.html` — Dashboard HTML (upload form + results table)
- `panel/__init__.py` — Empty Python package marker

**Modify:**
- `modules/lxf_parser.py` — Add import, lookup_club() calls, populate city/region
- `config.py` — Add MAPPING_EXCEL_PATH, MAPPING_SHEET_NAME, column indices

**No changes needed:**
- `requirements.txt` — openpyxl already present
- `.gitignore` — Already updated (data/results/*)

---

## Task Breakdown

### Task 1: Database Layer (`database/db.py`)

**Files:**
- Create: `database/db.py`
- Modify: `database/__init__.py` (export init_db)

**Interfaces:**
- Produces: 
  - `init_db()` → None (creates tables if missing)
  - `get_connection() -> sqlite3.Connection`
  - `insert_athlete(athlete_dict: Dict) -> bool`
  - `get_athletes_by_filter(birth_year: int, gender: str | None) -> List[Dict]`
  - `update_athlete_ranking(athlete_id: str, score: int, selected: bool, selection_type: str | None) -> bool`
  - `clear_athletes() -> bool`

- [ ] **Step 1: Write database schema file**

Create `database/db.py`:

```python
"""
Database layer for Milli Takım Seçme
SQLite3 backend, UTF-8 encoding
"""

import sqlite3
from pathlib import Path
from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Get SQLite connection with UTF-8 row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database, create tables if missing."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Athletes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS athletes (
            athlete_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            firstname TEXT,
            lastname TEXT,
            birthdate TEXT,
            birth_year INTEGER,
            gender TEXT,
            club_id TEXT,
            club_name TEXT,
            city TEXT DEFAULT 'Unknown',
            region INTEGER DEFAULT 0,
            best_score INTEGER,
            selected BOOLEAN DEFAULT 0,
            selection_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Results table (for tracking individual race results)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            athlete_id TEXT NOT NULL,
            event_id TEXT,
            distance INTEGER,
            stroke TEXT,
            time_text TEXT,
            time_seconds REAL,
            place INTEGER,
            points TEXT,
            race_source TEXT,
            FOREIGN KEY (athlete_id) REFERENCES athletes(athlete_id)
        )
    """)
    
    # Sync log (for tracking Excel imports)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            rows_loaded INTEGER,
            rows_skipped INTEGER,
            notes TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def insert_athlete(athlete_dict: dict) -> bool:
    """Insert or replace athlete record."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO athletes (
                athlete_id, name, firstname, lastname, birthdate, birth_year,
                gender, club_id, club_name, city, region, best_score, 
                selected, selection_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            athlete_dict.get('athlete_id'),
            f"{athlete_dict.get('firstname', '')} {athlete_dict.get('lastname', '')}".strip(),
            athlete_dict.get('firstname'),
            athlete_dict.get('lastname'),
            athlete_dict.get('birthdate'),
            athlete_dict.get('birth_year'),
            athlete_dict.get('gender'),
            athlete_dict.get('club_id'),
            athlete_dict.get('club_name', 'Unknown'),
            athlete_dict.get('city', 'Unknown'),
            athlete_dict.get('region', 0),
            athlete_dict.get('best_score'),
            athlete_dict.get('selected', 0),
            athlete_dict.get('selection_type'),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting athlete: {e}")
        return False
    finally:
        conn.close()


def insert_result(result_dict: dict) -> bool:
    """Insert race result."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO results (
                athlete_id, event_id, distance, stroke, time_text,
                time_seconds, place, points, race_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_dict.get('athlete_id'),
            result_dict.get('event_id'),
            result_dict.get('distance'),
            result_dict.get('stroke'),
            result_dict.get('time_text'),
            result_dict.get('time_seconds'),
            result_dict.get('place'),
            result_dict.get('points'),
            result_dict.get('race_source', 'unknown'),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting result: {e}")
        return False
    finally:
        conn.close()


def get_athletes_by_filter(birth_year: int = None, gender: str = None) -> list:
    """
    Get athletes filtered by birth_year and/or gender.
    Returns list of dicts with all columns.
    """
    conn = get_connection()
    query = "SELECT * FROM athletes WHERE selected = 1"
    params = []
    
    if birth_year:
        query += " AND birth_year = ?"
        params.append(birth_year)
    
    if gender:
        query += " AND gender = ?"
        params.append(gender)
    
    query += " ORDER BY best_score DESC"
    
    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_all_athletes() -> list:
    """Get all athletes from database."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM athletes ORDER BY best_score DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_athlete_ranking(athlete_id: str, score: int, selected: bool, selection_type: str = None) -> bool:
    """Update athlete's score and selection status."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE athletes
            SET best_score = ?, selected = ?, selection_type = ?, updated_at = CURRENT_TIMESTAMP
            WHERE athlete_id = ?
        """, (score, selected, selection_type, athlete_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating athlete: {e}")
        return False
    finally:
        conn.close()


def clear_athletes() -> bool:
    """Delete all athlete records (for re-import)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM athletes")
        conn.execute("DELETE FROM results")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing athletes: {e}")
        return False
    finally:
        conn.close()


def get_missing_clubs_from_db() -> list:
    """Get list of unique clubs with region=0 (unmapped)."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT club_name FROM athletes
            WHERE region = 0
            ORDER BY club_name
        """)
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()
```

- [ ] **Step 2: Update `database/__init__.py` to export functions**

```python
from database.db import (
    init_db,
    get_connection,
    insert_athlete,
    insert_result,
    get_athletes_by_filter,
    get_all_athletes,
    update_athlete_ranking,
    clear_athletes,
    get_missing_clubs_from_db,
)

__all__ = [
    'init_db',
    'get_connection',
    'insert_athlete',
    'insert_result',
    'get_athletes_by_filter',
    'get_all_athletes',
    'update_athlete_ranking',
    'clear_athletes',
    'get_missing_clubs_from_db',
]
```

- [ ] **Step 3: Test database initialization**

Run:
```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
python -c "from database.db import init_db; init_db(); print('✓ Database initialized')"
```

Expected: 
- No errors
- `data/selection.db` created
- Tables: `athletes`, `results`, `sync_log`

- [ ] **Step 4: Commit**

```bash
git add database/db.py database/__init__.py
git commit -m "feat: add database schema and CRUD operations"
```

---

### Task 2: Config Updates

**Files:**
- Modify: `config.py`

**Interfaces:**
- Produces:
  - `MAPPING_EXCEL_PATH: str`
  - `MAPPING_SHEET_NAME: str`
  - `MAPPING_DATA_START_ROW: int`
  - `COL_CLUB_ALT: int` (0 = Column A)
  - `COL_CLUB_CANONICAL: int` (2 = Column C)
  - `COL_CITY: int` (4 = Column E)
  - `COL_REGION: int` (6 = Column G)

- [ ] **Step 1: Read current config.py and add mapping constants**

Add to `config.py` after existing constants:

```python
# ─────────────────────────────────────────────────────────────────────────────
# Excel Mapping Configuration
# ─────────────────────────────────────────────────────────────────────────────

MAPPING_EXCEL_PATH = "Kulüp Şehir Mapping Exceli/Kulüp Şehir Mapping.xlsx"
MAPPING_SHEET_NAME = "Kulüp-Bölge-Şehir"

# Column indices (0-based)
# Excel columns: A=0, B=1, C=2, ... G=6
MAPPING_DATA_START_ROW = 5    # Row 5 (after header rows 1-4)
COL_CLUB_ALT = 0              # Column A: Kulüp Alternatif
COL_CLUB_CANONICAL = 2        # Column C: Kulüp Tekil
COL_CITY = 4                  # Column E: Şehir
COL_REGION = 6                # Column G: Bölge
```

- [ ] **Step 2: Commit**

```bash
git add config.py
git commit -m "config: add Excel mapping constants"
```

---

### Task 3: Mapping Module (`modules/m4_mapping.py`)

**Files:**
- Create: `modules/m4_mapping.py`
- Modify: `modules/__init__.py` (optional export)

**Interfaces:**
- Consumes:
  - `config.MAPPING_EXCEL_PATH`
  - `config.MAPPING_SHEET_NAME`
  - `config.COL_*` constants
- Produces:
  - `class ClubInfo(TypedDict)` with `city`, `region`, `club_canonical`
  - `load_mapping() -> None` (idempotent, caches)
  - `lookup_club(club_name: str) -> ClubInfo | None`
  - `get_missing_clubs(athletes: List[Dict]) -> Set[str]`

- [ ] **Step 1: Write mapping module**

Create `modules/m4_mapping.py`:

```python
"""
m4_mapping.py — Club → City → Region lookup
Reads Excel "Kulüp Şehir Mapping.xlsx", caches in memory.
"""

from typing import TypedDict, Optional
import openpyxl
import logging

from config import (
    MAPPING_EXCEL_PATH,
    MAPPING_SHEET_NAME,
    MAPPING_DATA_START_ROW,
    COL_CLUB_ALT,
    COL_CLUB_CANONICAL,
    COL_CITY,
    COL_REGION,
)

logger = logging.getLogger(__name__)


class ClubInfo(TypedDict):
    """Club mapping info."""
    city: str
    region: int
    club_canonical: str


# Global cache
_mapping_cache: Optional[dict[str, ClubInfo]] = None


def load_mapping():
    """
    Load Excel mapping into memory cache.
    Idempotent — only loads once, subsequent calls use cache.
    """
    global _mapping_cache
    
    if _mapping_cache is not None:
        return  # Already loaded
    
    _mapping_cache = {}
    
    try:
        wb = openpyxl.load_workbook(MAPPING_EXCEL_PATH, read_only=True, data_only=True)
    except FileNotFoundError:
        logger.error(f"Mapping Excel not found: {MAPPING_EXCEL_PATH}")
        return
    
    if MAPPING_SHEET_NAME not in wb.sheetnames:
        logger.error(f"Sheet '{MAPPING_SHEET_NAME}' not found in {MAPPING_EXCEL_PATH}")
        wb.close()
        return
    
    ws = wb[MAPPING_SHEET_NAME]
    
    # Iterate rows starting from MAPPING_DATA_START_ROW
    for row_idx, row in enumerate(ws.iter_rows(min_row=MAPPING_DATA_START_ROW, values_only=True), start=MAPPING_DATA_START_ROW):
        if not row or len(row) < COL_REGION + 1:
            continue
        
        # Extract columns
        club_alt = row[COL_CLUB_ALT] if COL_CLUB_ALT < len(row) else None
        club_canonical = row[COL_CLUB_CANONICAL] if COL_CLUB_CANONICAL < len(row) else None
        city = row[COL_CITY] if COL_CITY < len(row) else None
        region = row[COL_REGION] if COL_REGION < len(row) else None
        
        # Skip if critical fields missing
        if not city or region is None:
            continue
        
        # Use alt name if present, else canonical
        club_name = club_alt or club_canonical
        if not club_name:
            continue
        
        # Normalize key (uppercase)
        key = str(club_name).strip().upper()
        
        try:
            region_int = int(region)
        except (ValueError, TypeError):
            logger.warning(f"Invalid region for {club_name}: {region}")
            continue
        
        # Store in cache
        _mapping_cache[key] = {
            'city': str(city).strip(),
            'region': region_int,
            'club_canonical': str(club_canonical or club_alt).strip(),
        }
    
    wb.close()
    logger.info(f"Loaded {len(_mapping_cache)} clubs from Excel")


def lookup_club(club_name: str) -> Optional[ClubInfo]:
    """
    Look up club in cached mapping.
    Returns ClubInfo with city/region, or None if not found.
    """
    if not club_name:
        return None
    
    load_mapping()
    
    if _mapping_cache is None:
        return None
    
    key = str(club_name).strip().upper()
    return _mapping_cache.get(key)


def get_missing_clubs(athletes: list) -> set:
    """
    Get set of club names that don't map to a city/region.
    Useful for logging/debugging.
    """
    missing = set()
    for athlete in athletes:
        club_name = athlete.get('club_name')
        if club_name and not lookup_club(club_name):
            missing.add(club_name)
    return missing
```

- [ ] **Step 2: Test mapping module in isolation**

Run:
```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
python -c "
from modules.m4_mapping import lookup_club
result = lookup_club('ANKARA BEL. SK')
print(f'Result: {result}')
print(f'City: {result[\"city\"] if result else \"Not found\"}')
"
```

Expected: Should find "ANKARA BEL. SK" or similar club and return city/region.

- [ ] **Step 3: Commit**

```bash
git add modules/m4_mapping.py
git commit -m "feat: add Excel club → city/region mapping module"
```

---

### Task 4: Parser Integration (`modules/lxf_parser.py`)

**Files:**
- Modify: `modules/lxf_parser.py`

**Interfaces:**
- Consumes:
  - `lookup_club(club_name: str)` from m4_mapping
- Produces:
  - Same `parse_lxf_file()` signature, but athletes now have `city` and `region` fields

- [ ] **Step 1: Add import and lookup call in parse_lxf_file()**

At top of `modules/lxf_parser.py`, add import:

```python
from modules.m4_mapping import lookup_club
```

Find the line that creates the athlete dict (around line 56-65):

```python
athlete = {
    'athlete_id': athlete_id,
    'firstname': athlete_elem.get('firstname'),
    'lastname': athlete_elem.get('lastname'),
    'birthdate': athlete_elem.get('birthdate'),
    'gender': athlete_elem.get('gender'),
    'license': athlete_elem.get('license'),
    'club_id': None,
    'club_name': None,
}

# Get club info if available
club_elem = athlete_elem.find('.//CLUB')
if club_elem is not None:
    athlete['club_id'] = club_elem.get('clubid')
    athlete['club_name'] = club_elem.get('clubname')
```

Replace with:

```python
athlete = {
    'athlete_id': athlete_id,
    'firstname': athlete_elem.get('firstname'),
    'lastname': athlete_elem.get('lastname'),
    'birthdate': athlete_elem.get('birthdate'),
    'gender': athlete_elem.get('gender'),
    'license': athlete_elem.get('license'),
    'club_id': None,
    'club_name': None,
    'city': 'Unknown',      # ← ADD
    'region': 0,            # ← ADD
}

# Get club info if available
club_elem = athlete_elem.find('.//CLUB')
if club_elem is not None:
    athlete['club_id'] = club_elem.get('clubid')
    athlete['club_name'] = club_elem.get('clubname')
    
    # ← ADD: Look up city/region from Excel mapping
    if athlete['club_name']:
        mapping = lookup_club(athlete['club_name'])
        if mapping:
            athlete['city'] = mapping['city']
            athlete['region'] = mapping['region']
```

- [ ] **Step 2: Test parser with Antalya LXF**

Run:
```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
python -c "
from modules.lxf_parser import parse_lxf_file
athletes, results = parse_lxf_file('data/antalya_millitakim_secme_sonuc.lxf')
print(f'Parsed {len(athletes)} athletes')
for a in athletes[:3]:
    print(f\"  {a['firstname']} {a['lastname']}: {a['club_name']} → {a['city']} (region {a['region']})\")
"
```

Expected: 
- 2,888 results parsed
- Athletes have `city` and `region` fields populated (or 'Unknown'/0 if not in mapping)

- [ ] **Step 3: Commit**

```bash
git add modules/lxf_parser.py
git commit -m "feat: integrate city/region mapping into LXF parser"
```

---

### Task 5: HTTP Panel - Server Setup (`panel/serve.py`)

**Files:**
- Create: `panel/serve.py`
- Create: `panel/__init__.py`

**Interfaces:**
- Consumes:
  - `parse_lxf_file()` from modules
  - `insert_athlete()`, `get_athletes_by_filter()` from database
  - `lookup_club()` from m4_mapping
- Produces:
  - HTTP server on port 8765
  - Endpoints: GET /, POST /upload, GET /api/ranking

- [ ] **Step 1: Create empty `panel/__init__.py`**

```python
# panel package
```

- [ ] **Step 2: Write `panel/serve.py` - Part A: Helper functions and setup**

Create `panel/serve.py`:

```python
#!/usr/bin/env python3
"""
panel/serve.py — HTTP server for Milli Takım Seçme Dashboard

Endpoints:
  GET  /                    — Dashboard HTML
  POST /upload              — Upload LXF file, parse, insert to DB
  GET  /api/ranking         — Get selected athletes (JSON)
"""

import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

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
```

- [ ] **Step 3: Test server startup**

Run:
```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
timeout 5 python panel/serve.py
```

Expected:
- Server starts (outputs "Server running: http://localhost:8765")
- Stops after 5 seconds
- No errors

- [ ] **Step 4: Commit**

```bash
git add panel/serve.py panel/__init__.py
git commit -m "feat: add HTTP server with /upload and /api/ranking endpoints"
```

---

### Task 6: Dashboard HTML (`panel/index.html`)

**Files:**
- Create: `panel/index.html`

**Interfaces:**
- Consumes:
  - HTTP GET / (serves this file)
  - HTTP POST /upload (form submission)
  - HTTP GET /api/ranking (fetch for results)
- Produces:
  - Interactive form + results table

- [ ] **Step 1: Write dashboard HTML**

Create `panel/index.html`:

```html
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Milli Takım Seçme — Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            padding: 30px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .section {
            margin-bottom: 40px;
            border-bottom: 1px solid #eee;
            padding-bottom: 30px;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        h2 {
            color: #333;
            font-size: 18px;
            margin-bottom: 15px;
        }
        
        .upload-area {
            border: 2px dashed #007bff;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            background: #f8f9ff;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .upload-area:hover {
            border-color: #0056b3;
            background: #f0f4ff;
        }
        
        .upload-area.dragover {
            border-color: #0056b3;
            background: #e7f1ff;
        }
        
        #fileInput {
            display: none;
        }
        
        .upload-text {
            color: #666;
            margin-bottom: 10px;
        }
        
        .upload-hint {
            color: #999;
            font-size: 12px;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: center;
        }
        
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: #007bff;
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            background: #0056b3;
        }
        
        .btn-primary:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .filters {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .filter-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        label {
            font-weight: 500;
            color: #333;
            font-size: 14px;
        }
        
        select, input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }
        
        .status {
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            display: none;
        }
        
        .status.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            display: block;
        }
        
        .status.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            display: block;
        }
        
        .status.info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            display: block;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #dee2e6;
        }
        
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #dee2e6;
        }
        
        tr:hover {
            background: #f9f9f9;
        }
        
        .region {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .region-1 { background: #e3f2fd; color: #1565c0; }
        .region-2 { background: #f3e5f5; color: #6a1b9a; }
        .region-3 { background: #fff3e0; color: #e65100; }
        .region-4 { background: #f1f8e9; color: #558b2f; }
        .region-5 { background: #fce4ec; color: #c2185b; }
        .region-6 { background: #e0f2f1; color: #00695c; }
        
        .selection-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .selection-tr { background: #c8e6c9; color: #1b5e20; }
        .selection-b1 { background: #bbdefb; color: #0d47a1; }
        .selection-bolge { background: #ffe0b2; color: #e65100; }
        
        .loading {
            display: inline-block;
            text-align: center;
            color: #999;
            padding: 20px;
        }
        
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .no-data {
            text-align: center;
            color: #999;
            padding: 40px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏊 Milli Takım Seçme</h1>
        <p class="subtitle">Yüzme Federasyonu — Sporcu Seçim Sistemi</p>
        
        <!-- Upload Section -->
        <div class="section">
            <h2>📁 LXF Dosyası Yükle</h2>
            
            <div class="upload-area" id="uploadArea">
                <div class="upload-text">LXF dosyasını buraya sürükleyip bırakın veya tıklayın</div>
                <div class="upload-hint">Desteklenen format: .lxf (LENEX XML)</div>
                <input type="file" id="fileInput" accept=".lxf">
            </div>
            
            <div class="button-group">
                <button class="btn-primary" onclick="document.getElementById('fileInput').click()">Dosya Seç</button>
                <button class="btn-secondary" onclick="clearDatabase()">Veritabanını Temizle</button>
            </div>
            
            <div id="uploadStatus" class="status"></div>
        </div>
        
        <!-- Results Section -->
        <div class="section">
            <h2>📊 Seçilmiş Sporcular</h2>
            
            <div class="filters">
                <div class="filter-group">
                    <label for="filterYear">Doğum Yılı:</label>
                    <select id="filterYear" onchange="loadRankings()">
                        <option value="">Tümü</option>
                        <option value="2013">2013 (13 Yaş)</option>
                        <option value="2012">2012 (14 Yaş)</option>
                        <option value="2011">2011 (15 Yaş)</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="filterGender">Cinsiyet:</label>
                    <select id="filterGender" onchange="loadRankings()">
                        <option value="">Tümü</option>
                        <option value="F">Kadın (F)</option>
                        <option value="M">Erkek (M)</option>
                    </select>
                </div>
                
                <button class="btn-primary" style="margin-left: auto;" onclick="loadRankings()">Yenile</button>
            </div>
            
            <div id="resultsStatus" class="status"></div>
            <div id="resultsContainer">
                <div class="no-data">Veri yüklenmek üzere...</div>
            </div>
        </div>
    </div>
    
    <script>
        // Drag and drop
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                uploadFile();
            }
        });
        
        fileInput.addEventListener('change', uploadFile);
        
        function uploadFile() {
            const file = fileInput.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.className = 'status info';
            statusDiv.textContent = '⏳ Dosya yükleniyor...';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    statusDiv.className = 'status success';
                    let msg = `✓ ${data.count} sporcu başarıyla yüklendi`;
                    if (data.missing_clubs && data.missing_clubs.length > 0) {
                        msg += ` (${data.missing_clubs.length} kulüp haritalanmadı)`;
                    }
                    statusDiv.textContent = msg;
                    fileInput.value = '';
                    loadRankings();
                } else {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = `✗ Hata: ${data.message}`;
                }
            })
            .catch(err => {
                statusDiv.className = 'status error';
                statusDiv.textContent = `✗ Hata: ${err.message}`;
            });
        }
        
        function loadRankings() {
            const year = document.getElementById('filterYear').value;
            const gender = document.getElementById('filterGender').value;
            
            let url = '/api/ranking';
            const params = [];
            if (year) params.push(`birth_year=${year}`);
            if (gender) params.push(`gender=${gender}`);
            if (params.length > 0) url += '?' + params.join('&');
            
            const container = document.getElementById('resultsContainer');
            container.innerHTML = '<div class="loading"><div class="spinner"></div> Yükleniyor...</div>';
            
            fetch(url)
            .then(r => r.json())
            .then(athletes => {
                if (!athletes || athletes.length === 0) {
                    container.innerHTML = '<div class="no-data">Seçilmiş sporcu bulunamadı.</div>';
                    return;
                }
                
                let html = `<table>
                    <thead>
                        <tr>
                            <th>Ad Soyad</th>
                            <th>Kulüp</th>
                            <th>Şehir</th>
                            <th>Bölge</th>
                            <th>Yaş</th>
                            <th>Cinsiyet</th>
                            <th>Puan</th>
                            <th>Seçim</th>
                        </tr>
                    </thead>
                    <tbody>`;
                
                const regionNames = {
                    1: 'İstanbul', 2: 'Marmara', 3: 'Ege', 4: 'İç Anadolu', 5: 'Karadeniz', 6: 'Güneydoğu'
                };
                
                athletes.forEach(a => {
                    const regionNum = a.region || 0;
                    const regionName = regionNames[regionNum] || 'Bilinmiyor';
                    const selectionClass = a.selection_type ? `selection-${a.selection_type.toLowerCase()}` : '';
                    const selectionText = {
                        'TR': 'Türkiye',
                        'B1': 'Bölge 1',
                        'Bölge': 'Bölge'
                    }[a.selection_type] || '-';
                    
                    html += `<tr>
                        <td>${a.name || '-'}</td>
                        <td>${a.club_name || '-'}</td>
                        <td>${a.city || 'Unknown'}</td>
                        <td><span class="region region-${regionNum}">${regionName}</span></td>
                        <td>${a.birth_year || '-'}</td>
                        <td>${a.gender || '-'}</td>
                        <td><strong>${a.best_score || '-'}</strong></td>
                        <td><span class="selection-badge ${selectionClass}">${selectionText}</span></td>
                    </tr>`;
                });
                
                html += '</tbody></table>';
                container.innerHTML = html;
            })
            .catch(err => {
                container.innerHTML = `<div class="status error">Hata: ${err.message}</div>`;
            });
        }
        
        function clearDatabase() {
            if (!confirm('Veritabanındaki tüm veriler silinecek. Emin misiniz?')) {
                return;
            }
            
            fetch('/clear', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                document.getElementById('uploadStatus').className = 'status success';
                document.getElementById('uploadStatus').textContent = '✓ Veritabanı temizlendi';
                loadRankings();
            });
        }
        
        // Load on start
        loadRankings();
    </script>
</body>
</html>
```

- [ ] **Step 2: Add /clear endpoint to serve.py (for clear database button)**

Add to `DashboardHandler` class in `panel/serve.py`:

```python
def do_POST(self):
    """Handle POST requests."""
    if self.path == '/upload':
        self.handle_upload()
    elif self.path == '/clear':
        self.handle_clear()
    else:
        self.send_error(404, "Not found")

def handle_clear(self):
    """Handle database clear request."""
    try:
        clear_athletes()
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
    except Exception as e:
        self.send_error(500, str(e))
```

- [ ] **Step 3: Test dashboard**

Run:
```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
python panel/serve.py &
# Wait 2 seconds
curl http://localhost:8765/
```

Expected: HTML page returns (should see `<!DOCTYPE html>...`)

- [ ] **Step 4: Commit**

```bash
git add panel/index.html
git commit -m "feat: add dashboard HTML with upload form and rankings table"
```

---

### Task 7: Integration Test (Manual)

**Files:**
- Test files: `data/antalya_millitakim_secme_sonuc.lxf`, `data/edirne_millitakim_secme_sonuc.lxf`

**Interfaces:**
- Consumes:
  - All components from Tasks 1-6
- Produces:
  - Working system end-to-end
  - Database populated
  - API responding
  - Dashboard rendering

- [ ] **Step 1: Start server in background**

```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
python panel/serve.py > server.log 2>&1 &
# Get process ID
ps aux | grep "panel/serve.py"
```

- [ ] **Step 2: Wait 2 seconds for server startup**

```bash
sleep 2
```

- [ ] **Step 3: Test 1 — GET / (Dashboard loads)**

```bash
curl -s http://localhost:8765/ | head -20
```

Expected: HTML starts with `<!DOCTYPE html>`

- [ ] **Step 4: Test 2 — GET /api/ranking (empty, no data yet)**

```bash
curl -s http://localhost:8765/api/ranking | python -m json.tool
```

Expected: `[]` (empty JSON array)

- [ ] **Step 5: Test 3 — Upload Antalya LXF (manual via browser)**

Open browser: `http://localhost:8765`
- Click "Dosya Seç"
- Select `data/antalya_millitakim_secme_sonuc.lxf`
- Wait for upload to complete
- Should see success message with count (e.g., "234 sporcu başarıyla yüklendi")

Expected:
- Status shows "✓ ... sporcu başarıyla yüklendi"
- Table populates below

- [ ] **Step 6: Test 4 — Verify database via curl**

```bash
curl -s "http://localhost:8765/api/ranking?birth_year=2013&gender=F" | python -m json.tool | head -30
```

Expected:
- JSON array with athletes
- Each has `city`, `region`, `name`, `club_name`, `best_score`, etc.
- At least 40+ results for 2013F

- [ ] **Step 7: Test 5 — Filter by gender (curl)**

```bash
curl -s "http://localhost:8765/api/ranking?birth_year=2013&gender=M" | python -m json.tool | head -30
```

Expected: Different count (2013M should be ~29)

- [ ] **Step 8: Test 6 — Upload Edirne LXF (combination test)**

Browser: Upload `data/edirne_millitakim_secme_sonuc.lxf`

Expected:
- Additional athletes added
- Counts increase
- API still responds correctly

- [ ] **Step 9: Verify database file created**

```bash
ls -lah data/selection.db
sqlite3 data/selection.db "SELECT COUNT(*) FROM athletes"
```

Expected:
- `selection.db` file exists in data/
- `COUNT(*)` should be > 100

- [ ] **Step 10: Kill server**

```bash
pkill -f "python panel/serve.py"
```

- [ ] **Step 11: Commit integration test results**

```bash
git add -A
git commit -m "test: integration test Phase 2 — LXF upload, API, dashboard verified"
```

---

### Task 8: Final Documentation & Cleanup

**Files:**
- Modify: `README.md`
- Create: `docs/superpowers/IMPLEMENTATION_NOTES.md` (optional)

- [ ] **Step 1: Update README.md with Phase 2 info**

Add to `README.md`:

```markdown
## Phase 2: Çalışan Sistem

✅ **Tamamlandı (2026-08-31)**

### Kurulum & Kullanım

```bash
# 1. Bağımlılık yükle
pip install -r requirements.txt

# 2. Sunucu başlat
python panel/serve.py

# 3. Tarayıcı aç
open http://localhost:8765
```

### LXF Yükleme

1. Dashboard'da "Dosya Seç" tıkla
2. `data/antalya_millitakim_secme_sonuc.lxf` seç (veya Edirne)
3. "Yükle" tıkla
4. Sonuçlar tabloda görünecek

### API Endpoints

**GET /api/ranking** — Seçilmiş sporcular
```bash
curl "http://localhost:8765/api/ranking?birth_year=2013&gender=F"
```

Query params:
- `birth_year`: int (2013, 2012, 2011)
- `gender`: string (F, M, tümü)

Response: JSON array of athletes with city/region

### Önemli Dosyalar

- `database/db.py` — Database schema ve CRUD
- `modules/m4_mapping.py` — Excel club mapping
- `modules/lxf_parser.py` — LXF parser + city lookup
- `panel/serve.py` — HTTP server
- `panel/index.html` — Dashboard UI
- `config.py` — Configuration constants

### Sonraki Aşamalar (Phase 3)

- [ ] Delete race leg endpoint
- [ ] Leg toggle (Antalya/Edirne)
- [ ] Region-specific panels
- [ ] Export (Excel/PDF)
```

- [ ] **Step 2: Commit README update**

```bash
git add README.md
git commit -m "docs: add Phase 2 usage and API documentation"
```

- [ ] **Step 3: Final git log check**

```bash
git log --oneline | head -10
```

Expected: Clean commit history with Phase 2 tasks

---

## Plan Self-Review

**Spec Coverage:** ✅
- ✅ Database layer (Task 1)
- ✅ Excel mapping (Task 3)
- ✅ Parser integration (Task 4)
- ✅ API endpoint `/api/ranking` (Task 5)
- ✅ HTTP panel `/upload` (Task 5)
- ✅ Dashboard HTML (Task 6)
- ✅ Testing (Task 7)
- ✅ Config updates (Task 2)

**Placeholder Scan:** ✅ None found. All steps have actual code/commands.

**Type Consistency:** ✅
- `ClubInfo` defined in Task 3, used in Task 3-4
- `athletes_list` from Task 4, inserted in Task 5
- All function signatures consistent

**No Gaps:** ✅ Every spec section has corresponding task.

---

