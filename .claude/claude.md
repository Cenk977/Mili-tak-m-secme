# Claude Code Guidelines for Milli Takım Seçme

## Project Overview
Turkish National Swimming Team Selection System (Phase 2 Complete)
- Core parsing and ranking (Phase 1) ✅
- Web API and Dashboard (Phase 2) ✅

## Key Files & Responsibilities

### Database Layer (database/)
- SQLite with 3 tables: athletes, results, sync_log
- All CRUD operations in db.py
- Always UTF-8 encoding
- Foreign key constraints enabled

### Parser (modules/lxf_parser.py)
- LENEX 3.0 XML parsing
- Integrates city/region mapping via lookup_club()
- Returns (athletes, results) tuple

### Mapping (modules/m4_mapping.py)
- Excel-based club → city/region lookup
- Idempotent caching
- Handles case-insensitive lookups

### HTTP Server (panel/serve.py)
- Localhost:8765
- Endpoints: GET /, POST /upload, GET /api/ranking, POST /clear
- Multipart form parsing
- ensure_ascii=False for JSON responses

### Dashboard (panel/index.html)
- HTML5 with inline CSS
- Turkish language UI
- Fetch API integration
- Responsive design

## Coding Standards
- UTF-8 encoding throughout
- Turkish character support (İ, ş, ç, ğ, ü, ö)
- Keep it simple (KISS principle)
- Idempotent operations where specified
- Error handling with logging, not print statements

## Testing Before Deploy
1. Start HTTP server: python panel/serve.py
2. Open http://localhost:8765 in browser
3. Upload LXF file (test files in data/ directory)
4. Verify athletes parsed with city/region populated
5. Test filters: birth year, gender
6. Test API endpoints with curl

## Common Tasks

### Add a new endpoint to API
1. Add handler method to DashboardHandler in panel/serve.py
2. Add route in do_GET() or do_POST()
3. Return JSON with ensure_ascii=False
4. Add corresponding fetch call in panel/index.html

### Modify Excel mapping
1. Update config.py column indices if structure changes
2. Regenerate lookup_club() test in modules/m4_mapping.py
3. Re-run integration test (Task 7)

### Add database fields
1. Update athletes table schema in database/db.py
2. Update insert_athlete() and get_athletes_by_filter()
3. Update HTML table columns in panel/index.html
4. Add fetch response handling for new fields
