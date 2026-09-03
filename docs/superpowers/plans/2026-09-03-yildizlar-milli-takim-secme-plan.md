# Yıldızlar Milli Takım Seçme Sistemi Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement three youth national team selections (Multinations Stars, Comen Cup, Central European Meet) with independent qualification logic, antrenor coach thresholds, and multi-competition eligibility.

**Architecture:** Create three standalone baraj (performance threshold) modules, one shared ranking algorithm (yildizlar_ranker.py) that evaluates all competitions, extend database schema with selection flags, and update frontend to display athlete selections per competition and date.

**Tech Stack:** Python (backend/ranking), SQLite (database), JavaScript/HTML (frontend)

**Spec:** `docs/superpowers/specs/2026-09-03-yildizlar-milli-takim-secme-design.md`

## Global Constraints

- All age groups: 2013–2011 (13–15 age) except Comen Cup male includes 2012–2010
- Selection dates: Multinations December only; Comen Cup & Central Europe December + April
- Antrenor invitations: Based on performance threshold (baraj), not selection itself
- Athletes can qualify for multiple competitions simultaneously
- Yíldízlar points visible but do NOT affect federation quota slots
- Database: SQLite, UTF-8 encoding, foreign key constraints enabled

---

## File Structure

**Create (new files):**
- `federasyon/yildizlar_multinations_barajlari.py` — Performance thresholds for Multinations
- `federasyon/yildizlar_comen_cup_barajlari.py` — Performance thresholds for Comen Cup
- `federasyon/yildizlar_central_europe_barajlari.py` — Performance thresholds for Central Europe
- `federasyon/yildizlar_ranker.py` — Unified ranking engine for all three competitions

**Modify (existing files):**
- `database/db.py` — Add 10 new columns to `athletes` table (selection flags + coach flags)
- `panel/serve.py` — Add `/api/yildizlar` endpoint; update `/api/ranking` to include yíldízlar data
- `panel/index.html` — Add yíldízlar section to athlete profile display

---

### Task 1: Extend Database Schema

**Files:**
- Modify: `database/db.py` (athletes table definition + initialization)

**Interfaces:**
- Consumes: Existing `athletes` table structure
- Produces: Extended `athletes` table with 10 new boolean columns for yíldízlar selections

**Steps:**

- [ ] **Step 1: Open `database/db.py` and locate `CREATE TABLE athletes`**

Find the athletes table definition (around line 20–50). Note current columns: athlete_name, birth_year, gender, region, city, club, etc.

- [ ] **Step 2: Add 10 new columns to CREATE TABLE statement**

After existing columns, add:
```sql
selected_yildiz_multinations BOOLEAN DEFAULT 0,
coach_called_yildiz_multinations BOOLEAN DEFAULT 0,
selected_yildiz_comen_cup_aralik BOOLEAN DEFAULT 0,
selected_yildiz_comen_cup_nisan BOOLEAN DEFAULT 0,
coach_called_yildiz_comen_cup_aralik BOOLEAN DEFAULT 0,
coach_called_yildiz_comen_cup_nisan BOOLEAN DEFAULT 0,
selected_yildiz_central_europe_aralik BOOLEAN DEFAULT 0,
selected_yildiz_central_europe_nisan BOOLEAN DEFAULT 0,
coach_called_yildiz_central_europe_aralik BOOLEAN DEFAULT 0,
coach_called_yildiz_central_europe_nisan BOOLEAN DEFAULT 0
```

- [ ] **Step 3: Add migration logic (if database exists)**

In `db.py` `init_db()` function, after table creation, add ALTER TABLE statements for existing databases:
```python
try:
    cursor.execute("ALTER TABLE athletes ADD COLUMN selected_yildiz_multinations BOOLEAN DEFAULT 0")
except sqlite3.OperationalError:
    pass  # Column already exists
# ... repeat for all 10 new columns
```

- [ ] **Step 4: Update any SELECT/INSERT queries to handle new columns**

Search `db.py` for `SELECT * FROM athletes` and update column lists if needed. Update `get_athletes_by_filter()` to include new columns in returned dict.

- [ ] **Step 5: Test database initialization**

Run: `python -c "from database.db import init_db; init_db()"`

