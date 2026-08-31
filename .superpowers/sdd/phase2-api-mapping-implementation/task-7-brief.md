# Task 7: Integration Test

**Objective:**
Run the complete system end-to-end with real LXF files to verify all components work together correctly. This is a manual testing task, not code implementation.

**Prerequisites:**
- Tasks 1-6 complete (database, config, mapping, parser, HTTP server, dashboard)
- LXF test files available: `data/antalya_millitakim_secme_sonuc.lxf` and `data/edirne_millitakim_secme_sonuc.lxf`

## Step 1: Start the HTTP server

Run:
```bash
cd "C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme"
python panel/serve.py
```

Expected:
```
============================================================
Milli Takım Seçme — Dashboard
============================================================
Server running: http://localhost:8765
Database: data/selection.db
Press Ctrl+C to stop
============================================================
```

## Step 2: Open dashboard in browser

Open browser to http://localhost:8765/

Expected:
- Dashboard loads with title "Milli Takım Seçme 2026"
- Upload area visible with drag-and-drop UI
- Filter controls (birth year, gender) visible
- Empty state shown initially ("Yarışma sonuç dosyası yükleme işlemini başlayın")

## Step 3: Test file upload (Antalya)

Drag `data/antalya_millitakim_secme_sonuc.lxf` to the upload area or click to select.

Expected:
- Status message shows "Dosya yükleniyor..."
- File processes (may take 5-10 seconds)
- Success message: "✓ Başarılı! 763 sporcu yüklendi"
- Results table populates with athletes
- Statistics cards show: "763 Toplam Sporcu"
- Region badges visible with colors (Bölge 1-6)
- Selection badges visible (TR, B1, Bölge) where applicable

## Step 4: Test filters

### Filter by Birth Year
- Enter "2005" in birth year input
- Click "Filtrele"
- Expected: Table updates to show only athletes born in 2005

### Filter by Gender
- Select "Erkek" (Male) in gender dropdown
- Leave birth year empty
- Click "Filtrele"
- Expected: Table updates to show only male athletes

### Filter by Both
- Enter "2006" in birth year
- Select "Kız" (Female) in gender
- Click "Filtrele"
- Expected: Table shows only female athletes born in 2006

## Step 5: Test /api/ranking endpoint directly

Open browser console and run:
```javascript
fetch('/api/ranking?birth_year=2005&gender=M')
  .then(r => r.json())
  .then(data => console.log(`Found ${data.length} athletes`))
```

Expected:
- API returns JSON array of athletes
- Each athlete has: firstname, lastname, city, region, birth_year, gender, best_score, selected, selection_type

## Step 6: Test database clear

Click "Veritabanını Temizle" (Clear Database) button.

Expected:
- Confirmation dialog: "Veritabanındaki tüm veriler silinecek. Emin misiniz?"
- Click OK
- Success message: "✓ Veritabanı temizlendi"
- Table shows empty state again
- Statistics disappear

## Step 7: Upload second file (Edirne)

Upload `data/edirne_millitakim_secme_sonuc.lxf`

Expected:
- File processes
- Success message with athlete count
- Table populates with Edirne athletes
- Statistics cards update with new counts

## Step 8: Verify data integrity

In browser console, run:
```javascript
fetch('/api/ranking')
  .then(r => r.json())
  .then(data => {
    const cities = new Set(data.map(a => a.city));
    const regions = new Set(data.map(a => a.region));
    console.log(`Cities: ${Array.from(cities).join(', ')}`);
    console.log(`Regions: ${Array.from(regions).join(', ')}`);
    console.log(`Athletes with Unknown city: ${data.filter(a => a.city === 'Unknown').length}`);
  })
```

Expected:
- Multiple cities from Excel mapping (not all 'Unknown')
- Regions 1-6 represented (not all 0)
- Turkish character support verified (city names like İzmir, Ankara, etc.)

## Step 9: Verification checklist

Check all of the following:

- [ ] Server starts without errors
- [ ] Dashboard loads at http://localhost:8765/
- [ ] File upload works (drag-and-drop and click)
- [ ] Upload success message displays athlete count
- [ ] Results table displays correctly with all 8 columns
- [ ] Region badges show colors for regions 1-6
- [ ] Selection badges show correct values (TR, B1, Bölge)
- [ ] Birth year filter works (updates table)
- [ ] Gender filter works (updates table)
- [ ] Combined filters work (both parameters sent to API)
- [ ] API endpoint returns proper JSON with all fields
- [ ] Database clear works (table becomes empty)
- [ ] Second file upload works
- [ ] City/region mapping populated (not all 'Unknown' or 0)
- [ ] Turkish characters display correctly

## Step 10: Performance check

Time how long it takes to:
1. Upload first file: _____ seconds
2. Query /api/ranking with filters: _____ seconds
3. Clear database: _____ seconds

Expected: All operations complete within 10 seconds

## Report

Write a complete report to: `.superpowers/sdd/phase2-api-mapping-implementation/task-7-report.md`

Include:
- Status: DONE or BLOCKED
- Summary of test results
- Checklist items that passed/failed
- Any errors encountered
- Performance metrics
- Concerns or issues found

If all items in the verification checklist pass, mark as DONE. If any fail, describe the issue and mark as BLOCKED.
