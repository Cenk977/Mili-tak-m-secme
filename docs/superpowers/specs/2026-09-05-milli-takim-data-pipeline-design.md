# Milli Takım Seçme - Data Pipeline Design

**Date:** 2026-09-05  
**Author:** Claude Code  
**Status:** Approved for Implementation

---

## 1. Overview

**Goal:** LXF dosya upload'ında otomatik olarak sporcuları puanla, sırala ve seçim kararlarını oluştur.

**Scope:** 
- Input: LXF file (antalya_millitakim_secme_sonuc.lxf tarzı)
- Output: Seçilmiş sporcuların (TR, BÖLGE) listesi database'e kaydedilmiş
- Integration: panel/serve.py POST /upload endpoint'i

**Timeline:** Phase 3A Task 1 (1-2 gün)

---

## 2. Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────┐
│ panel/serve.py (Upload Endpoint)                        │
│   POST /upload → DashboardHandler.do_POST()            │
└────────────┬────────────────────────────────────────────┘
             │ LXF file path
             ↓
┌─────────────────────────────────────────────────────────┐
│ federasyon/pipeline.py (NEW - Orchestration)            │
│                                                         │
│  MiltiTakimPipeline.process(lxf_path):                 │
│    1. parse_and_extract()    ← modules/lxf_parser.py   │
│    2. score_athletes()        ← federasyon/scorer.py    │
│    3. rank_athletes()         ← federasyon/ranker.py    │
│    4. save_to_database()      ← federasyon/db_fed.py    │
│    5. return ranked_data      → panel/serve.py          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Role | Status |
|-----------|------|--------|
| `federasyon/pipeline.py` | Orchestration (LXF→score→rank→save) | ✅ NEW |
| `modules/lxf_parser.py` | LENEX 3.0 parsing | ✅ Existing |
| `federasyon/scorer.py` | Time → points conversion | ✅ Existing (Complete) |
| `federasyon/ranker.py` | Selection & ranking logic | ✅ Existing (Complete) |
| `federasyon/db_fed.py` | Database CRUD | ⚠️ Extend |
| `panel/serve.py` | Upload handler orchestration | ⚠️ Modify |

---

## 3. Data Flow

### 3.1 Step-by-Step Process

**Step 1: Parse & Extract**
```
Input: LXF file path
↓
lxf_parser.parse(lxf_path) → (athletes, results)
↓
Output: 
  athletes = [
    {'name': 'Ahmet Yılmaz', 'birth_year': 2013, 'gender': 'M', 'club': 'İstanbul SK', ...},
    ...
  ]
  results = [
    {'athlete_name': 'Ahmet Yılmaz', 'event': ('Serbest', 50), 'time_sec': 29.5},
    ...
  ]
```

**Step 2: Score Athletes**
```
For each athlete:
  event_scores = score_athlete_row(athlete, birth_year, gender)
  # event_scores = {('Serbest', 50): 7, ('Serbest', 100): 5, ...}
  athlete['event_scores'] = event_scores
```

**Step 3: Rank & Select**
```
Input: athletes list with event_scores
↓
rank_all(athletes)
↓
Output: ranked athletes with:
  - seq: [9, 7, 5, 3, ...]  (best scores sequence)
  - top3_total: 21
  - ranking_key: (-21, -25, -30, -33)
  - selected: 'TR' | 'BÖLGE' | 'BARAJ_YOK' | '-'
  - selected_slot: 'TR-1', 'B1-2', etc.
  - tied: True/False
```

**Step 4: Save to Database**
```
For each ranked athlete:
  upsert_fed_results(athlete)  # ham sonuçlar
  update_athlete_selection(athlete)  # seçim durumu
```

**Step 5: Return to Client**
```
response = {
  'success': True,
  'selected_tr': [{name, slot, top3_total}, ...],
  'selected_bolge': [...],
  'baraj_yok': [...],
  'total_athletes': 150,
  'summary': {birth_year: 2013, selected_count: 25, ...}
}
```

---

## 4. Database Schema

### 4.1 New Columns (fed_results table)

```sql
ALTER TABLE fed_results ADD COLUMN IF NOT EXISTS selected TEXT DEFAULT '-';
ALTER TABLE fed_results ADD COLUMN IF NOT EXISTS selected_slot TEXT DEFAULT '-';
ALTER TABLE fed_results ADD COLUMN IF NOT EXISTS tied BOOLEAN DEFAULT 0;
ALTER TABLE fed_results ADD COLUMN IF NOT EXISTS ranking_key TEXT;
```