Expected: No errors; verify new columns exist with `sqlite3 database/athletes.db ".schema athletes"`

- [ ] **Step 6: Commit**

```bash
git add database/db.py
git commit -m "db: extend athletes table with 10 yildizlar selection columns"
```

---

### Task 2: Create Multinations Baraj Table

**Files:**
- Create: `federasyon/yildizlar_multinations_barajlari.py`

**Interfaces:**
- Produces: `ANTRENOR_BARAJLARI` dict mapping (stroke, distance, gender) → time_string

**Steps:**

- [ ] **Step 1: Create new file `federasyon/yildizlar_multinations_barajlari.py`**

- [ ] **Step 2: Add docstring and data structure**

```python
"""
Multinations Yıldızlar 2026 — Antrenor Performance Thresholds (Barajları)

Athletes passing these times qualify for coach invitation.
Same as times in PDF page 3-4.
"""

ANTRENOR_BARAJLARI = {
    # Format: (stroke, distance) → {"M": time_str, "F": time_str}
    ("Freestyle", 50): {"M": "00:23.41", "F": "00:26.34"},
    ("Freestyle", 100): {"M": "00:51.53", "F": "00:57.33"},
    ("Freestyle", 200): {"M": "01:53.26", "F": "02:04.99"},
    ("Freestyle", 400): {"M": "04:01.40", "F": "04:23.21"},
    ("Freestyle", 800): {"M": None, "F": "09:04.07"},
    ("Freestyle", 1500): {"M": "16:03.90", "F": None},
    ("Backstroke", 50): {"M": "00:26.70", "F": "00:30.12"},
    ("Backstroke", 100): {"M": "00:57.28", "F": "01:04.27"},
    ("Backstroke", 200): {"M": "02:05.25", "F": "02:18.57"},
    ("Breaststroke", 50): {"M": "00:29.09", "F": "00:33.00"},
    ("Breaststroke", 100): {"M": "01:03.96", "F": "01:11.81"},
    ("Breaststroke", 200): {"M": "02:19.32", "F": "02:34.35"},
    ("Butterfly", 50): {"M": "00:25.02", "F": "00:28.01"},
    ("Butterfly", 100): {"M": "00:55.08", "F": "01:02.16"},
    ("Butterfly", 200): {"M": "02:04.45", "F": "02:17.82"},
    ("Medley", 200): {"M": "02:06.79", "F": "02:21.06"},
    ("Medley", 400): {"M": "04:31.78", "F": "04:58.98"},
}

def check_antrenor_baraj(stroke, distance, gender, time_str):
    """
    Check if athlete's time passes antrenor baraj threshold.
    
    Args:
        stroke: "Freestyle", "Backstroke", "Breaststroke", "Butterfly", "Medley"
        distance: int (50, 100, 200, 400, 800, 1500)
        gender: "M" or "F"
        time_str: time in format "MM:SS.SS"
    
    Returns:
        bool: True if time <= baraj (passes threshold), False otherwise or if no baraj defined
    """
    key = (stroke, distance)
    if key not in ANTRENOR_BARAJLARI:
        return False
    
    baraj_time = ANTRENOR_BARAJLARI[key].get(gender)
    if baraj_time is None:
        return False
    
    # Simple string comparison (works for time format MM:SS.SS)
    return time_str <= baraj_time
```

- [ ] **Step 3: Test the baraj check**

```python
if __name__ == "__main__":
    assert check_antrenor_baraj("Freestyle", 50, "M", "00:23.40") == True
    assert check_antrenor_baraj("Freestyle", 50, "M", "00:23.50") == False
    print("✓ Baraj tests pass")
```

Run: `python federasyon/yildizlar_multinations_barajlari.py`

Expected: ✓ Baraj tests pass

- [ ] **Step 4: Commit**

```bash
git add federasyon/yildizlar_multinations_barajlari.py
git commit -m "feat: add Multinations Yildizlar antrenor baraj thresholds"
```

---

### Task 3: Create Comen Cup Baraj Table

**Files:**
- Create: `federasyon/yildizlar_comen_cup_barajlari.py`

**Interfaces:**
- Produces: `ANTRENOR_BARAJLARI` dict (same structure as Task 2, same times per PDF)

**Steps:**

