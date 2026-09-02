# Yıldızlar Milli Takım Seçme Sistemi — Design Spec

> **For agentic workers:** REQUIRED SKILL: Use superpowers:subagent-driven-development for implementation

**Goal:** Implement three additional youth national team selections (Multinations Stars, Comen Cup, Central European Countries Meet) alongside existing federation-based selections, allowing athletes to qualify for multiple competitions simultaneously.

**Architecture:** Extend current selection system with three parallel yıldızlar (youth) selection modules, each with distinct criteria, age groups, and selection dates. Athletes can qualify for multiple yıldızlar competitions if they meet respective criteria. Maintain separation between federation rankings (TR/BÖLGE/MULTINATIONS) and yıldızlar rankings.

**Tech Stack:** Python (backend), SQLite (database), JavaScript (frontend)

**Spec:** This document

---

## Global Constraints

All selections target age groups 2013–2011 (13–15 age), with exception noted per competition. Selection dates are fixed per competition. Athlete points display in frontend but do not affect federation quota placement (karma). Antrenor (coach) invitations tied to performance thresholds (baraj) only.

---

## Current System (Federation Selections)

**Status:** Working correctly ✓

- **Selection Type:** TR, BÖLGE, MULTINATIONS (fed karmaları)
- **Cascade Rule:** MULTINATIONS → can't enter BÖLGE/TR; BÖLGE → can't enter TR
- **Ranking:** Points-based + cascade (lower athlete moves up)
- **Points Display:** Shown in athlete profile
- **Antrenor:** Not currently tracked for fed karmaları

---

## New: Yıldızlar (Youth) Selections

Three new selection competitions, each independent but with athlete overlap.

### 1. MULTINATIONS YILDIZLAR (Yunuslar)

**Event Details:**
- Event Date: 28–29 March 2026 (Graz, Austria)
- Age Groups: 2013–2012–2011 (Female & Male)
- Selection Qualifier: 20–22 December 2025 (single date)

**Selection Criteria:**

1. Selection is **ranking-based + points**, similar to federation selections (fed karmaları logic)
2. Each stroke/distance: top finishers selected (1st place athletes form initial cadre)
3. **Cadre Size:** 10 Female + 10 Male
4. **Points Display:** Yes, visible in athlete profile — **but does NOT qualify for federation quota slots** (karma kadrolarına giremez)
5. **Qualification:** Athlete selected if qualifies; points shown for informational ranking only

**Antrenor Recruitment:**

- Coach threshold: Fixed performance times per stroke/distance (antrenör barajları table)
- Coaches of selected athletes who **pass the performance threshold** are invited
- Invitation text: "Antrenör barajı geçti" (Coach threshold passed)
- Coaches selected: Top 6 athletes closest to Olympic standard (olimpiyat barajlarına yüzdelik olarak en yakın 6)

**Multi-Selection Rule:**

- If athlete selected for MULTINATIONS → **can also qualify for Comen Cup AND Central European** (no exclusion)

---

### 2. COMEN CUP YILDIZLAR

**Event Details:**
- Event Date: June 2026 (Belgrade, Serbia)
- Age Groups: 
  - Female: 2013–2012–2011
  - Male: 2012–2011–2010 (note: includes 2010 male athletes)
- Selection Qualifiers: 20–22 December 2025 AND 17–19 April 2026 (two selection dates)

**Selection Criteria:**

1. Selection is **ranking-based**, evaluated across both December and April competitions
2. Rankings determined by best time/performance across both dates (overall best performance)
3. Same athlete may place different (1st vs 2nd) in December vs April; ranking uses overall evaluation
4. Cadre size: Determined by competition format (not fixed quota like Multinations)
5. Max 4 individual events per athlete
6. Tiebreaker: If same ranking, secondary events (other strokes/distances) used to break tie
7. **Antrenor per selection date:** 6 coaches per date (December 6 + April 6 = up to 12 total coaches)

**Antrenor Recruitment:**

- Coach threshold: Fixed performance times (antrenör barajları table — same as Multinations)
- Coaches of selected athletes in each date who **pass the performance threshold** are invited
- Invitation text: "Antrenör barajı geçti" (Coach threshold passed)
- December coaches: Top 6 of December qualifiers
- April coaches: Top 6 of April qualifiers