**Explanation:**
- `selected`: Selection status ('TR', 'BÖLGE', 'BARAJ_YOK', '-')
- `selected_slot`: Slot label ('TR-1', 'B1-2', 'B2-1', etc.)
- `tied`: True if athlete tied at quota boundary
- `ranking_key`: For reproducibility and audit trail

### 4.2 Updates to fed_athlete_best

```sql
ALTER TABLE fed_athlete_best ADD COLUMN IF NOT EXISTS selected TEXT DEFAULT '-';
ALTER TABLE fed_athlete_best ADD COLUMN IF NOT EXISTS selected_slot TEXT DEFAULT '-';
```

### 4.3 New Functions in db_fed.py

```python
def upsert_fed_results(athlete: dict) -> None:
    """Insert or update raw result for each event"""
    for (stroke, distance), points in athlete['event_scores'].items():
        # INSERT OR REPLACE into fed_results
        pass

def update_athlete_selection(athlete: dict) -> None:
    """Update selection status in fed_athlete_best"""
    # UPDATE fed_athlete_best SET selected=?, selected_slot=? WHERE ...
    pass

def get_selected_athletes(birth_year: int = None, selected: str = None) -> list[dict]:
    """Query selected athletes"""
    # SELECT * FROM fed_athlete_best WHERE selected=? ...
    pass
```

---

## 5. Error Handling & Validation

### 5.1 Error Cases

| Error | Cause | Handling |
|-------|-------|----------|
| LXF Parse Error | Malformed XML/missing tags | Log + return error message |
| Unknown Event | (stroke, distance) not in TABLES | Score as 0 (baraj yok) |
| Missing birth_year | Cannot determine age group | Skip athlete, log warning |
| Scoring Table Missing | birth_year/gender combo not in TABLES | Use fallback baraj (all 0) |
| Database Transaction Fail | FK constraint, disk full, etc. | Rollback + return error |

### 5.2 Validation Rules

```python
def validate_results(ranked_athletes: list[dict]) -> bool:
    """Validate selection consistency"""
    
    # 1. TR quota check
    for by in [2013, 2012, 2011]:
        tr_selected = [a for a in ranked_athletes 
                      if a['birth_year'] == by and a['selected'] == 'TR']
        max_tr = SELECTION_QUOTAS[by]['tr']
        assert len(tr_selected) <= max_tr, f"TR quota exceeded for {by}"
    
    # 2. Region quota check (per region, per birth_year)
    # ...
    
    # 3. Selection status validity
    for a in ranked_athletes:
        assert a['selected'] in ['-', 'TR', 'BÖLGE', 'BARAJ_YOK']
    
    # 4. Slot format validation
    # ...
    
    return True
```

---

## 6. Integration with panel/serve.py

### 6.1 Updated Upload Handler

```python
# panel/serve.py - DashboardHandler.do_POST()

elif self.path == '/upload':
    try:
        # 1. Parse multipart form
        form_data = self.parse_multipart()
        lxf_file_bytes = form_data.get('file')
        
        # 2. Save to temp file
        temp_lxf_path = Path(tempfile.gettempdir()) / f"upload_{uuid.uuid4()}.lxf"
        temp_lxf_path.write_bytes(lxf_file_bytes)
        
        # 3. Run pipeline
        from federasyon.pipeline import MiltiTakimPipeline
        pipeline = MiltiTakimPipeline()
        result = pipeline.process(str(temp_lxf_path))
        
        # 4. Send response
        response = {
            'success': True,
            'message': f"Processed {result['total_athletes']} athletes",
            'selected_tr': result['selected_tr'],
            'selected_bolge': result['selected_bolge'],
            'baraj_yok_count': result['baraj_yok_count'],
            'summary': result['summary']
        }
        self.send_json(response)
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        self.send_json({'success': False, 'error': str(e)}, status=400)
    
    finally:
        # Cleanup
        if temp_lxf_path.exists():
            temp_lxf_path.unlink()
```

### 6.2 Response Format