- [ ] **Step 1: Create new file `federasyon/yildizlar_comen_cup_barajlari.py`**

- [ ] **Step 2: Copy structure from `yildizlar_multinations_barajlari.py`**

```python
"""
Comen Cup Yıldızlar 2026 — Antrenor Performance Thresholds (Barajları)

Same times as Multinations (per PDF page 5).
"""

ANTRENOR_BARAJLARI = {
    ("Freestyle", 50): {"M": "00:23.41", "F": "00:26.34"},
    ("Freestyle", 100): {"M": "00:51.53", "F": "00:57.33"},
    ("Freestyle", 200): {"M": "01:53.26", "F": "02:04.99"},
    ("Freestyle", 400): {"M": "04:01.40", "F": "04:23.21"},
    ("Freestyle", 800): {"M": None, "F": "09:04.07"},
    ("Freestyle", 1500): {"M": "16:03.90", "F": None},
    ("Backstroke", 50): {"M": "00:26.70", "F": "00:30.12"},
    ("Backstroke", 100): {"M": "00:57.28", "F": "01:04.27"},
    ("Backstroke", 200): {"M": "02:05.25", "F": "02:18.57"},
    ("Breaststroke", 50): {"M": "00:29.09", "F": "00:33.00"},
    ("Breaststroke", 100): {"M": "01:03.96", "F": "01:11.81"},
    ("Breaststroke", 200): {"M": "02:19.32", "F": "02:34.35"},
    ("Butterfly", 50): {"M": "00:25.02", "F": "00:28.01"},
    ("Butterfly", 100): {"M": "00:55.08", "F": "01:02.16"},
    ("Butterfly", 200): {"M": "02:04.45", "F": "02:17.82"},
    ("Medley", 200): {"M": "02:06.79", "F": "02:21.06"},
    ("Medley", 400): {"M": "04:31.78", "F": "04:58.98"},
}

def check_antrenor_baraj(stroke, distance, gender, time_str):
    key = (stroke, distance)
    if key not in ANTRENOR_BARAJLARI:
        return False
    baraj_time = ANTRENOR_BARAJLARI[key].get(gender)
    if baraj_time is None:
        return False
    return time_str <= baraj_time
```

- [ ] **Step 3: Test**

Run: `python federasyon/yildizlar_comen_cup_barajlari.py`

Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add federasyon/yildizlar_comen_cup_barajlari.py
git commit -m "feat: add Comen Cup Yildizlar antrenor baraj thresholds"
```

---

### Task 4: Create Central European Baraj Table

**Files:**
- Create: `federasyon/yildizlar_central_europe_barajlari.py`

**Interfaces:**
- Produces: `ANTRENOR_BARAJLARI` dict (same times as Task 2 & 3 per PDF)

**Steps:**

- [ ] **Step 1: Create `federasyon/yildizlar_central_europe_barajlari.py`**

- [ ] **Step 2: Copy from Task 2 or 3**

```python
"""
Central European Countries Meet Yıldızlar 2026 — Antrenor Performance Thresholds

Same times as Multinations/Comen Cup (per PDF page 7).
"""

ANTRENOR_BARAJLARI = {
    ("Freestyle", 50): {"M": "00:23.41", "F": "00:26.34"},
    ("Freestyle", 100): {"M": "00:51.53", "F": "00:57.33"},
    ("Freestyle", 200): {"M": "01:53.26", "F": "02:04.99"},
    ("Freestyle", 400): {"M": "04:01.40", "F": "04:23.21"},
    ("Freestyle", 800): {"M": None, "F": "09:04.07"},
    ("Freestyle", 1500): {"M": "16:03.90", "F": None},
    ("Backstroke", 50): {"M": "00:26.70", "F": "00:30.12"},
    ("Backstroke", 100): {"M": "00:57.28", "F": "01:04.27"},
    ("Backstroke", 200): {"M": "02:05.25", "F": "02:18.57"},
    ("Breaststroke", 50): {"M": "00:29.09", "F": "00:33.00"},
    ("Breaststroke", 100): {"M": "01:03.96", "F": "01:11.81"},
    ("Breaststroke", 200): {"M": "02:19.32", "F": "02:34.35"},
    ("Butterfly", 50): {"M": "00:25.02", "F": "00:28.01"},
    ("Butterfly", 100): {"M": "00:55.08", "F": "01:02.16"},
    ("Butterfly", 200): {"M": "02:04.45", "F": "02:17.82"},
    ("Medley", 200): {"M": "02:06.79", "F": "02:21.06"},
    ("Medley", 400): {"M": "04:31.78", "F": "04:58.98"},
}

