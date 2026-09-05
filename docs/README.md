# Milli Takım Seçme Documentation

## Phase 1: Core Parser & Database (COMPLETE)

- LXF file parsing with LENEX 3.0 XML support
- SQLite database with athletes and results tables
- Excel-based club to city/region mapping

## Phase 2: Web API & Dashboard (COMPLETE)

- HTTP server on localhost:8765
- REST API endpoints for querying athletes and rankings
- Web dashboard for file uploads and filtering
- Multi-language support (Turkish)

## Phase 3: Milli Takım Seçimleri

### 3A: Data Pipeline (OPERATIONAL)

End-to-end LXF file processing with automatic scoring and selection.

**Quick Start:**
```bash
python panel/serve.py
# → http://localhost:8765
# Upload LXF file → Automatic scoring → Dashboard shows selected athletes
```

**Flow:**
1. Upload LXF file → panel/serve.py POST /upload
2. Pipeline orchestration → federasyon/pipeline.py
3. Scoring → federasyon/scorer.py (time → points)
4. Ranking → federasyon/ranker.py (quotas + selection)
5. Save → federasyon/db_fed.py (fed_results, fed_athlete_best)
6. Display → panel/index.html (TR/BÖLGE tables)

**API Response:**
```json
{
  "success": true,
  "selected_tr": [...],
  "selected_bolge": [...],
  "summary": { "2013": {...}, ... }
}
```

## Related Documentation

- [Federasyon Module Guide](../federasyon/README.md) — Module components, API usage, rules, testing
- [System Architecture](./ARCHITECTURE.md) — System design, data flow, schema details
