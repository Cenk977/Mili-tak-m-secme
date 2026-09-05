# Milli Takım Seçme Architecture — Phase 3A

## System Overview

```
┌─────────────┐
│ LXF Upload  │
└──────┬──────┘
       ↓
┌─────────────────────────────────────────────┐
│ MiltiTakimPipeline.process()                │
│  1. Parse LXF (lxf_parser.py)              │
│  2. Score Athletes (scorer.py)              │
│  3. Rank & Select (ranker.py)               │
│  4. Save (db_fed.py)                        │
│  5. Return Response                         │
└──────┬──────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ Database (SQLite)                           │
│  • fed_results (raw event results)          │
│  • fed_athlete_best (selection decisions)   │
└──────┬──────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ Dashboard (panel/index.html)                │
│  • Display selected TR/BÖLGE athletes       │
│  • Summary statistics                       │
└─────────────────────────────────────────────┘
```

## Data Flow

1. **Input**: LXF file (LENEX 3.0 XML)
2. **Parse**: Extract athletes + results
3. **Score**: time_sec → points (0-9, 8 yok)
4. **Rank**: Group by (birth_year, gender, region), enforce quotas
5. **Select**: Mark as TR/BÖLGE/BARAJ_YOK, assign slot
6. **Save**: Insert into database
7. **Output**: JSON response + dashboard update

## Schema

### fed_results
- race_leg, race_date, athlete_name, birth_year, gender, region, city, club
- stroke, distance, points
- selected, selected_slot, tied, ranking_key

### fed_athlete_best
- (Similar fields) + aggregated selection status

## Component Details

### Parser (lxf_parser.py)
Extracts athlete information and race results from LENEX 3.0 XML files.

**Input**: LXF file path  
**Output**: Tuple of (athletes list, results list)

### Scorer (federasyon/scorer.py)
Converts swim times to scoring points based on time thresholds.

**Key Functions**:
- `score_event()`: Single event scoring (0-9 scale, 8 omitted)
- `score_athlete_row()`: All events for one athlete
- `compute_ranking_key()`: Tiebreaker key computation
- `qualifies_minimum()`: Minimum qualification check (7 points)

**Scoring Rules**:
- Time < threshold → 9 points (best)
- Points decrease with slower times
- 0 points = did not qualify
- Tiebreaker: cumulative sums (-top3, -top4, -top5, -top6)

### Ranker (federasyon/ranker.py)
Ranks athletes and makes selection decisions based on quotas and tiers.

**Selection Categories**:
- **TR**: National team (country-wide top performers)
- **BÖLGE**: Regional selection (per-region quota)
- **BARAJ_YOK**: Below threshold (didn't pass minimum)
- **-**: Not selected (regional quota full)

**Quota Logic**:
- TR: First 20 females + 10 males from all regions
- BÖLGE: Regional allocation based on birth year and gender
- BARAJ_YOK: Athletes with top-3 sum < 7 points

### Pipeline (federasyon/pipeline.py)
Orchestrates the entire process from LXF to database.

**Main Method**: `MiltiTakimPipeline.process(lxf_path)`

**Steps**:
1. Parse LXF file
2. Score all athletes
3. Rank and select athletes
4. Save to database
5. Return JSON response

**Response Structure**:
```json
{
  "success": true,
  "message": "Selection complete",
  "selected_tr": [...],
  "selected_bolge": [...],
  "baraj_yok_count": 42,
  "total_athletes": 763,
  "summary": {
    "2013": {
      "F": { "TR": 5, "BÖLGE": 15, "BARAJ_YOK": 23 },
      "M": { "TR": 3, "BÖLGE": 10, "BARAJ_YOK": 18 }
    },
    ...
  }
}
```

### Database (federasyon/db_fed.py)
Manages all database operations for selection results.

**Key Tables**:
- `fed_results`: Raw event results and selection information
- `fed_athlete_best`: Best performance aggregates

**Key Functions**:
- `upsert_fed_results()`: Insert/update event results
- `update_athlete_selection()`: Update selection status
- `get_selected_athletes()`: Query by selection criteria
- `migrate_add_selection_columns()`: Schema migration

## Integration Points

### File Upload Endpoint (panel/serve.py)
```python
POST /upload
Content-Type: multipart/form-data
Body: file=<LXF file>

Response: 200 JSON
{
  "success": true,
  "selected_tr": [...],
  "selected_bolge": [...],
  "summary": {...}
}
```

### Dashboard Display (panel/index.html)
- Fetches selected athletes via `/api/ranking` endpoint
- Displays TR and BÖLGE selections in separate tables
- Shows summary statistics by age group and gender

## Testing Strategy

### Unit Tests
- `federasyon/tests/test_scorer.py`: Scoring logic
- `federasyon/tests/test_ranker.py`: Ranking and selection
- `federasyon/tests/test_pipeline.py`: End-to-end pipeline

### Integration Tests
- `tests/test_upload_endpoint.py`: Full upload and processing flow

### Test Data
Sample LXF files in `data/` directory:
- `data/antalya_millitakim_secme_sonuc.lxf`
- `data/edirne_millitakim_secme_sonuc.lxf`

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|-----------|
| LXF Parse Error | Invalid XML | Validate LXF file format |
| Unknown Event | Event not in TABLES | Update scoring_tables.py |
| Missing birth_year | No birth date in LXF | Check LXF file contents |
| Database Error | FK constraint or disk full | Check disk space, run migration |
| Quota Mismatch | Selection algorithm issue | Review ranker.py quotas |

## Performance Considerations

- **LXF Parsing**: ~1-2 seconds for typical file (763 athletes)
- **Scoring**: ~0.5 seconds (763 athletes × ~15 events)
- **Ranking**: ~0.2 seconds (sorting + filtering)
- **Database**: ~1 second (batch insert + index updates)

**Total**: ~3-4 seconds end-to-end for typical file

## Future Enhancements

1. **Excel Export**: Generate selection reports in XLSX
2. **Multi-event Analysis**: Support cross-competition rankings
3. **Historical Tracking**: Archive selection decisions by date
4. **Advanced Filtering**: Region-specific selection rules
5. **API Authentication**: Secure endpoints with token auth