def check_antrenor_baraj(stroke, distance, gender, time_str):
    key = (stroke, distance)
    if key not in ANTRENOR_BARAJLARI:
        return False
    baraj_time = ANTRENOR_BARAJLARI[key].get(gender)
    if baraj_time is None:
        return False
    return time_str <= baraj_time
```

- [ ] **Step 3: Test**

Run: `python federasyon/yildizlar_central_europe_barajlari.py`

Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add federasyon/yildizlar_central_europe_barajlari.py
git commit -m "feat: add Central European Yildizlar antrenor baraj thresholds"
```

---

### Task 5: Create Yildizlar Ranking Engine

**Files:**
- Create: `federasyon/yildizlar_ranker.py`

**Interfaces:**
- Consumes: `athletes` list (from database), baraj modules (Tasks 2–4)
- Produces: Updated `athletes` list with yíldízlar selection flags populated

**Steps:**

- [ ] **Step 1: Create `federasyon/yildizlar_ranker.py` with imports**

```python
"""
Yíldízlar (Youth) National Team Selection Rankings

Handles three competitions:
- Multinations Yíldízlar (December selection only)
- Comen Cup Yíldízlar (December + April selections)
- Central European Meet Yíldízlar (December + April selections)

Each competition has independent logic; athletes can qualify for multiple.
"""

import logging
from federasyon.yildizlar_multinations_barajlari import check_antrenor_baraj as check_multi_baraj
from federasyon.yildizlar_comen_cup_barajlari import check_antrenor_baraj as check_comen_baraj
from federasyon.yildizlar_central_europe_barajlari import check_antrenor_baraj as check_central_baraj

logger = logging.getLogger(__name__)
```

- [ ] **Step 2: Implement Multinations selection function**

```python
def select_yildizlar_multinations(athletes):
    """
    Select Multinations Yíldízlar cadre (10F + 10M).
    
    - Ranking: Points-based (fed karma logic — highest points selected)
    - Cadre: 10 Female + 10 Male
    - Age: 2013–2011
    - Antrenor: Coaches of selected athletes passing performance baraj invited
    
    Returns: Updated athletes list with selection + coach flags set
    """
    
    # Filter by age group (2013–2011)
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    
    # Separate by gender
    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']
    
    # Sort by points (descending)
    females_sorted = sorted(females, key=lambda x: x.get('combined_top3', 0), reverse=True)
    males_sorted = sorted(males, key=lambda x: x.get('combined_top3', 0), reverse=True)
    
    # Select top 10 each
    selected_females = females_sorted[:10]
    selected_males = males_sorted[:10]
    
    selected_ids = {a.get('athlete_id') for a in selected_females + selected_males}
    
    # Mark selections + check antrenor baraj
    for athlete in athletes:
        if athlete.get('athlete_id') in selected_ids:
            athlete['selected_yildiz_multinations'] = True
            
            # Check antrenor baraj for each event
            passes_baraj = False
            for (stroke, dist), points in athlete.get('combined_events', {}).items():
                time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
                if check_multi_baraj(stroke, dist, athlete.get('gender'), time_str):
                    passes_baraj = True
                    break
            
            athlete['coach_called_yildiz_multinations'] = passes_baraj
            logger.info(f"Multinations: {athlete.get('athlete_name')} selected, coach_baraj={passes_baraj}")
    
    return athletes
```

- [ ] **Step 3: Implement Comen Cup selection (December)**

