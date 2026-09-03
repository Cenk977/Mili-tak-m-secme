# Task 6: Update HTTP API Endpoint

**Files:**
- Modify: `panel/serve.py`

**Interfaces:**
- **Consumes:** Updated athletes list with yíldízlar flags from Task 5 (`select_all_yildizlar`)
- **Produces:** Extended `/api/ranking` endpoint JSON response including 10 new yíldízlar fields

**Steps:**

- [ ] **Step 1: Locate `/api/ranking` handler in `serve.py`**

Find the method that handles GET requests to `/api/ranking` (around line 520–640).

- [ ] **Step 2: Add import at top of serve.py**

```python
from federasyon.yildizlar_ranker import select_all_yildizlar
```

- [ ] **Step 3: Call yíldízlar selection before building response**

In the `/api/ranking` handler, before the response dict loop (around line 600), add:

```python
# Apply yíldízlar selections
athletes = select_all_yildizlar(athletes)
```

- [ ] **Step 4: Extend response dict with yíldízlar fields**

In the loop where you build the response (where you set athlete['selected'], athlete['selected_slot'], etc.), add these 10 fields after the existing fed karma fields:

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

Start the server and test with curl:

```bash
curl "http://localhost:8765/api/ranking?birth_year=2012&gender=M" | python -m json.tool | head -40
```

Expected: JSON response includes the 10 new yíldízlar fields (values may be False if test data doesn't trigger selections, but fields must be present)

- [ ] **Step 6: Commit**

```bash
git add panel/serve.py
git commit -m "api: extend /api/ranking endpoint with yildizlar selection fields"
```
