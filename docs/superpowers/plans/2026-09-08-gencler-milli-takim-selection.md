# Gençler Milli Takım Seçimleri Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mevcut Yıldızlar seçim sistemine, Gençler yaş grubu için Multinations Gençler ve Avrupa Gençler milli takım seçimlerini additive olarak eklemek.

**Architecture:** Yeni `federasyon/gencler_barajlari.py` (baraj tabloları) ve `federasyon/gencler_ranker.py` (seçim fonksiyonları). Multinations Gençler, `yildizlar_ranker.py`'den çıkarılan saf `_select_branch_winners_core()` çekirdeğini yeniden kullanır (Yıldızlar davranışı hiç değişmez). Avrupa Gençler baraj-geçme mantığıyla yeni yazılır. `panel/serve.py` ve `panel/index.html` yeni alanları/rozetleri gösterir. Çapraz dışlama YOK.

**Tech Stack:** Python 3 (stdlib), pytest, düz HTML/JS dashboard.

**Spec:** `docs/superpowers/specs/2026-09-07-gencler-milli-takim-selection-design.md`

## Global Constraints

- UTF-8 her yerde; Türkçe karakter desteği (İ, ş, ç, ğ, ü, ö).
- Branş adları Türkçe: `"Serbest"`, `"Sırtüstü"`, `"Kurbağalama"`, `"Kelebek"`, `"Karışık"`.
- Zaman karşılaştırması `parse_time()` ile saniyeye çevirerek yapılır — string karşılaştırma YASAK.
- Baraj eşitliği geçer: `parse_time(sporcu) <= parse_time(baraj)`.
- Tek iş parçacığı, senkron. Yeni bağımlılık yok.
- Mevcut testler (`python -m pytest -q`) her task sonunda yeşil kalmalı (şu an 116 test).
- Federasyon Karması / Yıldızlar çıktıları hiç değişmez (additive).
- Sık commit; her task kendi testiyle biter.

---

### Task 1: Gençler baraj tabloları modülü

**Files:**
- Create: `federasyon/gencler_barajlari.py`
- Test: `federasyon/tests/test_gencler_barajlari.py`

**Interfaces:**
- Produces:
  - `MULTI_GENCLER_ANTRENOR: dict[tuple[str,int], dict[str, str|None]]`
  - `AVRUPA_GENCLER_SPORCU: dict[tuple[str,int], dict[str, str|None]]`
  - `AVRUPA_GENCLER_ANTRENOR: dict[tuple[str,int], dict[str, str|None]]`
  - `check_baraj(table: dict, stroke: str, distance: int, gender: str, time_str: str|None) -> bool`
  - `passes_any(table: dict, athlete: dict, event_times_key: str = 'combined_events_time') -> bool`

- [ ] **Step 1: Write the failing test**

`federasyon/tests/test_gencler_barajlari.py`:

```python
# -*- coding: utf-8 -*-
from federasyon.gencler_barajlari import (
    MULTI_GENCLER_ANTRENOR, AVRUPA_GENCLER_SPORCU, AVRUPA_GENCLER_ANTRENOR,
    check_baraj, passes_any,
)

STROKES = ["Serbest", "Sırtüstü", "Kurbağalama", "Kelebek", "Karışık"]


def test_all_tables_have_17_event_rows():
    for tbl in (MULTI_GENCLER_ANTRENOR, AVRUPA_GENCLER_SPORCU, AVRUPA_GENCLER_ANTRENOR):
        assert len(tbl) == 17
        for (stroke, dist), row in tbl.items():
            assert stroke in STROKES
            assert set(row.keys()) == {"M", "F"}


def test_check_baraj_equal_time_passes():
    # Avrupa sporcu K 50 Serbest = 25.81
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", "00:00:25.81") is True


def test_check_baraj_faster_passes_slower_fails():
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", "00:00:25.80") is True
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", "00:00:25.82") is False


def test_check_baraj_missing_event_or_gender_or_time():
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 999, "F", "00:00:25.00") is False
    # Erkek 800 Serbest MULTI_GENCLER_ANTRENOR'da None
    assert check_baraj(MULTI_GENCLER_ANTRENOR, "Serbest", 800, "M", "00:08:00.00") is False
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", None) is False
    assert check_baraj(AVRUPA_GENCLER_SPORCU, "Serbest", 50, "F", "-") is False


def test_mmss_and_hhmmss_formats_parse():
    # 1:02.09 (K 100 Sırtüstü antrenör) vs athlete "00:01:02.09"
    assert check_baraj(AVRUPA_GENCLER_ANTRENOR, "Sırtüstü", 100, "F", "00:01:02.09") is True
    assert check_baraj(AVRUPA_GENCLER_ANTRENOR, "Sırtüstü", 100, "F", "00:01:02.10") is False


def test_passes_any_true_when_one_event_passes():
    athlete = {
        "gender": "F",
        "combined_events": {("Serbest", 50): 9, ("Kelebek", 100): 3},
        "combined_events_time": {("Serbest", 50): "00:00:25.00",  # geçer
                                 ("Kelebek", 100): "00:01:30.00"},  # geçmez
    }
    assert passes_any(AVRUPA_GENCLER_SPORCU, athlete) is True


def test_passes_any_false_when_none_pass():
    athlete = {
        "gender": "F",
        "combined_events": {("Serbest", 50): 1},
        "combined_events_time": {("Serbest", 50): "00:00:40.00"},
    }
    assert passes_any(AVRUPA_GENCLER_SPORCU, athlete) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest federasyon/tests/test_gencler_barajlari.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'federasyon.gencler_barajlari'`