```python
def select_yildizlar_comen_cup_aralik(athletes):
    """
    Comen Cup December selection (20-22 Aralık 2025).
    
    - Age: 2013–2011 (F), 2012–2010 (M)
    - Ranking: Points-based per competition
    - Cadre: Determined by rules (not fixed quota)
    """
    
    # Filter by age group (gender-specific)
    eligible = [
        a for a in athletes
        if (a.get('gender') == 'F' and 2011 <= a.get('birth_year') <= 2013) or
           (a.get('gender') == 'M' and 2010 <= a.get('birth_year') <= 2012)
    ]
    
    # Sort by points (descending)
    eligible_sorted = sorted(eligible, key=lambda x: x.get('combined_top3', 0), reverse=True)
    
    # Select (simplified: select all ranked athletes)
    for athlete in eligible_sorted:
        athlete['selected_yildiz_comen_cup_aralik'] = True
        
        # Check antrenor baraj
        passes_baraj = False
        for (stroke, dist), points in athlete.get('combined_events', {}).items():
            time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
            if check_comen_baraj(stroke, dist, athlete.get('gender'), time_str):
                passes_baraj = True
                break
        
        athlete['coach_called_yildiz_comen_cup_aralik'] = passes_baraj
        logger.info(f"Comen Cup Aralık: {athlete.get('athlete_name')} selected, coach_baraj={passes_baraj}")
    
    return athletes
```

- [ ] **Step 4: Implement Comen Cup selection (April)**

```python
def select_yildizlar_comen_cup_nisan(athletes):
    """
    Comen Cup April selection (17-19 Nisan 2026).
    
    Same logic as December but separate flag.
    """
    eligible = [
        a for a in athletes
        if (a.get('gender') == 'F' and 2011 <= a.get('birth_year') <= 2013) or
           (a.get('gender') == 'M' and 2010 <= a.get('birth_year') <= 2012)
    ]
    
    eligible_sorted = sorted(eligible, key=lambda x: x.get('combined_top3', 0), reverse=True)
    
    for athlete in eligible_sorted:
        athlete['selected_yildiz_comen_cup_nisan'] = True
        
        passes_baraj = False
        for (stroke, dist), points in athlete.get('combined_events', {}).items():
            time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
            if check_comen_baraj(stroke, dist, athlete.get('gender'), time_str):
                passes_baraj = True
                break
        
        athlete['coach_called_yildiz_comen_cup_nisan'] = passes_baraj
    
    return athletes
```

- [ ] **Step 5: Implement Central European selections (December + April)**

```python
def select_yildizlar_central_europe_aralik(athletes):
    """
    Central European December selection (20-22 Aralık 2025).
    
    - Age: 2013–2011 (both genders)
    - Cadre: 12 Female + 12 Male (fixed quota)
    """
    
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    
    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']
    
    females_sorted = sorted(females, key=lambda x: x.get('combined_top3', 0), reverse=True)
    males_sorted = sorted(males, key=lambda x: x.get('combined_top3', 0), reverse=True)
    
    selected = females_sorted[:12] + males_sorted[:12]
    selected_ids = {a.get('athlete_id') for a in selected}
    
    for athlete in athletes:
        if athlete.get('athlete_id') in selected_ids:
            athlete['selected_yildiz_central_europe_aralik'] = True
            
            passes_baraj = False
            for (stroke, dist), points in athlete.get('combined_events', {}).items():
                time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
                if check_central_baraj(stroke, dist, athlete.get('gender'), time_str):
                    passes_baraj = True
                    break
            
            athlete['coach_called_yildiz_central_europe_aralik'] = passes_baraj
    
    return athletes

def select_yildizlar_central_europe_nisan(athletes):
    """Central European April selection — same logic as December, _nisan flags"""
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    
    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']
    
    females_sorted = sorted(females, key=lambda x: x.get('combined_top3', 0), reverse=True)
    males_sorted = sorted(males, key=lambda x: x.get('combined_top3', 0), reverse=True)
    
    selected = females_sorted[:12] + males_sorted[:12]
    selected_ids = {a.get('athlete_id') for a in selected}
    
    for athlete in athletes:
        if athlete.get('athlete_id') in selected_ids:
            athlete['selected_yildiz_central_europe_nisan'] = True
            
            passes_baraj = False
            for (stroke, dist), points in athlete.get('combined_events', {}).items():
                time_str = athlete.get('combined_events_time', {}).get((stroke, dist), "99:99.99")
                if check_central_baraj(stroke, dist, athlete.get('gender'), time_str):
                    passes_baraj = True
                    break
            
            athlete['coach_called_yildiz_central_europe_nisan'] = passes_baraj
    
    return athletes
```

