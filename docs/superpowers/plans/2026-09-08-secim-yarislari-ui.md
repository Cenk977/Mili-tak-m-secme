# Seçim Yarışları Gösterimi + Gençler Liste Rozetleri — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Detay panelinde yarış tablosuna "bu yarışta seçildi" rozeti + liste satırına Gençler (Multi/Avrupa) rozetleri; her ikisi additive.

**Architecture:** Backend, seçim fonksiyonlarının zaten hesapladığı "branş birinciliği event'leri"ni sporcu dict'ine public alan olarak yazar; `serve.py` bunları `/api/ranking` yanıtına ekler; `panel/index.html` yarış tablosunda ve liste satırında gösterir. Seçim SONUÇLARI (kim seçildi) değişmez.

**Tech Stack:** Python 3 stdlib, pytest, düz HTML/JS.

**Spec:** `docs/superpowers/specs/2026-09-08-secim-yarislari-ui-design.md`

## Global Constraints

- UTF-8; Türkçe branş adları (Serbest/Sırtüstü/Kurbağalama/Kelebek/Karışık).
- Additive: hiçbir seçim sonucu / mevcut alan değişmez. Mevcut suite (138) her task sonunda yeşil.
- Yeni `*_events` alanları yalnız ilgili müsabakaya seçili/aday sporcuda dolu; diğerlerinde `[]`.
- Event biçimi backend'de `(stroke, distance)` tuple; API'de `[stroke, distance]` liste.
- Frontend: leg filtresine bağlama YOK (Gençler seçimi leg'e göre değişmez).
- Sık commit.

---

### Task 1: Backend — `*_events` alanlarını sporcu dict'ine yaz

**Files:**
- Modify: `federasyon/yildizlar_ranker.py` (`_select_branch_winners_core` ~298; `select_yildizlar_multinations` ~332; `select_yildizlar_comen_cup_aralik` ~412; `_nisan` ~482; `select_yildizlar_central_europe_aralik` ~542; `_nisan` ~623)
- Modify: `federasyon/gencler_ranker.py` (`select_multinations_gencler`)
- Test: `federasyon/tests/test_secim_events_exposed.py` (yeni), `federasyon/tests/test_yildizlar_ranker_core.py` (ekleme)

**Interfaces:**
- Consumes: `_compute_group_stats` sonucundaki `first_events: list[(stroke,distance)]`
- Produces: sporcu dict'lerinde `multinations_events`, `multinations_gencler_events`, `comen_cup_events`, `central_europe_events` alanları (`list[tuple[str,int]]`; seçili değilse `[]`)

- [ ] **Step 1: Failing test — `federasyon/tests/test_secim_events_exposed.py`**

```python
# -*- coding: utf-8 -*-
"""Seçim fonksiyonları, karar veren branş-birinciliği yarışlarını public alana yazmalı."""
from federasyon.yildizlar_ranker import (
    select_yildizlar_multinations,
    select_yildizlar_comen_cup_aralik, select_yildizlar_comen_cup_nisan,
    select_yildizlar_central_europe_aralik, select_yildizlar_central_europe_nisan,
)
from federasyon.gencler_ranker import select_multinations_gencler


def _a(aid, gender, by, antalya=None, edirne=None):
    at = antalya or {}
    ed = edirne or {}
    combined = dict(at)
    for k, v in ed.items():
        combined[k] = v
    return {
        "athlete_id": aid, "athlete_name": aid, "gender": gender, "birth_year": by,
        "antalya_events_time": at, "edirne_events_time": ed,
        "combined_events_time": combined,
        "combined_events": {k: 1 for k in combined},
        "antalya_events": {k: 1 for k in at}, "edirne_events": {k: 1 for k in ed},
    }


def test_multinations_events_populated_for_winner_empty_for_loser():
    winner = _a("W", "M", 2012, antalya={("Serbest", 50): "00:00:24.00", ("Kelebek", 100): "00:00:55.00"})
    loser = _a("L", "M", 2012, antalya={("Serbest", 50): "00:00:30.00"})
    out = select_yildizlar_multinations([winner, loser])
    by = {a["athlete_id"]: a for a in out}
    assert set(by["W"]["multinations_events"]) == {("Serbest", 50), ("Kelebek", 100)}
    assert by["L"]["multinations_events"] == []


def test_multinations_events_only_swum_events():
    w = _a("W", "F", 2012, antalya={("Serbest", 50): "00:00:24.00"})
    out = select_yildizlar_multinations([w])
    ev = out[0]["multinations_events"]
    assert all(e in w["antalya_events"] for e in ev)


def test_multinations_gencler_events_populated():
    w = _a("W", "M", 2009, antalya={("Kurbağalama", 100): "00:01:05.00"})
    out = select_multinations_gencler([w])
    assert ("Kurbağalama", 100) in out[0]["multinations_gencler_events"]


def test_comen_events_union_of_aralik_and_nisan_wins():
    # Aralık'ta Serbest 50 birinci, Nisan'da Kelebek 100 birinci
    w = _a("W", "F", 2012,
           antalya={("Serbest", 50): "00:00:24.00"},
           edirne={("Kelebek", 100): "00:00:58.00"})
    other = _a("O", "F", 2012,
               antalya={("Serbest", 50): "00:00:40.00"},
               edirne={("Kelebek", 100): "00:01:30.00"})
    ath = [w, other]
    ath = select_yildizlar_comen_cup_aralik(ath)
    ath = select_yildizlar_comen_cup_nisan(ath)
    by = {a["athlete_id"]: a for a in ath}
    assert set(by["W"]["comen_cup_events"]) == {("Serbest", 50), ("Kelebek", 100)}
    assert by["O"]["comen_cup_events"] == []


def test_central_events_populated():
    w = _a("W", "M", 2012, antalya={("Sırtüstü", 200): "00:02:05.00"})
    o = _a("O", "M", 2012, antalya={("Sırtüstü", 200): "00:03:00.00"})
    ath = select_yildizlar_central_europe_aralik([w, o])
    ath = select_yildizlar_central_europe_nisan(ath)
    by = {a["athlete_id"]: a for a in ath}
    assert ("Sırtüstü", 200) in by["W"]["central_europe_events"]
    assert by["O"]["central_europe_events"] == []
```

- [ ] **Step 2: Run — expect fail**

Run: `python -m pytest federasyon/tests/test_secim_events_exposed.py -q`
Expected: FAIL — `KeyError: 'multinations_events'` (alan yok)

- [ ] **Step 3: Implement**

**3a. `_select_branch_winners_core`** (`federasyon/yildizlar_ranker.py`): stats döngüsünde `_first/_second/_third` atamalarının yanına ekle:

```python
            a['_first_events'] = list(s.get('first_events', []))
```

**3b. `select_yildizlar_multinations`**: `for athlete in athletes:` döngüsünde, `if aid in sel_ids:` / `elif aid in cand_ids:` dallarında `athlete['multinations_events'] = list(athlete.get('_first_events', []))`; `else` dalında `athlete['multinations_events'] = []`. Döngü sonundaki temp-key pop listesine `'_first_events'` ekle.

**3c. `select_multinations_gencler`** (`federasyon/gencler_ranker.py`): aynı desen, alan adı `multinations_gencler_events`; pop listesine `'_first_events'` ekle.

**3d. `select_yildizlar_comen_cup_aralik`**: `for athlete in athletes:` döngüsünde `if athlete['athlete_id'] in sel_ids:` dalında:

```python
            athlete['comen_cup_events'] = sorted(
                set(athlete.get('comen_cup_events', [])) | set(athlete.get('_first_events', []))
            )
```

`else` dalında: `athlete.setdefault('comen_cup_events', [])` (Nisan'ın yazdığını silme — sadece hiç yoksa `[]`). Mevcut `for k in ['_first_events', '_first_count']:` pop'u KALIR (artık public alana kopyalandıktan sonra).

**3e. `select_yildizlar_comen_cup_nisan`**: 3d ile aynı (aynı `comen_cup_events` alanına ekler — birleşim).

**3f. `select_yildizlar_central_europe_aralik` ve `_nisan`**: 3d/3e ile aynı, alan adı `central_europe_events`.

> Sıra notu: `select_all_yildizlar` bu fonksiyonları aralik→nisan sırasıyla çağırıyor. Aralık `comen_cup_events`'i kurar, Nisan üstüne ekler. `else` dalı `setdefault` kullandığı için seçili-değil sporcu `[]` alır ve Nisan bunu bozmaz.

- [ ] **Step 4: `test_yildizlar_ranker_core.py`'ye ekle**

```python
def test_core_sets_first_events_on_winners():
    from federasyon.yildizlar_ranker import _select_branch_winners_core, YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM
    males = [
        {"athlete_id": "M1", "athlete_name": "M1", "gender": "M", "birth_year": 2012,
         "antalya_events_time": {("Serbest", 50): "00:00:25.00"}},
        {"athlete_id": "M2", "athlete_name": "M2", "gender": "M", "birth_year": 2012,
         "antalya_events_time": {("Serbest", 50): "00:00:26.00"}},
    ]
    _select_branch_winners_core(males, 10, "antalya_events_time",
                                YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM)
    assert ("Serbest", 50) in males[0]["_first_events"]
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest federasyon/tests/test_secim_events_exposed.py federasyon/tests/test_yildizlar_ranker_core.py federasyon/tests/test_yildizlar_multinations.py federasyon/tests/test_yildizlar_comen_cup.py federasyon/tests/test_yildizlar_central_europe.py federasyon/tests/test_gencler_multinations.py -q`
Expected: PASS (hepsi — seçim sonuçları değişmedi)

- [ ] **Step 6: Full suite**

Run: `python -m pytest -q`
Expected: PASS (138 + 6 yeni = 144)

- [ ] **Step 7: Commit**

```bash
git add federasyon/yildizlar_ranker.py federasyon/gencler_ranker.py federasyon/tests/test_secim_events_exposed.py federasyon/tests/test_yildizlar_ranker_core.py
git commit -m "feat: seçim fonksiyonları karar veren branş-birinciliği yarışlarını public alana yazsın"
```

---

### Task 2: Backend — `serve.py` `/api/ranking` yanıtına `*_events` ekle

**Files:**
- Modify: `panel/serve.py` (yanıt sözlüğü — `avrupa_gencler_event_count` satırının yanı)
- Test: `panel/test_serve_upload.py` (ekleme)

**Interfaces:**
- Consumes: Task 1'in yazdığı `multinations_events` / `comen_cup_events` / `central_europe_events` / `multinations_gencler_events` (+ mevcut `avrupa_gencler_events`)
- Produces: `/api/ranking` yanıtında 5 alan, biçim `[[stroke, distance], ...]`

- [ ] **Step 1: Failing test — `panel/test_serve_upload.py` sonuna**

```python
def test_api_ranking_serializes_secim_events():
    from federasyon.yildizlar_ranker import select_yildizlar_multinations
    ath = [{
        "athlete_id": "e1", "athlete_name": "E1", "gender": "M", "birth_year": 2012,
        "antalya_events_time": {("Serbest", 50): "00:00:24.00"},
        "antalya_events": {("Serbest", 50): 1},
        "combined_events": {("Serbest", 50): 1}, "combined_events_time": {("Serbest", 50): "00:00:24.00"},
    }]
    out = select_yildizlar_multinations(ath)
    # backend alanı tuple listesi
    assert out[0]["multinations_events"] == [("Serbest", 50)]
    # serve.py serileştirme kalıbı (list-of-list)
    serialized = [list(e) for e in out[0].get("multinations_events", [])]
    assert serialized == [["Serbest", 50]]
```

- [ ] **Step 2: Run — expect pass (saf birim testi; asıl kanıt Step 4)**

Run: `python -m pytest panel/test_serve_upload.py::test_api_ranking_serializes_secim_events -q`

- [ ] **Step 3: Implement**

`panel/serve.py` — `grep -n "avrupa_gencler_event_count" panel/serve.py` ile bulunan yanıt sözlüğü satırının hemen ardına ekle:

```python
                    'multinations_events': [list(e) for e in athlete.get('multinations_events', [])],
                    'comen_cup_events': [list(e) for e in athlete.get('comen_cup_events', [])],
                    'central_europe_events': [list(e) for e in athlete.get('central_europe_events', [])],
                    'multinations_gencler_events': [list(e) for e in athlete.get('multinations_gencler_events', [])],
                    'avrupa_gencler_events': [list(e) for e in athlete.get('avrupa_gencler_events', [])],
```

- [ ] **Step 4: Verify**

Run: `python -m pytest panel/test_serve_upload.py -q && python -c "import panel.serve"`
Expected: PASS + import OK

- [ ] **Step 5: Live smoke**

```bash
python panel/serve.py & sleep 3
curl -s "http://localhost:8765/api/ranking?gender=M" -o resp.json
python -c "import json,io,sys; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8'); d=json.load(open('resp.json',encoding='utf-8')); s=[a for a in d if a.get('multinations_events') or a.get('multinations_gencler_events') or a.get('avrupa_gencler_events')]; print(len(s),'sporcuda seçim yarışı var'); [print(a['athlete_name'], a.get('multinations_events'), a.get('multinations_gencler_events'), a.get('avrupa_gencler_events')) for a in s[:5]]"
rm -f resp.json; kill %1
```
Expected: seçili sporcularda `[["Serbest",50],...]` biçimli listeler basılır.

- [ ] **Step 6: Full suite + commit**

Run: `python -m pytest -q` → 145
```bash
git add panel/serve.py panel/test_serve_upload.py
git commit -m "feat: /api/ranking yanıtına seçim yarışları listeleri (*_events)"
```

---

### Task 3: Frontend — yarış tablosu rozetleri + liste satırı Gençler rozetleri

**Files:**
- Modify: `panel/index.html` (`renderEventsTable` ~1318; `showAthleteDetail` tablo çağrıları ~1350; `renderAthletes` badge-strip — 2 blok, grep `MULTI-ADAY`)

**Interfaces:**
- Consumes: Task 2'nin serileştirdiği `*_events` + mevcut `selected_multinations_gencler` / `candidate_multinations_gencler` / `selected_avrupa_gencler` / `candidate_relay_avrupa_gencler`
- Produces: görsel — kod testi yok

- [ ] **Step 1: `renderEventsTable` imzası + rozet**

`renderEventsTable(events, title)` → `renderEventsTable(events, title, eventBadges)`.
Satır döngüsünde derece `<td>`'sinin İÇİNE, `${race.time}` ifadesinden sonra:

```javascript
${(() => { const bs = (eventBadges && eventBadges[race.stroke + '|' + race.distance]) || []; return bs.map(b => `<span style="display:inline-block;margin-left:4px;background:#eef;border:1px solid #99c;color:#334;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:600;">🏅 ${b}</span>`).join(''); })()}
```

- [ ] **Step 2: `showAthleteDetail` — badgeMap kur ve tablolara geçir**

Tablo çağrılarından (`renderEventsTable(athlete.antalya_events, ...)`) hemen önce:

```javascript
            const badgeMap = {};
            const addBadges = (arr, label) => (arr || []).forEach(([s, d]) => { const k = s + '|' + d; (badgeMap[k] = badgeMap[k] || []).push(label); });
            addBadges(athlete.multinations_events, 'Multi');
            addBadges(athlete.comen_cup_events, 'Comen');
            addBadges(athlete.central_europe_events, 'Central');
            addBadges(athlete.multinations_gencler_events, 'Multi Gençler');
            addBadges(athlete.avrupa_gencler_events, 'Avrupa Gençler');
```

Sonra TÜM `renderEventsTable(...)` çağrılarına 3. argüman olarak `badgeMap` ekle (antalya, edirne, ve varsa combined — grep `renderEventsTable(` ile hepsini bul).

- [ ] **Step 3: `renderAthletes` — Gençler rozetleri (2 blok)**

`grep -n "MULTI-ADAY" panel/index.html` → 2 satır. Her ikisinde, `${federasyonKarmaSelected ? ...}` ifadesinden HEMEN ÖNCE ekle:

```javascript
${athlete.selected_multinations_gencler ? '<span style="display:inline-block;margin-left:4px;background:#ad1457;color:white;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:600;">MULTI-G</span>' : ''}${athlete.candidate_multinations_gencler ? '<span style="display:inline-block;margin-left:4px;background:transparent;color:#ad1457;border:1px solid #ad1457;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;" title="Madde 5 kota kırpması - aday">MULTI-G ADAY</span>' : ''}${athlete.selected_avrupa_gencler ? '<span style="display:inline-block;margin-left:4px;background:#00695c;color:white;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:600;">AVR-G</span>' : ''}${athlete.candidate_relay_avrupa_gencler && !athlete.selected_avrupa_gencler ? '<span style="display:inline-block;margin-left:4px;background:transparent;color:#00695c;border:1px dashed #00695c;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">AVR-G BAYRAK</span>' : ''}
```

- [ ] **Step 4: Statik kontrol + regresyon**

Run: `grep -n "eventBadges\|badgeMap\|MULTI-G\|AVR-G" panel/index.html && python -m pytest -q`
Expected: her iki blokta MULTI-G/AVR-G; `renderEventsTable` 3-arg; suite 145 (değişmez)

- [ ] **Step 5: Live smoke**

```bash
python panel/serve.py & sleep 3
echo "Tarayıcıda http://localhost:8765 — bir Multi Gençler sporcusunun (ör. Utku Ulucan) detayında: yarış tablosunda '🏅 Multi Gençler' rozetli satır(lar); liste satırında 'MULTI-G' rozeti."
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add panel/index.html
git commit -m "feat: yarış tablosunda seçim yarışı rozetleri + liste satırında Gençler rozetleri"
```

---

## Self-Review Notu

- Spec kapsamı: `*_events` backend (Task 1), serve.py (Task 2), frontend tablo+liste (Task 3). ✓
- Tip tutarlılığı: backend `(stroke,distance)` tuple → serve.py `[stroke,distance]` → frontend `[s,d]` destructuring. ✓
- Comen/Central `else` dalı `setdefault` — aralik/nisan sıralı çağrı güvenli. ✓
- Placeholder yok; tüm kod blokları tam. Test sayıları yaklaşık (138 baz).