**Multi-Selection Rules:**

- If athlete selected for MULTINATIONS → **can also qualify for Comen Cup** ✓
- If athlete selected for Comen Cup → **can also qualify for Central European** ✓

---

### 3. CENTRAL EUROPEAN COUNTRIES MEET YILDIZLAR

**Event Details:**
- Event Date: 17–19 July 2026 (Slovenia)
- Age Groups: 2013–2012–2011 (Female & Male)
- Selection Qualifiers: 20–22 December 2025 AND 17–19 April 2026 (two selection dates)
- Cadre Size: 12 Female + 12 Male (fixed quota)

**Selection Criteria:**

1. Selection is **ranking-based + cadre quota**, evaluated across both December and April competitions
2. Rankings by best overall performance (same logic as Comen Cup)
3. Cadre selection: Top 12F + 12M selected per date
4. Tiebreaker: If same ranking, secondary events used
5. **Antrenor per selection date:** 6 coaches per date (December 6 + April 6 = up to 12 total coaches)

**Antrenor Recruitment:**

- Coach threshold: Fixed performance times (antrenör barajları table)
- Coaches of selected athletes who **pass the performance threshold** are invited
- Invitation text: "Antrenör barajı geçti"
- December coaches: Top 6 of December qualifiers
- April coaches: Top 6 of April qualifiers

**Multi-Selection Rules:**

- If athlete selected for MULTINATIONS OR Comen Cup (or both) → **can also qualify for Central European** ✓
- No exclusion rules; athlete can be in all three simultaneously

---

## Database Schema Changes

**Table:** `athletes` (extend)

New columns:
```sql
-- MULTINATIONS Yıldızlar Selection
selected_yildiz_multinations BOOLEAN DEFAULT FALSE
coach_called_yildiz_multinations BOOLEAN DEFAULT FALSE

-- COMEN CUP Yıldızlar Selection
selected_yildiz_comen_cup_aralik BOOLEAN DEFAULT FALSE
selected_yildiz_comen_cup_nisan BOOLEAN DEFAULT FALSE
coach_called_yildiz_comen_cup_aralik BOOLEAN DEFAULT FALSE
coach_called_yildiz_comen_cup_nisan BOOLEAN DEFAULT FALSE

-- CENTRAL EUROPEAN Yıldızlar Selection
selected_yildiz_central_europe_aralik BOOLEAN DEFAULT FALSE
selected_yildiz_central_europe_nisan BOOLEAN DEFAULT FALSE
coach_called_yildiz_central_europe_aralik BOOLEAN DEFAULT FALSE
coach_called_yildiz_central_europe_nisan BOOLEAN DEFAULT FALSE
```

**Rationale:** Each selection date tracked separately for Comen Cup and Central European (December + April). MULTINATIONS has single date (December only). Boolean flags allow filtering, querying, and independent tracking of coach invitations.

---

## File Structure

```
federasyon/
├── fed_karmalari.py                          (existing, federation selections)
├── yildizlar_multinations_barajlari.py       (new: performance thresholds)
├── yildizlar_comen_cup_barajlari.py          (new: performance thresholds)
├── yildizlar_central_europe_barajlari.py     (new: performance thresholds)
├── ranker.py                                  (existing, orchestrates fed selections)
└── yildizlar_ranker.py                       (new: orchestrates all yıldızlar)
```

**Separation:** Federation selections remain in `ranker.py` (untouched). Yıldızlar selections handled in separate `yildizlar_ranker.py` module with three selection functions.

---

## Selection Algorithm Flow

### Main Orchestration (ranker.py calls yildizlar_ranker functions)

```
select_all_yildizlar(athletes):
  1. check_yildizlar_multinations(athletes, selection_date="2025-12-22")
  2. check_yildizlar_comen_cup(athletes, selection_date_1="2025-12-22", selection_date_2="2026-04-19")
  3. check_yildizlar_central_europe(athletes, selection_date_1="2025-12-22", selection_date_2="2026-04-19")
```

### Per-Selection Function Logic