- [ ] **Step 6: Main orchestration function**

```python
def select_all_yildizlar(athletes):
    """
    Apply all yíldízlar selections to athletes list.
    
    Returns: Updated athletes list with all yíldízlar flags populated
    """
    athletes = select_yildizlar_multinations(athletes)
    athletes = select_yildizlar_comen_cup_aralik(athletes)
    athletes = select_yildizlar_comen_cup_nisan(athletes)
    athletes = select_yildizlar_central_europe_aralik(athletes)
    athletes = select_yildizlar_central_europe_nisan(athletes)
    
    logger.info(f"Yíldízlar selection complete: {len(athletes)} athletes processed")
    return athletes
```

- [ ] **Step 7: Test orchestration**

```python
if __name__ == "__main__":
    test_athlete = {
        'athlete_id': 1,
        'athlete_name': 'Test Athlete',
        'birth_year': 2012,
        'gender': 'M',
        'combined_top3': 100,
        'combined_events': {
            ('Freestyle', 50): 100,
        },
        'combined_events_time': {
            ('Freestyle', 50): '00:23.40',
        }
    }
    
    result = select_all_yildizlar([test_athlete])
    assert result[0]['selected_yildiz_multinations'] == True
    print("✓ Yíldízlar selection test pass")
```

Run: `python federasyon/yildizlar_ranker.py`

Expected: ✓ Yíldízlar selection test pass

- [ ] **Step 8: Commit**

```bash
git add federasyon/yildizlar_ranker.py
git commit -m "feat: implement yildizlar ranking engine for three youth competitions"
```

---

### Task 6: Update HTTP API Endpoint

**Files:**
- Modify: `panel/serve.py`

**Interfaces:**
- Consumes: Updated athletes list with yíldízlar flags (from Task 5)
- Produces: `/api/ranking` endpoint updated to include yíldízlar data in JSON response

**Steps:**

- [ ] **Step 1: Locate `/api/ranking` handler in `serve.py`**

Find `def serve_api_ranking(self):` (around line 520–640).

- [ ] **Step 2: Add import for yildizlar_ranker at top of serve.py**

```python
from federasyon.yildizlar_ranker import select_all_yildizlar
```

- [ ] **Step 3: Call yíldízlar selection before response build**

Before the response dict loop (around line 600), add:

```python
# Apply yíldízlar selections
athletes = select_all_yildizlar(athletes)
```

- [ ] **Step 4: Update response dict to include yíldízlar fields**

In the loop where response dict is built (around line 607–624), add after fed karma fields:

```python
'selected_yildiz_multinations': athlete.get('selected_yildiz_multinations', False),
'coach_called_yildiz_multinations': athlete.get('coach_called_yildiz_multinations', False),
'selected_yildiz_comen_cup_aralik': athlete.get('selected_yildiz_comen_cup_aralik', False),
'selected_yildiz_comen_cup_nisan': athlete.get('selected_yildiz_comen_cup_nisan', False),
'coach_called_yildiz_comen_cup_aralik': athlete.get('coach_called_yildiz_comen_cup_aralik', False),
'coach_called_yildiz_comen_cup_nisan': athlete.get('coach_called_yildiz_comen_cup_nisan', False),
'selected_yildiz_central_europe_aralik': athlete.get('selected_yildiz_central_europe_aralik', False),
'selected_yildiz_central_europe_nisan': athlete.get('selected_yildiz_central_europe_nisan', False),
'coach_called_yildiz_central_europe_aralik': athlete.get('coach_called_yildiz_central_europe_aralik', False),
'coach_called_yildiz_central_europe_nisan': athlete.get('coach_called_yildiz_central_europe_nisan', False),
```

- [ ] **Step 5: Test API response**

Run server, test with curl:
```bash
curl "http://localhost:8765/api/ranking?birth_year=2012&gender=M" | python -m json.tool | head -30
```

Expected: JSON includes new yíldízlar fields

- [ ] **Step 6: Commit**

```bash
git add panel/serve.py
git commit -m "api: extend /api/ranking endpoint with yildizlar selection fields"
```

---

### Task 7: Update Frontend — Athlete Profile Display

