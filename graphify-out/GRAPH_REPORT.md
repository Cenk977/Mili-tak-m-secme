# Graph Report - Mili_takım_secme  (2026-08-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 67 nodes · 114 edges · 12 communities (6 shown, 3 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `58a6c60c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- DashboardHandler
- lxf_parser.py
- m4_mapping.py
- db.py
- get_connection
- serve.py
- get_athletes_by_filter
- get_missing_clubs_from_db
- insert_athlete

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 12 edges
2. `DashboardHandler` - 10 edges
3. `parse_lxf_file()` - 8 edges
4. `process_lxf_upload()` - 8 edges
5. `lookup_club()` - 7 edges
6. `get_birth_year()` - 6 edges
7. `clear_athletes()` - 6 edges
8. `init_db()` - 6 edges
9. `get_athletes_by_filter()` - 6 edges
10. `get_missing_clubs_from_db()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `process_lxf_upload()` --calls--> `get_missing_clubs_from_db()`  [EXTRACTED]
  panel/serve.py → database/db.py
- `process_lxf_upload()` --calls--> `insert_athlete()`  [EXTRACTED]
  panel/serve.py → database/db.py
- `process_lxf_upload()` --calls--> `insert_result()`  [EXTRACTED]
  panel/serve.py → database/db.py
- `main()` --calls--> `init_db()`  [EXTRACTED]
  panel/serve.py → database/db.py
- `process_lxf_upload()` --calls--> `get_birth_year()`  [EXTRACTED]
  panel/serve.py → modules/lxf_parser.py

## Import Cycles
- None detected.

## Communities (12 total, 3 thin omitted)

### Community 0 - "DashboardHandler"
Cohesion: 0.17
Nodes (8): BaseHTTPRequestHandler, DashboardHandler, Serve ranking API endpoint., Handle database clear request., HTTP request handler for dashboard., Suppress default logging., Handle POST requests., Serve dashboard HTML.

### Community 1 - "lxf_parser.py"
Cohesion: 0.23
Nodes (12): get_birth_year(), map_stroke_name(), parse_lxf_file(), parse_swimtime(), LXF (Lenex) format parser for swimming competition data, Parse LXF file and extract athletes and results. Returns: Tuple of (athletes,…, Convert swim time string (MM:SS.XX format) to seconds., Extract birth year from birthdate string (YYYY-MM-DD format). (+4 more)

### Community 2 - "m4_mapping.py"
Cohesion: 0.21
Nodes (10): Configuration for Milli Takım Seçme Sistemi, ClubInfo, get_missing_clubs(), load_mapping(), lookup_club(), m4_mapping.py — Club → City → Region lookup Reads Excel "Kulüp Şehir…, Look up club in cached mapping. Returns ClubInfo with city/region, or None if…, Get set of club names that don't map to a city/region. Useful for… (+2 more)

### Community 3 - "db.py"
Cohesion: 0.36
Nodes (6): get_all_athletes(), insert_result(), Database layer for Milli Takım Seçme SQLite3 backend, UTF-8 encoding, Get all athletes from database., Update athlete's score and selection status., update_athlete_ranking()

### Community 4 - "get_connection"
Cohesion: 0.40
Nodes (5): Connection, clear_athletes(), get_connection(), Get SQLite connection with UTF-8 row factory., Delete all athlete records (for re-import).

### Community 5 - "serve.py"
Cohesion: 0.67
Nodes (3): init_db(), Initialize database, create tables if missing., main()

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DashboardHandler` connect `DashboardHandler` to `serve.py`?**
  _High betweenness centrality (0.244) - this node is a cross-community bridge._
- **Why does `parse_lxf_file()` connect `lxf_parser.py` to `m4_mapping.py`, `serve.py`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Why does `lookup_club()` connect `m4_mapping.py` to `lxf_parser.py`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._