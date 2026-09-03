# Task 5: Create Yildizlar Ranking Engine

**Files:**
- Create: `federasyon/yildizlar_ranker.py`

**Interfaces:**
- **Consumes:** 
  - `athletes` list (from database) with columns added in Task 1
  - baraj modules from Tasks 2–4: `check_antrenor_baraj` functions
- **Produces:** 
  - Updated `athletes` list with all 10 yíldízlar selection/coach flags populated
  - `select_all_yildizlar(athletes)` → athletes (main orchestration function)

**Key Logic:**

- **Multinations:** Top 10F + 10M from 2013–2011, ranked by combined_top3 points
- **Comen Cup (Aralık + Nisan):** All eligible ranked athletes; 2013–2011 F, 2012–2010 M
- **Central European (Aralık + Nisan):** Top 12F + 12M from 2013–2011

- **Coach invitation:** For each selected athlete, check if ANY of their events passes performance baraj. If yes, set coach flag to True.

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

- [ ] **Step 2: Implement `select_yildizlar_multinations(athletes)`**

```python
def select_yildizlar_multinations(athletes):
    """
    Select Multinations Yíldízlar cadre (10F + 10M).
    Age: 2013–2011
    Ranking: Points-based (highest combined_top3 selected)
    Returns: Updated athletes list
    """
    eligible = [a for a in athletes if 2011 <= a.get('birth_year') <= 2013]
    
    females = [a for a in eligible if a.get('gender') == 'F']
    males = [a for a in eligible if a.get('gender') == 'M']
    
    females_sorted = sorted(females, key=lambda x: x.get('combined_top3', 0), reverse=True)
    males_sorted = sorted(males, key=lambda x: x.get('combined_top3', 0), reverse=True)
    
    selected_females = females_sorted[:10]
    selected_males = males_sorted[:10]
    selected_ids = {a.get('athlete_id') for a in selected_females + selected_males}
    
    for athlete in athletes:
        if athlete.get('athlete_id') in selected_ids:
            athlete['selected_yildiz_multinations'] = True
            
            # Check if ANY event passes baraj
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

- [ ] **Step 3: Implement `select_yildizlar_comen_cup_aralik(athletes)`**

```python
def select_yildizlar_comen_cup_aralik(athletes):
    """
    Comen Cup December selection (20-22 Aralık 2025).
    Age: 2013–2011 F, 2012–2010 M
    Ranking: Points-based
    """
    eligible = [
        a for a in athletes
        if (a.get('gender') == 'F' and 2011 <= a.get('birth_year') <= 2013) or
           (a.get('gender') == 'M' and 2010 <= a.get('birth_year') <= 2012)
    ]
    
    eligible_sorted = sorted(eligible, key=lambda x: x.get('combined_top3', 0), reverse=True)
    
    for athlete in eligible_sorted:
        athlete['selected_yildiz_comen_cup_aralik'] = True
        
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

- [ ] **Step 4: Implement `select_yildizlar_comen_cup_nisan(athletes)`**

Same logic as Step 3 but with _nisan flags instead of _aralik.

- [ ] **Step 5: Implement `select_yildizlar_central_europe_aralik(athletes)`**

```python
def select_yildizlar_central_europe_aralik(athletes):
    """
    Central European December selection (20-22 Aralık 2025).
    Age: 2013–2011 (both genders)
    Cadre: Top 12F + 12M
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
```

- [ ] **Step 6: Implement `select_yildizlar_central_europe_nisan(athletes)`**

Same logic as Step 5 but with _nisan flags.

- [ ] **Step 7: Implement orchestration function**

```python
def select_all_yildizlar(athletes):
    """Apply all yíldízlar selections to athletes list."""
    athletes = select_yildizlar_multinations(athletes)
    athletes = select_yildizlar_comen_cup_aralik(athletes)
    athletes = select_yildizlar_comen_cup_nisan(athletes)
    athletes = select_yildizlar_central_europe_aralik(athletes)
    athletes = select_yildizlar_central_europe_nisan(athletes)
    
    logger.info(f"Yíldízlar selection complete: {len(athletes)} athletes processed")
    return athletes
```

- [ ] **Step 8: Test**

```python
if __name__ == "__main__":
    test_athlete = {
        'athlete_id': 1,
        'athlete_name': 'Test',
        'birth_year': 2012,
        'gender': 'M',
        'combined_top3': 100,
        'combined_events': {('Freestyle', 50): 100},
        'combined_events_time': {('Freestyle', 50): '00:23.40'}
    }
    result = select_all_yildizlar([test_athlete])
    assert result[0]['selected_yildiz_multinations'] == True
    print("✓ Test pass")
```

Run: `python federasyon/yildizlar_ranker.py`

Expected: ✓ Test pass

- [ ] **Step 9: Commit**

```bash
git add federasyon/yildizlar_ranker.py
git commit -m "feat: implement yildizlar ranking engine for three youth competitions"
```
