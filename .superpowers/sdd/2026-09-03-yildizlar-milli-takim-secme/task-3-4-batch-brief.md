# Tasks 3-4 (Batched): Create Comen Cup & Central European Baraj Tables

**BATCHING RATIONALE:** Tasks 3 and 4 are identical small transcription work — same structure, same data (ANTRENOR_BARAJLARI dict and check_antrenor_baraj function), different file paths only.

**Files:**
- Create: `federasyon/yildizlar_comen_cup_barajlari.py`
- Create: `federasyon/yildizlar_central_europe_barajlari.py`

**Interfaces (both files):**
- **Produces:** 
  - `ANTRENOR_BARAJLARI` dict: (stroke, distance) → {"M": time_str, "F": time_str}
  - `check_antrenor_baraj(stroke, distance, gender, time_str)` → bool

**Data:** Both files use identical ANTRENOR_BARAJLARI dict (same times as Task 2 per PDF pages 5 and 7).

**Steps:**

- [ ] **File 1: `federasyon/yildizlar_comen_cup_barajlari.py`**

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

- [ ] **File 2: `federasyon/yildizlar_central_europe_barajlari.py`**

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

- [ ] **Step 3: Test both files**

```bash
python federasyon/yildizlar_comen_cup_barajlari.py
python federasyon/yildizlar_central_europe_barajlari.py
```

Expected: No errors

- [ ] **Step 4: Commit both**

```bash
git add federasyon/yildizlar_comen_cup_barajlari.py federasyon/yildizlar_central_europe_barajlari.py
git commit -m "feat: add Comen Cup & Central European Yildizlar antrenor baraj thresholds"
```
