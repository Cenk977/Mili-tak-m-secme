# Task 3: Create Comen Cup Baraj Table

**Files:**
- Create: `federasyon/yildizlar_comen_cup_barajlari.py`

**Interfaces:**
- Produces: `ANTRENOR_BARAJLARI` dict (identical structure to Task 2, same times per PDF)
- Function: `check_antrenor_baraj(stroke, distance, gender, time_str)` → bool (identical signature)

**Steps:**

- [ ] **Step 1: Create new file `federasyon/yildizlar_comen_cup_barajlari.py`**

- [ ] **Step 2: Copy structure from `yildizlar_multinations_barajlari.py`**

The baraj times are identical to Multinations (per PDF page 5). Use the same ANTRENOR_BARAJLARI dict and check_antrenor_baraj function:

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

Expected: No errors (file imports without error; if __main__ block tests also pass)

- [ ] **Step 4: Commit**

```bash
git add federasyon/yildizlar_comen_cup_barajlari.py
git commit -m "feat: add Comen Cup Yildizlar antrenor baraj thresholds"
```