**Multinations:**
1. Filter athletes by age group (2013–2011)
2. Filter by event (stroke, distance)
3. Rank by points (descending)
4. Select top 10F + 10M
5. Mark `selected_yildiz_multinations = TRUE`
6. Check antrenor threshold → if passed, mark `coach_called_yildiz_multinations = TRUE`
7. Display points in frontend ✓ (but exclude from federation quota logic)

**Comen Cup (per date: December or April):**
1. Filter athletes by age group (2013–2011 Female, 2012–2010 Male)
2. Evaluate across all strokes/distances
3. Rank by overall performance (best time across both dates if evaluating combined)
4. Select qualifying athletes per cadre rules
5. Max 4 events per athlete
6. Tiebreaker: secondary event performance
7. Mark `selected_yildiz_comen_cup_aralik` or `selected_yildiz_comen_cup_nisan = TRUE`
8. Check antrenor threshold → if passed, mark corresponding `coach_called_*`
9. Do **NOT** exclude based on Multinations selection (athlete can be in both)

**Central European (per date: December or April):**
1. Filter athletes by age group (2013–2011)
2. Evaluate across all strokes/distances
3. Rank by overall performance
4. Select top 12F + 12M per date
5. Tiebreaker: secondary event performance
6. Mark `selected_yildiz_central_europe_aralik` or `selected_yildiz_central_europe_nisan = TRUE`
7. Check antrenor threshold → if passed, mark corresponding `coach_called_*`
8. Do **NOT** exclude based on Multinations or Comen Cup selection (athlete can be in any/all)

---

## Frontend Display — Athlete Profile

**Section: Yıldızlar Selections**

```
YILDIZLAR (Youth National Teams):

Multinations Yıldızlar:
  Status: Seçildi ✓
  Points: 245 (ranking info only — not federation quota)
  Antrenör: Barajı geçti ✓

Comen Cup Yıldızlar:
  Aralık (December): Seçildi ✓ | Antrenör: Barajı geçti ✓
  Nisan (April): Seçilmedi ✗ | Antrenör: —

Central European Countries Meet Yıldızlar:
  Aralık (December): Seçildi ✓ | Antrenör: Barajı geçemedi ✗
  Nisan (April): Seçildi ✓ | Antrenör: Barajı geçti ✓
```

**Points Display:** Yes, visible for ranking purposes. **Does NOT affect federation quota slots** (karma kadrolarına giremez).

**No Cascade Rule for Yıldızlar:** Unlike federation selections (TR → BÖLGE → MULTINATIONS cascade), yıldızlar selections are independent. Athlete can appear in none, one, or all three competitions.

---

## Baraj (Performance Threshold) Tables

Each yıldızlar module contains antrenor barajları (coach invitation thresholds):

**File:** `yildizlar_multinations_barajlari.py`
```python
ANTRENOR_BARAJLARI = {
    "50m Freestyle": {"M": "00:23.41", "F": "00:26.34"},
    "100m Freestyle": {"M": "00:51.53", "F": "00:57.33"},
    # ... all strokes/distances
}
```

Same structure for Comen Cup and Central European (may differ from Multinations in future).

---

## Testing Checklist

- [ ] Athlete qualifies for Multinations only
- [ ] Athlete qualifies for Multinations + Comen Cup (December)
- [ ] Athlete qualifies for Comen Cup (April only, not December)
- [ ] Athlete qualifies for all three (different dates)
- [ ] Antrenor threshold: passes → coach invited; fails → coach not invited
- [ ] Frontend displays selections correctly per date
- [ ] Points shown but do not affect federation quota
- [ ] Age group filtering works (2010 male excluded from Multinations/Central, included in Comen Cup)
- [ ] Database schema migrations applied
- [ ] No regression in existing federation selection logic

---

## Acceptance Criteria

✓ Three yıldızlar selection modules implemented independently  
✓ Athletes can qualify for multiple competitions simultaneously  
✓ Antrenor invitations based on performance threshold (baraj)  
✓ Age groups per competition enforced (especially 2010 male in Comen Cup only)  
✓ Selection dates tracked separately (December/April)  
✓ Points displayed; federation quota logic unchanged  
✓ Database schema extended without breaking existing data  
✓ All existing fed karma selections continue working  
✓ Frontend displays all selection statuses clearly  

---

**Status:** Ready for implementation planning

**Next Step:** Invoke writing-plans skill for detailed task breakdown