```json
{
  "success": true,
  "message": "Processed 150 athletes",
  "selected_tr": [
    {"name": "Ahmet Yılmaz", "birth_year": 2013, "selected_slot": "TR-1", "top3_total": 21},
    ...
  ],
  "selected_bolge": [
    {"name": "Fatma Kaya", "birth_year": 2013, "selected_slot": "B1-1", "top3_total": 19},
    ...
  ],
  "baraj_yok_count": 25,
  "summary": {
    "2013": {"multi": 0, "tr": 20, "bolge": 30, "total": 50},
    "2012": {"multi": 0, "tr": 10, "bolge": 15, "total": 25},
    "2011": {"multi": 0, "tr": 5, "bolge": 7, "total": 12}
  }
}
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

**File:** `federasyon/tests/test_pipeline.py`

```python
def test_pipeline_end_to_end():
    """LXF → parse → score → rank → save"""
    pipeline = MiltiTakimPipeline()
    result = pipeline.process('test_data/sample.lxf')
    assert result['total_athletes'] == 10
    assert len(result['selected_tr']) >= 0

def test_tr_quota_respected():
    """TR selection respects SELECTION_QUOTAS"""
    result = pipeline.process(...)
    tr_count = len([a for a in result if a['selected'] == 'TR'])
    expected_max = SELECTION_QUOTAS[2013]['tr']
    assert tr_count <= expected_max

def test_validation_passes():
    """Result passes validation checks"""
    result = pipeline.process(...)
    assert validate_results(result) == True

def test_error_handling_corrupted_lxf():
    """Graceful error on invalid LXF"""
    with pytest.raises(Exception):
        pipeline.process('test_data/corrupted.lxf')
```

### 7.2 Integration Tests

**File:** `tests/test_upload_endpoint.py`

```python
def test_upload_endpoint_success():
    """POST /upload processes LXF and returns selection"""
    with open('test_data/sample.lxf', 'rb') as f:
        response = http_post('/upload', files={'file': f})
    assert response['status'] == 200
    assert response['data']['success'] == True
    assert 'selected_tr' in response['data']

def test_upload_endpoint_invalid_file():
    """POST /upload rejects invalid file"""
    response = http_post('/upload', files={'file': b'not-lxf'})
    assert response['status'] == 400
    assert 'error' in response['data']
```

### 7.3 Test Data

Create `test_data/sample.lxf`:
- 10 athletes (5×2013F, 5×2013M)
- Mixed scoring (TR qualification, BÖLGE qualification, baraj yok)
- Expected output documented

---

## 8. Implementation Roadmap

**Phase 1: Foundation (Day 1, 2-3 hours)**
- [ ] Create `federasyon/pipeline.py` with MiltiTakimPipeline class
- [ ] Implement score_athletes(), rank_athletes()
- [ ] Extend db_fed.py with upsert/update functions

**Phase 2: Integration (Day 1, 1-2 hours)**
- [ ] Update panel/serve.py POST /upload handler
- [ ] Test with sample LXF file
- [ ] Update panel/index.html to show results

**Phase 3: Testing & Polish (Day 2, 2-3 hours)**
- [ ] Write unit & integration tests
- [ ] Error handling & edge cases
- [ ] Performance check (large LXF files)

---

## 9. Success Criteria

- ✅ LXF file upload → automatic scoring + ranking
- ✅ Selection decisions saved to fed_athlete_best
- ✅ Dashboard shows selected athletes with slot labels
- ✅ Quota rules enforced (TR, BÖLGE per region)
- ✅ Tie-breaking works correctly
- ✅ Error messages clear and actionable
- ✅ 90%+ test coverage on pipeline.py

---

## 10. Dependencies & Constraints

**Dependencies:**
- `modules/lxf_parser.py` (existing, functional)
- `federasyon/scorer.py` (existing, complete)
- `federasyon/ranker.py` (existing, complete)
- `federasyon/db_fed.py` (existing, will extend)

**Constraints:**
- Only LXF input (no Excel, CSV)
- Single-threaded execution (no async)
- fed_results/fed_athlete_best schema (no new tables)
- UTF-8 encoding throughout

**Assumptions:**
- LXF file is well-formed LENEX 3.0
- birth_year can be extracted from athlete data
- All required fields present in LXF

---

## 11. Future Considerations

- Multi-leg support (Antalya + Edirne → merge scores)
- Batch processing (multiple LXF files)
- Async/queue-based processing (large files)
- Manual override system
- Excel export of selections