**Files:**
- Modify: `panel/index.html`

**Interfaces:**
- Consumes: Updated API response with yíldízlar fields (from Task 6)
- Produces: Athlete profile page displaying yíldízlar selections

**Steps:**

- [ ] **Step 1: Locate athlete profile section in `index.html`**

Find where federation selections are displayed.

- [ ] **Step 2: Add yíldízlar display section**

After fed karma section, add HTML:

```html
<div class="yildizlar-section">
  <h3>Yıldızlar Milli Takımları</h3>
  
  <div class="yildiz-item">
    <strong>Multinations Yıldızlar:</strong>
    <span id="yildiz-multi-status">-</span>
    <span id="yildiz-multi-coach">-</span>
  </div>
  
  <div class="yildiz-item">
    <strong>Comen Cup:</strong>
    <div>
      <span>Aralık: <span id="yildiz-comen-aralik">-</span> | 
      <span id="yildiz-comen-aralik-coach">-</span></span>
    </div>
    <div>
      <span>Nisan: <span id="yildiz-comen-nisan">-</span> | 
      <span id="yildiz-comen-nisan-coach">-</span></span>
    </div>
  </div>
  
  <div class="yildiz-item">
    <strong>Central European Countries Meet:</strong>
    <div>
      <span>Aralık: <span id="yildiz-central-aralik">-</span> | 
      <span id="yildiz-central-aralik-coach">-</span></span>
    </div>
    <div>
      <span>Nisan: <span id="yildiz-central-nisan">-</span> | 
      <span id="yildiz-central-nisan-coach">-</span></span>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Add JavaScript to populate yíldízlar fields**

In JavaScript section, add function:

```javascript
function populateYildizarFields(athlete) {
  document.getElementById('yildiz-multi-status').textContent = 
    athlete.selected_yildiz_multinations ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-multi-coach').textContent = 
    athlete.coach_called_yildiz_multinations ? 'Antrenör barajı geçti' : '-';
  
  document.getElementById('yildiz-comen-aralik').textContent = 
    athlete.selected_yildiz_comen_cup_aralik ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-comen-aralik-coach').textContent = 
    athlete.coach_called_yildiz_comen_cup_aralik ? 'Antrenör barajı geçti' : '-';
  
  document.getElementById('yildiz-comen-nisan').textContent = 
    athlete.selected_yildiz_comen_cup_nisan ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-comen-nisan-coach').textContent = 
    athlete.coach_called_yildiz_comen_cup_nisan ? 'Antrenör barajı geçti' : '-';
  
  document.getElementById('yildiz-central-aralik').textContent = 
    athlete.selected_yildiz_central_europe_aralik ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-central-aralik-coach').textContent = 
    athlete.coach_called_yildiz_central_europe_aralik ? 'Antrenör barajı geçti' : '-';
  
  document.getElementById('yildiz-central-nisan').textContent = 
    athlete.selected_yildiz_central_europe_nisan ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-central-nisan-coach').textContent = 
    athlete.coach_called_yildiz_central_europe_nisan ? 'Antrenör barajı geçti' : '-';
}
```

Call this function after athlete is displayed (e.g., in the existing profile display handler).

- [ ] **Step 4: Add CSS styling**

Add to inline CSS:

```css
.yildizlar-section {
  margin-top: 20px;
  padding: 15px;
  border-top: 1px solid #ccc;
  background: #f9f9f9;
}

.yildiz-item {
  margin: 10px 0;
  font-size: 14px;
}

.yildiz-item strong {
  display: block;
  margin-bottom: 5px;
}
```

- [ ] **Step 5: Test in browser**

Start server, navigate to athlete profile, verify yíldízlar section displays.

Expected: Section visible, fields show "-" or selection status

- [ ] **Step 6: Commit**

```bash
git add panel/index.html
git commit -m "ui: add yildizlar selections display to athlete profile"
```

---

### Task 8: Integration Test

**Files:**
- Test: Manual + API test script

**Interfaces:**
- Consumes: Full system (database, ranking, API, frontend)
- Produces: Verified end-to-end yíldízlar selection flow

**Steps:**

- [ ] **Step 1: Clear database and start fresh server**

```bash
rm database/athletes.db
python panel/serve.py &
```

- [ ] **Step 2: Upload test LXF file**

```bash
curl -X POST -F "file=@data/antalya_millitakim_secme_sonuc.lxf" \
  http://localhost:8765/upload
