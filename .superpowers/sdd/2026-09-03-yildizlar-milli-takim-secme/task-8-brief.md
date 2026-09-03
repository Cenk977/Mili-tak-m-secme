# Task 8: Integration Test

**Files:**
- Test: Manual + API test script (no new files created; use existing test data)

**Interfaces:**
- **Consumes:** Full system (database from Task 1, baraj tables from Tasks 2–4, ranker from Task 5, API from Task 6, frontend from Task 7)
- **Produces:** Verified end-to-end yíldízlar selection flow with no regressions

**Steps:**

- [ ] **Step 1: Clear database and restart server**

```bash
rm database/athletes.db
python panel/serve.py &
```

Wait a few seconds for server to start.

- [ ] **Step 2: Upload test LXF file**

```bash
curl -X POST -F "file=@data/antalya_millitakim_secme_sonuc.lxf" \
  http://localhost:8765/upload
```

Expected: HTTP 200, "Athletes parsed" message

Wait 2 seconds for processing.

- [ ] **Step 3: Query API for 2012 male athlete (should have yíldízlar fields)**

```bash
curl "http://localhost:8765/api/ranking?birth_year=2012&gender=M" | \
  python -c "import sys, json; data = json.load(sys.stdin); \
  athlete = data[0] if data else None; \
  if athlete: \
    print(f'Athlete: {athlete[\"athlete_name\"]}'); \
    print(f'Multinations: {athlete.get(\"selected_yildiz_multinations\")}'); \
    print(f'Comen Cup Aralık: {athlete.get(\"selected_yildiz_comen_cup_aralik\")}'); \
    print(f'Central Europe Aralık: {athlete.get(\"selected_yildiz_central_europe_aralik\")}') \
  else: \
    print('No athletes found')"
```

Expected: Output shows athlete name and selection status (True/False)

- [ ] **Step 4: Check antrenor flags**

```bash
curl "http://localhost:8765/api/ranking?birth_year=2012&gender=M" | \
  python -c "import sys, json; data = json.load(sys.stdin); \
  athlete = data[0] if data else None; \
  if athlete: \
    print(f'Coach Multinations: {athlete.get(\"coach_called_yildiz_multinations\")}'); \
    print(f'Coach Comen Aralık: {athlete.get(\"coach_called_yildiz_comen_cup_aralik\")}'); \
    print(f'Coach Central Aralık: {athlete.get(\"coach_called_yildiz_central_europe_aralik\")}') \
  else: \
    print('No athletes found')"
```

Expected: Some athletes show True (passed baraj), some False

- [ ] **Step 5: Open browser and check athlete profile**

1. Open http://localhost:8765 in browser
2. Scroll through athlete list
3. Click on an athlete to view profile
4. Scroll down to "Yıldızlar Milli Takımları" section
5. Verify selections displayed correctly

Expected: 
- Section visible and styled
- Shows status for all three competitions
- Shows dates (Aralık/Nisan) where applicable

- [ ] **Step 6: Verify no federation selection regression**

In the same athlete profile, check that:
- Federation selections (TR/BÖLGE/MULTINATIONS) still show
- Federation and yíldízlar sections are separate
- No data loss from existing system

Expected: Both sections present, clean separation

- [ ] **Step 7: Test age group boundaries**

Query 2010 male (should be eligible for Comen Cup only, NOT Multinations/Central):

```bash
curl "http://localhost:8765/api/ranking?birth_year=2010&gender=M" | \
  python -c "import sys, json; data = json.load(sys.stdin); \
  athlete = data[0] if data else None; \
  if athlete: \
    print(f'2010 Male:'); \
    print(f'  Multinations: {athlete.get(\"selected_yildiz_multinations\")} (should be False)'); \
    print(f'  Comen Cup Aralık: {athlete.get(\"selected_yildiz_comen_cup_aralik\")} (should be True)'); \
    print(f'  Central Europe Aralık: {athlete.get(\"selected_yildiz_central_europe_aralik\")} (should be False)') \
  else: \
    print('2010 athletes filtered out (expected for 2010)')"
```

Expected: 
- 2010 male NOT in Multinations or Central Europe
- 2010 male included in Comen Cup (and possibly selected based on ranking)

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

Expected: Clean commit with all changes staged and committed