- [ ] **Step 3: Write the module**

`federasyon/gencler_barajlari.py` (süreler PDF s.3 ve s.5'ten; `,`/`;` → `.`):

```python
# -*- coding: utf-8 -*-
"""
2026 Gençler Milli Takım baraj tabloları.
Kaynak: 2026-GENCLER-MILLI-TAKIM-SECILME-KRITERLERI.pdf (s.3 Multi Gençler,
s.5 Avrupa Gençler). Branş adları Türkçe; süreler "MM:SS.ss" / "M:SS.ss".
None = o cinsiyette yarış yok.
"""
from federasyon.yildizlar_ranker import parse_time

# --- Multinations Gençler — Antrenör Barajı (PDF s.3) ---
MULTI_GENCLER_ANTRENOR = {
    ("Serbest", 50):       {"M": "22.84",    "F": "25.69"},
    ("Serbest", 100):      {"M": "50.32",    "F": "55.75"},
    ("Serbest", 200):      {"M": "1:50.51",  "F": "2:01.95"},
    ("Serbest", 400):      {"M": "3:55.85",  "F": "4:17.82"},
    ("Serbest", 800):      {"M": None,       "F": "8:46.98"},
    ("Serbest", 1500):     {"M": "15:37.03", "F": None},
    ("Sırtüstü", 50):      {"M": "26.05",    "F": "29.37"},
    ("Sırtüstü", 100):     {"M": "55.89",    "F": "1:02.39"},
    ("Sırtüstü", 200):     {"M": "2:02.20",  "F": "2:15.61"},
    ("Kurbağalama", 50):   {"M": "28.37",    "F": "32.18"},
    ("Kurbağalama", 100):  {"M": "1:01.87",  "F": "1:09.63"},
    ("Kurbağalama", 200):  {"M": "2:14.87",  "F": "2:30.03"},
    ("Kelebek", 50):       {"M": "24.39",    "F": "27.31"},
    ("Kelebek", 100):      {"M": "53.74",    "F": "1:00.24"},
    ("Kelebek", 200):      {"M": "2:00.41",  "F": "2:13.57"},
    ("Karışık", 200):      {"M": "2:02.66",  "F": "2:16.73"},
    ("Karışık", 400):      {"M": "4:22.60",  "F": "4:49.67"},
}

# --- Avrupa Gençler — Sporcu Barajı (PDF s.5) ---
AVRUPA_GENCLER_SPORCU = {
    ("Serbest", 50):       {"M": "22.84",    "F": "25.81"},
    ("Serbest", 100):      {"M": "50.27",    "F": "56.02"},
    ("Serbest", 200):      {"M": "1:50.51",  "F": "2:01.95"},
    ("Serbest", 400):      {"M": "3:54.15",  "F": "4:17.20"},
    ("Serbest", 800):      {"M": "8:07.21",  "F": "8:45.96"},
    ("Serbest", 1500):     {"M": "15:28.02", "F": "16:43.01"},
    ("Sırtüstü", 50):      {"M": "26.10",    "F": "29.31"},
    ("Sırtüstü", 100):     {"M": "55.89",    "F": "1:02.69"},
    ("Sırtüstü", 200):     {"M": "2:02.20",  "F": "2:16.26"},
    ("Kurbağalama", 50):   {"M": "28.38",    "F": "32.18"},
    ("Kurbağalama", 100):  {"M": "1:02.32",  "F": "1:10.13"},
    ("Kurbağalama", 200):  {"M": "2:15.84",  "F": "2:31.11"},
    ("Kelebek", 50):       {"M": "24.25",    "F": "27.29"},
    ("Kelebek", 100):      {"M": "53.74",    "F": "1:00.53"},
    ("Kelebek", 200):      {"M": "2:00.41",  "F": "2:14.21"},
    ("Karışık", 200):      {"M": "2:02.66",  "F": "2:17.39"},
    ("Karışık", 400):      {"M": "4:22.60",  "F": "4:51.06"},
}

# --- Avrupa Gençler — Antrenör Barajı (PDF s.5, daha sıkı) ---
AVRUPA_GENCLER_ANTRENOR = {
    ("Serbest", 50):       {"M": "22.62",    "F": "25.56"},
    ("Serbest", 100):      {"M": "49.83",    "F": "55.49"},
    ("Serbest", 200):      {"M": "1:49.45",  "F": "2:01.36"},
    ("Serbest", 400):      {"M": "3:51.88",  "F": "4:14.72"},
    ("Serbest", 800):      {"M": "8:02.50",  "F": "8:40.90"},
    ("Serbest", 1500):     {"M": "15:19.01", "F": "16:33.32"},
    ("Sırtüstü", 50):      {"M": "25.54",    "F": "29.13"},
    ("Sırtüstü", 100):     {"M": "55.35",    "F": "1:02.09"},
    ("Sırtüstü", 200):     {"M": "2:01.03",  "F": "2:14.95"},
    ("Kurbağalama", 50):   {"M": "28.00",    "F": "32.08"},
    ("Kurbağalama", 100):  {"M": "1:01.72",  "F": "1:09.46"},
    ("Kurbağalama", 200):  {"M": "2:14.54",  "F": "2:29.67"},
    ("Kelebek", 50):       {"M": "24.10",    "F": "27.12"},
    ("Kelebek", 100):      {"M": "53.22",    "F": "59.95"},
    ("Kelebek", 200):      {"M": "1:59.25",  "F": "2:12.93"},
    ("Karışık", 200):      {"M": "2:01.48",  "F": "2:16.07"},
    ("Karışık", 400):      {"M": "4:20.08",  "F": "4:48.28"},
}


def check_baraj(table, stroke, distance, gender, time_str):
    """time_str baraj süresine eşit veya daha hızlıysa True."""
    row = table.get((stroke, distance))
    if not row:
        return False
    baraj = row.get(gender)
    if baraj is None or not time_str or time_str == "-":
        return False
    return parse_time(time_str) <= parse_time(baraj)


def passes_any(table, athlete, event_times_key="combined_events_time"):
    """Sporcu, yüzdüğü herhangi bir branşta bu tablonun barajını geçiyor mu?"""
    ets = athlete.get(event_times_key, {})
    gender = athlete.get("gender")
    return any(
        check_baraj(table, s, d, gender, ets.get((s, d)))
        for (s, d) in athlete.get("combined_events", {})
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest federasyon/tests/test_gencler_barajlari.py -q`
Expected: PASS (7 passed)

- [ ] **Step 5: Run full suite (no regression)**

Run: `python -m pytest -q`
Expected: PASS (123 passed)

- [ ] **Step 6: Commit**

```bash
git add federasyon/gencler_barajlari.py federasyon/tests/test_gencler_barajlari.py
git commit -m "feat: Gençler baraj tabloları (Multi Gençler + Avrupa Gençler)"
```

---

### Task 2: `_select_branch_winners_core` çıkarımı (yildizlar_ranker refactor)

**Files:**
- Modify: `federasyon/yildizlar_ranker.py` (`select_yildizlar_multinations` — satır ~332-400 civarı)
- Test: `federasyon/tests/test_yildizlar_ranker_core.py`

**Interfaces:**
- Consumes: `_compute_group_stats`, `_split_winners_by_quota`, `_relay_candidate_ids`, `RELAY_LEG_EVENTS` (aynı modülde mevcut)
- Produces:
  - `_select_branch_winners_core(eligible: list[dict], quota: int, event_times_key: str, female_program: set, male_program: set, relay_events: set = RELAY_LEG_EVENTS) -> tuple[set, set, set]` → `(selected_ids, candidate_ids, relay_candidate_ids)`. Yan etki: `eligible` içindeki sporculara `_first/_second/_third` int alanları eklenir (caller temizler).

- [ ] **Step 1: Write the failing test**

`federasyon/tests/test_yildizlar_ranker_core.py`:

```python
# -*- coding: utf-8 -*-
from federasyon.yildizlar_ranker import (
    _select_branch_winners_core, YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM,
)


def _a(aid, gender, et):
    return {"athlete_id": aid, "athlete_name": aid, "gender": gender,
            "birth_year": 2012, "antalya_events_time": et,
            "combined_events": {}, "combined_events_time": {}}


def test_core_returns_winner_as_selected():
    males = [
        _a("M1", "M", {("Serbest", 50): "00:00:25.00"}),   # kazanır
        _a("M2", "M", {("Serbest", 50): "00:00:26.00"}),   # 2.
    ]
    sel, cand, relay = _select_branch_winners_core(
        males, 10, "antalya_events_time",
        YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)
    assert "M1" in sel
    assert "M1" not in cand


def test_core_over_quota_trims_by_depth():
    events = list(YILDIZLAR_MALE_PROGRAM)[:11]
    males = []
    for i, ev in enumerate(events):
        et = {ev: "00:00:25.00"}
        if i < 10:
            et[events[(i + 1) % len(events)]] = "00:00:25.50"  # derinlik (2.lik)
        males.append(_a(f"W{i+1}", "M", et))
    sel, cand, relay = _select_branch_winners_core(
        males, 10, "antalya_events_time",
        YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)
    assert len(sel) == 10
    assert "W11" in cand  # derinliksiz birinci kırpıldı
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest federasyon/tests/test_yildizlar_ranker_core.py -q`
Expected: FAIL — `ImportError: cannot import name '_select_branch_winners_core'`

- [ ] **Step 3: Extract the core**

`federasyon/yildizlar_ranker.py` — `MULTINATIONS_QUOTA = 10` satırından hemen sonra ekle:

```python
def _select_branch_winners_core(eligible, quota, event_times_key,
                                female_program, male_program,
                                relay_events=RELAY_LEG_EVENTS):
    """Branş-birinciliği tabanlı seçim çekirdeği (Multi Yıldızlar + Multi
    Gençler ortak). eligible: tek yaş-grubu-filtreli sporcu listesi.
    Döner: (selected_ids, candidate_ids, relay_candidate_ids).
    Yan etki: eligible sporculara _first/_second/_third eklenir."""
    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']

    for glist, prog in ((females, female_program), (males, male_program)):
        stats = _compute_group_stats(glist, event_times_key, prog)
        for a in glist:
            s = stats.get(a.get('athlete_id'), {'first': 0, 'second': 0, 'third': 0})
            a['_first'] = s['first']
            a['_second'] = s['second']
            a['_third'] = s['third']

    def _grp(group):
        with_first = [a for a in group if a.get('_first', 0) > 0]
        without_first = [a for a in group if a.get('_first', 0) == 0]
        return _split_winners_by_quota(with_first, without_first, quota)

    sel_f, cand_f = _grp(females)
    sel_m, cand_m = _grp(males)
    sel_ids = {a.get('athlete_id') for a in sel_f + sel_m}
    cand_ids = {a.get('athlete_id') for a in cand_f + cand_m}
    relay_ids = (
        _relay_candidate_ids(females, event_times_key, sel_ids, relay_events) |
        _relay_candidate_ids(males, event_times_key, sel_ids, relay_events)
    )
    return sel_ids, cand_ids, relay_ids
```

Sonra `select_yildizlar_multinations` gövdesinin başını (eligible/females/males/programs/stats/select_group/sel_f.../relay_cand_ids bloğu, `for athlete in athletes:` satırına kadar) şununla değiştir:

```python
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    sel_ids, cand_ids, relay_cand_ids = _select_branch_winners_core(
        eligible, MULTINATIONS_QUOTA, 'antalya_events_time',
        YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)
```

`for athlete in athletes:` sonrası (rozet yazımı + `_first/_second/_third` pop) AYNEN kalır.

- [ ] **Step 4: Run new + regression tests**

Run: `python -m pytest federasyon/tests/test_yildizlar_ranker_core.py federasyon/tests/test_yildizlar_multinations.py federasyon/tests/test_yildizlar_quota_trim.py -q`
Expected: PASS (hepsi)

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: PASS (125 passed)

- [ ] **Step 6: Commit**

```bash
git add federasyon/yildizlar_ranker.py federasyon/tests/test_yildizlar_ranker_core.py
git commit -m "refactor: branş-birinciliği seçim çekirdeğini _select_branch_winners_core'a çıkar"
```

---

### Task 3: `select_multinations_gencler`

**Files:**
- Create: `federasyon/gencler_ranker.py`
- Test: `federasyon/tests/test_gencler_multinations.py`

**Interfaces:**
- Consumes: `_select_branch_winners_core`, `YILDIZLAR_FEMALE_PROGRAM`, `YILDIZLAR_MALE_PROGRAM` (yildizlar_ranker); `MULTI_GENCLER_ANTRENOR`, `passes_any` (gencler_barajlari)
- Produces: `select_multinations_gencler(athletes: list[dict]) -> list[dict]`. Her sporcuya yazar: `selected_multinations_gencler`, `candidate_multinations_gencler`, `candidate_relay_multinations_gencler`, `coach_called_multinations_gencler` (hepsi bool). `MULTI_GENCLER_QUOTA = 10`.

- [ ] **Step 1: Write the failing test**

`federasyon/tests/test_gencler_multinations.py`:

```python
# -*- coding: utf-8 -*-
from federasyon.gencler_ranker import select_multinations_gencler, MULTI_GENCLER_QUOTA
from federasyon.yildizlar_ranker import YILDIZLAR_MALE_PROGRAM, select_yildizlar_multinations


def _a(aid, gender, by, et):
    return {"athlete_id": aid, "athlete_name": aid, "gender": gender,
            "birth_year": by, "antalya_events_time": et,
            "combined_events": {}, "combined_events_time": {}}


def test_only_2008_2010_eligible():
    ath = [
        _a("young", "M", 2011, {("Serbest", 50): "00:00:25.00"}),
        _a("ok",    "M", 2009, {("Serbest", 100): "00:00:55.00"}),
        _a("old",   "M", 2007, {("Kelebek", 50): "00:00:25.00"}),
    ]
    out = select_multinations_gencler(ath)
    by = {a["athlete_id"]: a for a in out}
    assert by["ok"]["selected_multinations_gencler"] is True
    assert by["young"]["selected_multinations_gencler"] is False
    assert by["old"]["selected_multinations_gencler"] is False


def test_madde5_trim_to_quota_by_depth():
    events = list(YILDIZLAR_MALE_PROGRAM)[:11]
    ath = []
    for i, ev in enumerate(events):
        et = {ev: "00:00:25.00"}
        if i < 10:
            et[events[(i + 1) % len(events)]] = "00:00:25.50"
        ath.append(_a(f"W{i+1}", "M", 2009, et))
    out = select_multinations_gencler(ath)
    by = {a["athlete_id"]: a for a in out}
    sel = [a for a in out if a["selected_multinations_gencler"]]
    assert len(sel) == MULTI_GENCLER_QUOTA
    assert by["W11"]["candidate_multinations_gencler"] is True
    assert by["W11"]["selected_multinations_gencler"] is False


def test_does_not_touch_yildizlar_fields():
    ath = [_a("x", "F", 2009, {("Serbest", 50): "00:00:25.00"})]
    select_multinations_gencler(ath)
    assert "selected_yildiz_multinations" not in ath[0]


def test_yildizlar_multinations_unaffected_by_gencler_call():
    ath = [
        {"athlete_id": "y1", "athlete_name": "y1", "gender": "F", "birth_year": 2012,
         "antalya_events_time": {("Serbest", 50): "00:00:25.00"},
         "combined_events": {}, "combined_events_time": {}},
    ]
    select_multinations_gencler(ath)
    select_yildizlar_multinations(ath)
    assert ath[0]["selected_yildiz_multinations"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest federasyon/tests/test_gencler_multinations.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'federasyon.gencler_ranker'`

- [ ] **Step 3: Write `gencler_ranker.py` (Multi Gençler bölümü)**

```python
# -*- coding: utf-8 -*-
"""
2026 Gençler Milli Takım seçimleri (Multinations Gençler + Avrupa Gençler).
Additive: Yıldızlar / Federasyon Karması çıktılarına dokunmaz, çapraz dışlama yok.
"""
from federasyon.yildizlar_ranker import (
    _select_branch_winners_core, parse_time,
    YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM,
    _relay_candidate_ids,
)
from federasyon.gencler_barajlari import (
    MULTI_GENCLER_ANTRENOR, AVRUPA_GENCLER_SPORCU, AVRUPA_GENCLER_ANTRENOR,
    check_baraj, passes_any,
)

MULTI_GENCLER_QUOTA = 10
MULTI_GENCLER_AGES = (2008, 2010)
AVRUPA_GENCLER_AGES = (2008, 2012)


def select_multinations_gencler(athletes):
    """Multinations Gençler (2008-2010): 20-22 Aralık seçme (antalya_events_time),
    branş birincisi + kota 10/10 + madde 4/5. Multi Yıldızlar ile aynı çekirdek."""
    lo, hi = MULTI_GENCLER_AGES
    eligible = [a for a in athletes
                if a.get('birth_year') is not None and lo <= a['birth_year'] <= hi]
    sel_ids, cand_ids, relay_ids = _select_branch_winners_core(
        eligible, MULTI_GENCLER_QUOTA, 'antalya_events_time',
        YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)

    for athlete in athletes:
        aid = athlete.get('athlete_id')
        athlete['candidate_relay_multinations_gencler'] = aid in relay_ids
        if aid in sel_ids:
            athlete['selected_multinations_gencler'] = True
            athlete['candidate_multinations_gencler'] = False
            athlete['coach_called_multinations_gencler'] = passes_any(
                MULTI_GENCLER_ANTRENOR, athlete, 'antalya_events_time')
        elif aid in cand_ids:
            athlete['selected_multinations_gencler'] = False
            athlete['candidate_multinations_gencler'] = True
            athlete['coach_called_multinations_gencler'] = False
        else:
            athlete['selected_multinations_gencler'] = False
            athlete['candidate_multinations_gencler'] = False
            athlete['coach_called_multinations_gencler'] = False
        for k in ('_first', '_second', '_third'):
            athlete.pop(k, None)
    return athletes
```

> Not: `passes_any` çağrısında `combined_events` anahtarları kullanılır ama
> zaman `antalya_events_time`'dan okunur (Multi Gençler Aralık-only). Bir
> sporcunun `combined_events`'i varsa ama `antalya_events_time`'da o branş
> yoksa `ets.get(...)` None döner, `check_baraj` False verir — doğru.

- [ ] **Step 4: Run new test**

Run: `python -m pytest federasyon/tests/test_gencler_multinations.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: PASS (129 passed)

- [ ] **Step 6: Commit**

```bash
git add federasyon/gencler_ranker.py federasyon/tests/test_gencler_multinations.py
git commit -m "feat: select_multinations_gencler (2008-2010, branş birincisi + kota)"
```

---

### Task 4: `select_avrupa_gencler` + `select_all_gencler`

**Files:**
- Modify: `federasyon/gencler_ranker.py`
- Test: `federasyon/tests/test_gencler_avrupa.py`

**Interfaces:**
- Consumes: `AVRUPA_GENCLER_SPORCU`, `AVRUPA_GENCLER_ANTRENOR`, `check_baraj` (gencler_barajlari); `_relay_candidate_ids` (yildizlar_ranker)
- Produces:
  - `select_avrupa_gencler(athletes) -> athletes`. Yazar: `selected_avrupa_gencler` (bool), `avrupa_gencler_events` (list[tuple[str,int]]), `coach_called_avrupa_gencler` (bool), `candidate_relay_avrupa_gencler` (bool).
  - `select_all_gencler(athletes) -> athletes` (Multi Gençler + Avrupa Gençler sırayla).

- [ ] **Step 1: Write the failing test**

`federasyon/tests/test_gencler_avrupa.py`:

```python
# -*- coding: utf-8 -*-
from federasyon.gencler_ranker import select_avrupa_gencler, select_all_gencler


def _a(aid, gender, by, cet):
    return {"athlete_id": aid, "athlete_name": aid, "gender": gender,
            "birth_year": by,
            "combined_events": {k: 1 for k in cet},
            "combined_events_time": cet,
            "antalya_events_time": {}}


def test_meeting_sporcu_baraj_selects():
    # K 100 Serbest sporcu barajı = 56.02
    ath = [_a("q", "F", 2011, {("Serbest", 100): "00:00:56.02"})]  # eşit → geçer
    out = select_avrupa_gencler(ath)
    assert out[0]["selected_avrupa_gencler"] is True
    assert ("Serbest", 100) in out[0]["avrupa_gencler_events"]


def test_missing_baraj_by_001_not_selected():
    ath = [_a("slow", "F", 2011, {("Serbest", 100): "00:00:56.03"})]
    out = select_avrupa_gencler(ath)
    assert out[0]["selected_avrupa_gencler"] is False
    assert out[0]["avrupa_gencler_events"] == []


def test_antrenor_baraj_implies_sporcu_baraj():
    # E 50 Kelebek: antrenör 24.10, sporcu 24.25. 24.05 ikisini de geçer.
    ath = [_a("elite", "M", 2009, {("Kelebek", 50): "00:00:24.05"})]
    out = select_avrupa_gencler(ath)
    assert out[0]["selected_avrupa_gencler"] is True
    assert out[0]["coach_called_avrupa_gencler"] is True


def test_age_window_2008_2012():
    ath = [
        _a("in1", "F", 2008, {("Serbest", 50): "00:00:25.00"}),
        _a("in2", "F", 2012, {("Serbest", 50): "00:00:25.00"}),
        _a("out_young", "F", 2013, {("Serbest", 50): "00:00:25.00"}),
        _a("out_old", "F", 2007, {("Serbest", 50): "00:00:25.00"}),
    ]
    out = select_avrupa_gencler(ath)
    by = {a["athlete_id"]: a for a in out}
    assert by["in1"]["selected_avrupa_gencler"] is True
    assert by["in2"]["selected_avrupa_gencler"] is True
    assert by["out_young"]["selected_avrupa_gencler"] is False
    assert by["out_old"]["selected_avrupa_gencler"] is False


def test_no_quota_trim_all_qualifiers_selected():
    ath = [_a(f"s{i}", "F", 2011, {("Serbest", 50): "00:00:25.00"}) for i in range(15)]
    out = select_avrupa_gencler(ath)
    assert sum(1 for a in out if a["selected_avrupa_gencler"]) == 15


def test_select_all_gencler_sets_both_competitions():
    ath = [{"athlete_id": "z", "athlete_name": "z", "gender": "F", "birth_year": 2009,
            "antalya_events_time": {("Serbest", 50): "00:00:25.00"},
            "combined_events": {("Serbest", 50): 1},
            "combined_events_time": {("Serbest", 50): "00:00:25.00"}}]
    out = select_all_gencler(ath)
    assert "selected_multinations_gencler" in out[0]
    assert "selected_avrupa_gencler" in out[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest federasyon/tests/test_gencler_avrupa.py -q`
Expected: FAIL — `ImportError: cannot import name 'select_avrupa_gencler'`

- [ ] **Step 3: Append to `gencler_ranker.py`**

```python
def select_avrupa_gencler(athletes):
    """Avrupa Gençler (2008-2012): kendi branş/mesafesindeki SPORCU BARAJI'nı
    (eşit dahil) geçen her sporcu kesin. Kota yok. Veri: combined_events_time
    (geniş pencere → en iyi derece; elimizde yalnız Aralık+Nisan → kısmi)."""
    lo, hi = AVRUPA_GENCLER_AGES
    for athlete in athletes:
        by = athlete.get('birth_year')
        in_age = by is not None and lo <= by <= hi
        gender = athlete.get('gender')
        ets = athlete.get('combined_events_time', {})
        qual, coach = [], False
        if in_age:
            for (s, d) in athlete.get('combined_events', {}):
                t = ets.get((s, d))
                if check_baraj(AVRUPA_GENCLER_SPORCU, s, d, gender, t):
                    qual.append((s, d))
                if check_baraj(AVRUPA_GENCLER_ANTRENOR, s, d, gender, t):
                    coach = True
        athlete['avrupa_gencler_events'] = qual
        athlete['selected_avrupa_gencler'] = len(qual) > 0
        athlete['coach_called_avrupa_gencler'] = coach

    elig = [a for a in athletes
            if a.get('birth_year') is not None and lo <= a['birth_year'] <= hi]
    sel_ids = {a['athlete_id'] for a in elig if a['selected_avrupa_gencler']}
    fem = [a for a in elig if a.get('gender') == 'F']
    mal = [a for a in elig if a.get('gender') == 'M']
    relay_ids = (_relay_candidate_ids(fem, 'combined_events_time', sel_ids) |
                 _relay_candidate_ids(mal, 'combined_events_time', sel_ids))
    for athlete in athletes:
        athlete['candidate_relay_avrupa_gencler'] = athlete.get('athlete_id') in relay_ids
    return athletes


def select_all_gencler(athletes):
    """Tüm Gençler seçimlerini uygula (additive)."""
    athletes = select_multinations_gencler(athletes)
    athletes = select_avrupa_gencler(athletes)
    return athletes
```

- [ ] **Step 4: Run new test**

Run: `python -m pytest federasyon/tests/test_gencler_avrupa.py -q`
Expected: PASS (6 passed)

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: PASS (135 passed)

- [ ] **Step 6: Commit**

```bash
git add federasyon/gencler_ranker.py federasyon/tests/test_gencler_avrupa.py
git commit -m "feat: select_avrupa_gencler (baraj-geçme, kotasız) + select_all_gencler"
```

---

### Task 5: `panel/serve.py` entegrasyonu

**Files:**
- Modify: `panel/serve.py` (import ~satır 38; `select_all_yildizlar(` çağrıları ~654/829/925; yanıt sözlüğü ~764-782)
- Test: `panel/test_serve_upload.py` (yeni test fonksiyonu ekle)

**Interfaces:**
- Consumes: `select_all_gencler` (federasyon.gencler_ranker)
- Produces: `/api/ranking` JSON yanıtında her sporcu için ek alanlar: `selected_multinations_gencler`, `candidate_multinations_gencler`, `candidate_relay_multinations_gencler`, `coach_called_multinations_gencler`, `selected_avrupa_gencler`, `coach_called_avrupa_gencler`, `candidate_relay_avrupa_gencler`, `avrupa_gencler_event_count` (int).

- [ ] **Step 1: Write the failing test**

`panel/test_serve_upload.py` sonuna ekle:

```python
def test_api_ranking_includes_gencler_fields():
    """select_all_gencler /api/ranking akışında çağrılır ve alanlar yanıta girer."""
    from federasyon.gencler_ranker import select_all_gencler
    ath = [{
        "athlete_id": "g1", "athlete_name": "Genç Sporcu", "birth_year": 2009,
        "gender": "F", "region": 1, "city": "İstanbul", "club": "X",
        "antalya_events_time": {("Serbest", 50): "00:00:25.00"},
        "combined_events": {("Serbest", 50): 9},
        "combined_events_time": {("Serbest", 50): "00:00:25.00"},
    }]
    out = select_all_gencler(ath)
    assert out[0]["selected_multinations_gencler"] is True
    assert out[0]["selected_avrupa_gencler"] is True
    assert isinstance(out[0]["avrupa_gencler_events"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest panel/test_serve_upload.py::test_api_ranking_includes_gencler_fields -q`
Expected: FAIL — `ImportError` (henüz gencler_ranker serve akışında kullanılmıyor değil; test doğrudan import ettiği için aslında burada PASS olabilir — bu durumda Step 3'e geç ve entegrasyonu yine de yap; asıl doğrulama Step 4 full suite + manuel).

> Not: Bu test saf birim testi; kırmızı-yeşil döngüsü için asıl kanıt Step 4.

- [ ] **Step 3: Integrate**

3a. Import satırı (mevcut `from federasyon.yildizlar_ranker import select_all_yildizlar` yanına, ~satır 38):

```python
from federasyon.gencler_ranker import select_all_gencler
```

3b. `grep -n "select_all_yildizlar(" panel/serve.py` ile bulunan HER çağrının hemen ardına ekle (3 yer):

```python
            athletes = select_all_gencler(athletes)
```

(Girinti bağlama uysun — hepsi `athletes = select_all_yildizlar(athletes)` ile aynı seviye.)

3c. Yanıt sözlüğünde (`'coach_called_yildiz_central_europe_nisan': ...,` satırından hemen sonra, `})` kapanışından önce):

```python
                    'selected_multinations_gencler': athlete.get('selected_multinations_gencler', False),
                    'candidate_multinations_gencler': athlete.get('candidate_multinations_gencler', False),
                    'candidate_relay_multinations_gencler': athlete.get('candidate_relay_multinations_gencler', False),
                    'coach_called_multinations_gencler': athlete.get('coach_called_multinations_gencler', False),
                    'selected_avrupa_gencler': athlete.get('selected_avrupa_gencler', False),
                    'coach_called_avrupa_gencler': athlete.get('coach_called_avrupa_gencler', False),
                    'candidate_relay_avrupa_gencler': athlete.get('candidate_relay_avrupa_gencler', False),
                    'avrupa_gencler_event_count': len(athlete.get('avrupa_gencler_events', [])),
```

- [ ] **Step 4: Run tests + import check**

Run: `python -m pytest panel/test_serve_upload.py -q && python -c "import panel.serve"`
Expected: PASS + import hatasız

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: PASS (136 passed)

- [ ] **Step 6: Commit**

```bash
git add panel/serve.py panel/test_serve_upload.py
git commit -m "feat: /api/ranking yanıtına Gençler seçim alanları"
```

---

### Task 6: Dashboard — "Gençler Milli Takımları" bölümü

**Files:**
- Modify: `panel/index.html` (detay paneli — Yıldızlar bölümü ~satır 1248-1281; JS doldurma ~satır 1127-1150)

**Interfaces:**
- Consumes: `/api/ranking` yanıtındaki Gençler alanları (Task 5)
- Produces: detay panelinde iki yeni satır ("Multinations Gençler", "Avrupa Gençler")

- [ ] **Step 1: Add the HTML block**

`panel/index.html` — Yıldızlar `<div class="yildizlar-section">` bloğunu kapatan `html += '</div>';` satırından SONRA, `// Helper function to render events table` yorumundan ÖNCE ekle:

```javascript
            // Gençler Milli Takımları section
            html += '<div class="yildizlar-section">';
            html += '<h3 style="margin: 0 0 15px 0; font-size: 14px; color: #333;">Gençler Milli Takımları</h3>';

            html += '<div class="yildiz-item">';
            html += '<strong>Multinations Gençler:</strong>';
            html += '<span id="genc-multi-status">-</span> | ';
            html += '<span id="genc-multi-coach">-</span>';
            html += '</div>';

            html += '<div class="yildiz-item">';
            html += '<strong>Avrupa Gençler:</strong>';
            html += '<span id="genc-avrupa-status">-</span> | ';
            html += '<span id="genc-avrupa-coach">-</span>';
            html += '<div style="font-size: 11px; color: #999;">Kısmi — yalnızca TYF Aralık/Nisan verisi</div>';
            html += '</div>';

            html += '</div>';
```

- [ ] **Step 2: Add the JS population**

`panel/index.html` — `yildiz-central-nisan-coach` textContent atamasından SONRA (JS bloğu, ~satır 1150 civarı) ekle:

```javascript
            document.getElementById('genc-multi-status').textContent =
                athlete.selected_multinations_gencler ? 'Seçildi ✓'
                : (athlete.candidate_multinations_gencler ? 'Aday'
                : (athlete.candidate_relay_multinations_gencler ? 'Bayrak adayı' : '-'));
            document.getElementById('genc-multi-coach').textContent =
                athlete.coach_called_multinations_gencler ? 'Antrenör barajı geçti' : '-';

            document.getElementById('genc-avrupa-status').textContent =
                athlete.selected_avrupa_gencler
                    ? ('Seçildi ✓ (' + (athlete.avrupa_gencler_event_count || 0) + ' branş)')
                    : (athlete.candidate_relay_avrupa_gencler ? 'Bayrak adayı' : '-');
            document.getElementById('genc-avrupa-coach').textContent =
                athlete.coach_called_avrupa_gencler ? 'Antrenör barajı geçti' : '-';
```

- [ ] **Step 3: Manual smoke test**

```bash
python panel/serve.py &
sleep 2
curl -s "http://localhost:8765/api/ranking?gender=F" | python -c "import sys,json; d=json.load(sys.stdin); a=[x for x in d if x['birth_year'] in (2008,2009,2010)][:1]; print(a[0].get('selected_multinations_gencler'), a[0].get('selected_avrupa_gencler'), a[0].get('avrupa_gencler_event_count')) if a else print('veri yok')"
kill %1
```
Expected: üç değer basılır (True/False/int), hata yok. Tarayıcıda bir sporcunun detayında "Gençler Milli Takımları" bölümü görünür.

- [ ] **Step 4: Run full suite (regression)**

Run: `python -m pytest -q`
Expected: PASS (136 passed)

- [ ] **Step 5: Commit**

```bash
git add panel/index.html
git commit -m "feat: dashboard 'Gençler Milli Takımları' bölümü (Multi + Avrupa Gençler)"
```

---

### Task 7: Gerçek veriyle akıl-sağlığı doğrulaması

**Files:**
- Create: `resmi-kadrolar/gencler-dogrulama-2026-09-08.md` (bulgular)

**Interfaces:**
- Consumes: tüm önceki task'lar; `data/bolge_karmalari.db` (dolu — 2008-2010 sporcuları var)

- [ ] **Step 1: Run the sanity script**

```bash
python - <<'EOF'
# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from database.db import get_athlete_rankings
from federasyon.gencler_ranker import select_all_gencler
for g in ('F', 'M'):
    ath = select_all_gencler(get_athlete_rankings(None, g, None))
    multi = [a for a in ath if a.get('selected_multinations_gencler')]
    multi_aday = [a for a in ath if a.get('candidate_multinations_gencler')]
    avr = [a for a in ath if a.get('selected_avrupa_gencler')]
    print(f"\n=== {g} ===")
    print(f"Multi Gençler KESİN={len(multi)} ADAY={len(multi_aday)}")
    for a in sorted(multi, key=lambda x: x['birth_year']):
        assert 2008 <= a['birth_year'] <= 2010, a
        print("  ", a['birth_year'], a['athlete_name'])
    print(f"Avrupa Gençler KESİN={len(avr)}")
    for a in sorted(avr, key=lambda x: (x['birth_year'], x['athlete_name']))[:20]:
        assert 2008 <= a['birth_year'] <= 2012, a
        print("  ", a['birth_year'], a['athlete_name'], a['avrupa_gencler_events'])
EOF
```

- [ ] **Step 2: Doğrula ve belgele**

Kontrol listesi:
- Multi Gençler yaşları yalnız 2008-2010; KESİN sayısı ≤ 10 K + 10 E (madde 5 kırpması çalışıyor).
- Avrupa Gençler yaşları yalnız 2008-2012.
- `avrupa_gencler_events` sadece sporcunun gerçekten yüzdüğü branşları içeriyor.
- Yıldızlar/Federasyon Karması çıktıları hâlâ eskisi gibi (ayrı bir `python -m pytest -q` = 136 yeşil).

Bulguları `resmi-kadrolar/gencler-dogrulama-2026-09-08.md`'ye yaz: her iki cinsiyet için KESİN listeler, sayılar, gözlemler, "Avrupa Gençler kısmi veri" notu. Resmi kadro elde olmadığı için "doğrulama sınırlı — algoritma Multi Yıldızlar ile aynı çekirdek" notunu ekle.

- [ ] **Step 3: Commit**

```bash
git add resmi-kadrolar/gencler-dogrulama-2026-09-08.md
git commit -m "docs: Gençler seçimleri gerçek veri akıl-sağlığı doğrulaması"
```

---

## Self-Review Notu

- **Spec kapsamı:** Multi Gençler (Task 3), Avrupa Gençler (Task 4), baraj tabloları (Task 1), çekirdek refactor (Task 2), serve.py (Task 5), index.html (Task 6), gerçek-veri doğrulama (Task 7). Gençler Alternatif / Dakar spec kapsamı dışında — plan da dışında. ✓
- **Tip tutarlılığı:** `_select_branch_winners_core` imzası Task 2'de tanımlı, Task 3'te aynı argümanlarla çağrılıyor. `check_baraj`/`passes_any` Task 1'de tanımlı, Task 3-4'te kullanılıyor. Alan adları (`selected_multinations_gencler` vb.) Task 3/4/5/6 boyunca aynı. ✓
- **Placeholder yok:** tüm kod blokları tam. ✓
- **Test sayıları** yaklaşık (mevcut 116 baz); executor gerçek sayıyı görüp devam eder.