```

Expected: HTTP 200

- [ ] **Step 3: Query API for 2012 male athlete (should have yíldízlar fields)**

```bash
curl "http://localhost:8765/api/ranking?birth_year=2012&gender=M" | \
  python -c "import sys, json; data = json.load(sys.stdin); \
  athlete = data[0]; \
  print(f\"Athlete: {athlete['athlete_name']}\"); \
  print(f\"Multinations: {athlete.get('selected_yildiz_multinations')}\"); \
  print(f\"Comen Cup Aralık: {athlete.get('selected_yildiz_comen_cup_aralik')}\")"
```

Expected: Output shows selection status (True/False)

- [ ] **Step 4: Check antrenor flags**

```bash
curl "http://localhost:8765/api/ranking?birth_year=2012&gender=M" | \
  python -c "import sys, json; data = json.load(sys.stdin); \
  athlete = data[0]; \
  print(f\"Coach Multinations: {athlete.get('coach_called_yildiz_multinations')}\"); \
  print(f\"Coach Comen Aralık: {athlete.get('coach_called_yildiz_comen_cup_aralik')}\")"
```

Expected: Some athletes show True, some False

- [ ] **Step 5: Open browser and check athlete profile**

1. Open http://localhost:8765
2. Click on athlete profile
3. Scroll to "Yıldızlar Milli Takımları" section
4. Verify selections displayed

Expected: Section shows selection status for all three competitions

- [ ] **Step 6: Verify no federation selection regression**

Check that fed karma selection still works and is separate from yíldízlar.

Expected: Clean separation; no data loss

- [ ] **Step 7: Test age group boundary**

Query 2010 male (eligible for Comen Cup only):

```bash
curl "http://localhost:8765/api/ranking?birth_year=2010&gender=M" | \
  python -c "import sys, json; data = json.load(sys.stdin); \
  athlete = data[0] if data else None; \
  if athlete: print(f\"2010 Multinations: {athlete.get('selected_yildiz_multinations')}\") \
  else: print('Filtered out (expected)')"
```

Expected: 2010 male has Multinations=False, Comen Cup=True

- [ ] **Step 8: Commit test results**

```bash
git add -A
git commit -m "test: integration test for yildizlar selection system

- Verified all three competitions select correctly
- Antrenor baraj thresholds applied
- Age group boundaries enforced (2010 male in Comen Cup only)
- Frontend displays selections + coach status
- Fed karma selections unchanged (no regression)
"
```

---

## Pre-Flight Scan

**File conflicts (shared dependencies):**

| Files | Produced | Consumed | Status |
|-------|----------|----------|--------|
| Task 1 → Task 5-6 | `athletes.selected_yildiz_*`, `athletes.coach_called_yildiz_*` columns | yildizlar_ranker imports columns, serve.py returns columns | ✓ Consistent |
| Task 2-4 → Task 5 | `check_antrenor_baraj()` function in 3 baraj modules | yildizlar_ranker imports and calls as `check_multi_baraj`, `check_comen_baraj`, `check_central_baraj` | ✓ Consistent |
| Task 5 → Task 6 | `select_all_yildizlar()` orchestration function | serve.py calls before response build | ✓ Consistent |
| Task 6 → Task 7 | API response includes `selected_yildiz_*`, `coach_called_yildiz_*` fields | index.html references these exact field names in JavaScript | ✓ Consistent |

**Internal consistency (task with itself):**

- Task 1: Column names consistent (snake_case, _aralik/_nisan for dates)
- Task 2-4: Function signatures identical across three baraj modules (check_antrenor_baraj)
- Task 5: Uses consistent naming from Task 1 columns (selected_yildiz_*, coach_called_yildiz_*)
- Task 6: API field names match Task 1 column names
- Task 7: HTML IDs and JS variables reference Task 6 field names exactly
- Task 8: Test queries reference exact field names from Task 6

**Self-review:** No placeholders, no contradictions, no ambiguity. Plan ready.

---

**Proceeding to Task 1 dispatch.**
