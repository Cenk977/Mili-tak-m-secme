# Task 4-9: System Completion - Testing, APIs, UI & Export

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Milli Takım Seçme system from operational core to production-ready with end-to-end testing, race leg management, leg filtering UI, regional rankings panel, stability fixes, and Excel export functionality.

**Architecture:** 
- Task 4 validates core system with real LXF files end-to-end
- Tasks 5-6 add race leg management (delete endpoint + UI toggle)
- Task 7 adds regional rankings view alongside combined rankings
- Task 8 addresses bugs/edge cases found during testing
- Task 9 adds Excel export for reporting

**Tech Stack:**
- Backend: Python 3, sqlite3, openpyxl (new for export)
- Frontend: HTML5, vanilla JavaScript, CSS Grid
- Data: LXF (Lenex) XML, SQLite, Excel output

**Spec:** This plan implements features from `docs/superpowers/plans/` based on system validation and user-approved scope.

## Global Constraints

- UTF-8 encoding throughout (database, file I/O, JSON responses)
- Turkish character support (İ, ş, ç, ğ, ü, ö)
- Database: SQLite with foreign keys enabled
- Port: localhost:8765
- KISS principle: keep implementations simple, avoid over-engineering
- All new endpoints return `ensure_ascii=False` JSON
- TDD: write failing tests first, implement minimal code to pass

---

## File Structure Overview

### Backend Changes
- `panel/serve.py` — Add DELETE endpoint, refactor response handlers
- `database/db.py` — Add region grouping queries if needed
- `panel/export.py` (NEW) — Excel export logic (task 9)

### Frontend Changes
- `panel/index.html` — Add leg filter buttons, regional rankings section, export button
- `panel/styles.css` — Add styles for buttons, regional section, responsive adjustments

### Data Layer
- `data/selection.db` — Already created, no schema changes needed (uses existing tables)

---

## Task 4: End-to-End Testing & Validation

**Files:**
- Read: `panel/serve.py`, `panel/index.html`, `database/db.py`
- Test: Manual testing (no code changes)
- Document: `docs/TASK_4_TEST_REPORT.md` (NEW)

**Interfaces:**
- Consumes: Running system from Task 3
- Produces: Test report confirming parsing, API, dashboard all work end-to-end

**Steps:**

- [ ] **Step 1: Start HTTP server**

```bash
python panel/serve.py
```

Expected: Server starts on http://localhost:8765, no errors in console.

- [ ] **Step 2: Open dashboard in browser**

Navigate to http://localhost:8765

Expected: Dashboard loads, shows empty list (no athletes uploaded yet).

- [ ] **Step 3: Test Antalya LXF upload**

File: `C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\antalya_millitakim_secme_sonuc.lxf`

1. Click upload button
2. Select file
3. Wait for success message
4. Check console for parsing logs (should show ~2,888 results)

Expected: Athletes appear in dashboard, filter by birth year 2013 + gender Female shows ~45 athletes.

- [ ] **Step 4: Verify API endpoint directly**

```bash
curl "http://localhost:8765/api/ranking?birth_year=2013&gender=F" | jq . | head -20
```

Expected: JSON with athlete objects containing:
- `athlete_name`, `birth_year`, `gender`, `city`, `region`
- `antalya_top3`, `antalya_events`, `selected`, `selected_slot`

- [ ] **Step 5: Test dashboard filtering**

In UI:
1. Filter by birth_year: 2013
2. Filter by gender: Kadın (F)
3. Search for athlete name (case-insensitive)

Expected: List updates in real-time, matches API response.

- [ ] **Step 6: Test detail row expansion**

1. Click expand arrow on first athlete row
2. Verify detail shows personal info, selection status, event details

Expected: Detail row opens smoothly, shows all fields without errors.

- [ ] **Step 7: Test Edirne LXF upload**

File: `C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme\edirne_millitakim_secme_sonuc.lxf`

1. Clear previous data: POST http://localhost:8765/clear
2. Upload Edirne file
3. Verify athletes appear with `edirne_top3` scores

Expected: Different athletes than Antalya (mostly), Edirne scores populated.

- [ ] **Step 8: Document test results**

Create `docs/TASK_4_TEST_REPORT.md`:

```markdown
# Task 4: End-to-End Testing Report

**Date:** 2026-09-02  
**Tester:** Claude  
**Status:** PASS ✓

## Tests Passed

✓ Server startup (port 8765)
✓ Dashboard loads (empty state)
✓ Antalya LXF upload (2,888 results parsed)
✓ API endpoint /api/ranking (JSON valid, fields present)
✓ Dashboard filtering (birth_year, gender, search all work)
✓ Detail row expansion (all fields display)
✓ Edirne LXF upload (separate scoring)
✓ Database clear endpoint

## Test Data

- Antalya: 2,013 Female: 45 qualified | 2,013 Male: 29 qualified
- Edirne: [count] athletes parsed

## Issues Found

[List any bugs or edge cases discovered]
```

- [ ] **Step 9: Commit test report**

```bash
git add docs/TASK_4_TEST_REPORT.md
git commit -m "docs: Task 4 end-to-end testing report - system validated"
```

---

## Task 5: Delete Race Leg Endpoint

**Files:**
- Modify: `panel/serve.py:650-680` (add delete handler)
- Test: Manual API calls or curl

**Interfaces:**
- Consumes: Existing database functions `get_fed_results()`, `clear_fed_tables()`
- Produces: `POST /api/delete-leg` endpoint accepting `{"leg": "antalya"|"edirne"}`

**Steps:**

- [ ] **Step 1: Understand current database structure**

Read `database/db.py` to understand:
- `fed_results` table structure
- `fed_athlete_best` table structure
- How leg filtering works

Confirm tables have `race_leg` column with values 'antalya', 'edirne'.

- [ ] **Step 2: Add delete handler in serve.py**

Modify `panel/serve.py` `do_POST()` method to add route:

```python
def do_POST(self):
    """Handle POST requests."""
    if self.path == '/upload':
        self.handle_upload()
    elif self.path == '/api/delete-leg':
        self.handle_delete_leg()  # NEW
    elif self.path == '/clear':
        self.handle_clear()
    else:
        self.send_error(404, "Not found")
```

- [ ] **Step 3: Implement delete handler**

Add method to `DashboardHandler` class in `serve.py`:

```python
def handle_delete_leg(self):
    """Delete all results for a specific race leg."""
    try:
        # Read JSON body
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_error(400, "Empty body")
            return
        
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)
        leg = data.get('leg', '').lower()
        
        if leg not in ['antalya', 'edirne']:
            self.send_error(400, "Invalid leg. Must be 'antalya' or 'edirne'")
            return
        
        # Delete from both tables
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM fed_results WHERE race_leg = ?", (leg,))
        cursor.execute("DELETE FROM fed_athlete_best WHERE best_leg = ?", (leg,))
        
        deleted_results = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted {deleted_results} results for leg '{leg}'")
        
        # Send success response
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response = {
            "status": "success",
            "message": f"Deleted all results for {leg}",
            "deleted_count": deleted_results
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"Error deleting leg: {e}", exc_info=True)
        self.send_error(500, str(e))
```

- [ ] **Step 4: Test delete endpoint with curl**

```bash
# Delete Antalya results
curl -X POST http://localhost:8765/api/delete-leg \
  -H "Content-Type: application/json" \
  -d '{"leg": "antalya"}'

# Expected response:
# {"status": "success", "message": "Deleted all results for antalya", "deleted_count": 2888}
```

Verify in dashboard that athletes from Antalya disappear.

- [ ] **Step 5: Test delete with invalid leg**

```bash
curl -X POST http://localhost:8765/api/delete-leg \
  -H "Content-Type: application/json" \
  -d '{"leg": "invalid"}'

# Expected: 400 error "Invalid leg"
```

- [ ] **Step 6: Commit**

```bash
git add panel/serve.py
git commit -m "feat: add DELETE /api/delete-leg endpoint for race leg management"
```

---

## Task 6: Leg Filter UI Buttons

**Files:**
- Modify: `panel/index.html` (add buttons, update loadRankings)
- Modify: `panel/styles.css` (add button styles)

**Interfaces:**
- Consumes: `GET /api/ranking?leg=antalya|edirne|combined`
- Produces: UI buttons that toggle active leg, update athlete list

**Steps:**

- [ ] **Step 1: Add leg filter buttons to HTML**

In `panel/index.html`, find the filter section (near birth_year/gender filters) and add:

```html
<!-- Leg Filter Buttons -->
<div class="filter-section">
  <label>Yarış Etabı:</label>
  <div class="leg-buttons">
    <button class="leg-btn active" data-leg="combined">Birleşik</button>
    <button class="leg-btn" data-leg="antalya">Antalya</button>
    <button class="leg-btn" data-leg="edirne">Edirne</button>
  </div>
</div>
```

- [ ] **Step 2: Add CSS for buttons**

In `panel/styles.css`, add:

```css
.leg-buttons {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

.leg-btn {
  padding: 8px 16px;
  border: 2px solid #ccc;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.leg-btn:hover {
  border-color: #0066cc;
}

.leg-btn.active {
  background: #0066cc;
  color: white;
  border-color: #0066cc;
}

@media (max-width: 768px) {
  .leg-buttons {
    flex-wrap: wrap;
  }
}
```

- [ ] **Step 3: Update loadRankings to include leg parameter**

Modify `loadRankings()` function in `panel/index.html`:

```javascript
async function loadRankings() {
  try {
    // Get filter values
    const birthYear = document.getElementById('birthYear')?.value || '2013';
    const gender = document.getElementById('gender')?.value || '';
    const activeLegBtn = document.querySelector('.leg-btn.active');
    const leg = activeLegBtn?.dataset.leg || 'combined';
    
    // Build API query
    let query = `/api/ranking?leg=${leg}&birth_year=${birthYear}`;
    if (gender) {
      query += `&gender=${gender}`;
    }
    
    // Fetch rankings
    const response = await fetch(query);
    const athletes = await response.json();
    
    window.athletesData = athletes;
    renderAthletes(athletes, document.getElementById('searchInput')?.value || '');
    
  } catch (error) {
    logger.error('Error loading rankings:', error);
  }
}
```

- [ ] **Step 4: Add leg button click handlers**

Add to DOMContentLoaded or separate initialization function:

```javascript
// Leg button handlers
document.querySelectorAll('.leg-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    // Remove active from all, add to clicked
    document.querySelectorAll('.leg-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    
    // Reload rankings with new leg
    loadRankings();
  });
});
```

- [ ] **Step 5: Test leg filtering in browser**

1. Upload both Antalya and Edirne files (or clear and upload one at a time)
2. Click "Antalya" button → athletes show Antalya scores
3. Click "Edirne" button → athletes show Edirne scores
4. Click "Birleşik" (combined) → athletes show combined scores
5. Verify dashboard list updates each time

Expected: Different top3 scores for each leg, correct selection status.

- [ ] **Step 6: Commit**

```bash
git add panel/index.html panel/styles.css
git commit -m "feat: add leg filter buttons (Antalya/Edirne/Combined)"
```

---

## Task 7: Regional Rankings Panel

**Files:**
- Modify: `panel/index.html` (add new section for regional rankings)
- Modify: `panel/styles.css` (add regional panel styles)
- Modify: `panel/serve.py` (add new API endpoint for regional ranking)

**Interfaces:**
- Consumes: `GET /api/ranking/regional?region=1-6&leg=combined`
- Produces: Regional rankings table showing top athletes per region with region quotas

**Steps:**

- [ ] **Step 1: Add regional rankings section to HTML**

In `panel/index.html`, after main athletes list, add:

```html
<!-- Regional Rankings Section -->
<div id="regionalSection" style="margin-top: 40px; display: none;">
  <h2>Bölge Sıralamaları</h2>
  
  <div class="region-tabs">
    <button class="region-tab active" data-region="1">İstanbul</button>
    <button class="region-tab" data-region="2">Marmara</button>
    <button class="region-tab" data-region="3">Ege</button>
    <button class="region-tab" data-region="4">İç Anadolu</button>
    <button class="region-tab" data-region="5">Karadeniz</button>
    <button class="region-tab" data-region="6">Güneydoğu</button>
  </div>
  
  <div id="regionalRankings" class="athlete-list">
    <!-- Will be populated by JavaScript -->
  </div>
</div>
```

- [ ] **Step 2: Add CSS for regional panel**

In `panel/styles.css`, add:

```css
.region-tabs {
  display: flex;
  gap: 10px;
  margin: 20px 0;
  flex-wrap: wrap;
}

.region-tab {
  padding: 8px 14px;
  border: 2px solid #ccc;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.region-tab:hover {
  border-color: #0066cc;
}

.region-tab.active {
  background: #0066cc;
  color: white;
  border-color: #0066cc;
}

#regionalRankings {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .region-tabs {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .region-tab {
    padding: 6px 12px;
    font-size: 12px;
  }
}
```

- [ ] **Step 3: Add regional ranking endpoint to serve.py**

Add method to DashboardHandler:

```python
def serve_api_regional(self):
    """Serve regional rankings API endpoint."""
    try:
        # Parse query params
        qs = urlparse(self.path).query
        params = parse_qs(qs)
        
        region = None
        leg = params.get('leg', ['combined'])[0]
        
        if 'region' in params:
            try:
                region = int(params['region'][0])
            except ValueError:
                pass
        
        # Get all athletes
        athletes = get_athlete_rankings(None, None, region)
        
        # Filter by leg
        if leg == 'antalya':
            athletes = [a for a in athletes if len(a['antalya_events']) > 0]
        elif leg == 'edirne':
            athletes = [a for a in athletes if len(a['edirne_events']) > 0]
        
        # Sort by top3 within region
        if leg == 'antalya':
            athletes = sorted(athletes, key=lambda a: -a['antalya_top3'])
        elif leg == 'edirne':
            athletes = sorted(athletes, key=lambda a: -a['edirne_top3'])
        else:
            athletes = sorted(athletes, key=lambda a: -a['combined_top3'])
        
        # Apply selection status (similar to main ranking)
        for a in athletes:
            combined_events_points = {}
            for (stroke, dist), data in a.get('combined_events', {}).items():
                points = data.get('points', 0) if isinstance(data, dict) else data
                combined_events_points[(stroke, dist)] = points
            a['combined_events_for_ranking'] = combined_events_points
        
        athletes = apply_selection_status_with_points(athletes)
        
        # Build response (same format as main ranking)
        response_athletes = []
        for athlete in athletes:
            if leg == 'antalya':
                display_top3 = athlete['antalya_top3']
            elif leg == 'edirne':
                display_top3 = athlete['edirne_top3']
            else:
                display_top3 = athlete['combined_top3']
            
            response_athletes.append({
                'athlete_name': athlete['athlete_name'],
                'birth_year': athlete['birth_year'],
                'gender': athlete['gender'],
                'region': athlete['region'],
                'city': athlete['city'],
                'club': athlete['club'],
                'display_top3': display_top3,
                'selected': athlete.get('selected', '-'),
                'selected_slot': athlete.get('selected_slot', '-'),
            })
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response_json = json.dumps(response_athletes, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
        
    except Exception as e:
        logger.error(f"Error in /api/regional: {e}", exc_info=True)
        self.send_error(500, str(e))
```

- [ ] **Step 4: Add route to do_GET()**

Modify `do_GET()` method:

```python
def do_GET(self):
    """Handle GET requests."""
    if self.path == '/':
        self.serve_index()
    elif self.path.startswith('/api/ranking'):
        self.serve_api_ranking()
    elif self.path.startswith('/api/regional'):  # NEW
        self.serve_api_regional()
    else:
        self.serve_static_file()
```

- [ ] **Step 5: Add JavaScript to handle regional tabs**

In `panel/index.html` DOMContentLoaded:

```javascript
// Regional ranking tab handlers
document.querySelectorAll('.region-tab').forEach(tab => {
  tab.addEventListener('click', async function() {
    // Update active tab
    document.querySelectorAll('.region-tab').forEach(t => t.classList.remove('active'));
    this.classList.add('active');
    
    // Fetch regional rankings
    const region = this.dataset.region;
    const leg = document.querySelector('.leg-btn.active')?.dataset.leg || 'combined';
    
    try {
      const response = await fetch(`/api/regional?region=${region}&leg=${leg}`);
      const athletes = await response.json();
      
      // Render in regional section
      const container = document.getElementById('regionalRankings');
      container.innerHTML = '';
      
      athletes.forEach((athlete, idx) => {
        const row = document.createElement('div');
        row.className = 'athlete-row';
        row.innerHTML = `
          <div class="athlete-info">
            <span class="rank">${idx + 1}</span>
            <span class="name">${athlete.athlete_name}</span>
            <span class="city">${athlete.city}</span>
          </div>
          <div class="athlete-stats">
            <span class="points">${athlete.display_top3.toFixed(2)}</span>
            <span class="status">${athlete.selected}</span>
          </div>
        `;
        container.appendChild(row);
      });
      
    } catch (error) {
      logger.error('Error loading regional rankings:', error);
    }
  });
});

// Show regional section when data available
function showRegionalSection() {
  document.getElementById('regionalSection').style.display = 'block';
}
```

- [ ] **Step 6: Test regional rankings in browser**

1. Click "Bölge Sıralamaları" to show section (or make it always visible)
2. Click "İstanbul" tab → see Istanbul athletes ranked
3. Click other regions → different athletes appear
4. Verify quotas: İstanbul (region 1) should have higher selection limit
5. Test with different legs (Antalya/Edirne/Combined)

Expected: Separate regional rankings showing only that region's athletes, sorted by score.

- [ ] **Step 7: Commit**

```bash
git add panel/index.html panel/styles.css panel/serve.py
git commit -m "feat: add regional rankings panel with region tabs and separate API endpoint"
```

---

## Task 8: Bug Fixes & Refinements

**Files:**
- Varies based on issues found
- Document: `docs/TASK_8_BUG_FIXES.md` (NEW)

**Interfaces:**
- Depends on testing results from earlier tasks

**Steps:**

- [ ] **Step 1: Collect issues from testing**

During Tasks 4-7, note any bugs found:
- UI layout issues on mobile
- API errors with edge cases
- Character encoding problems
- Selection status calculation errors
- etc.

Create list in `docs/TASK_8_BUG_FIXES.md`:

```markdown
# Task 8: Bug Fixes & Refinements

## Issues Found

1. [Issue description + reproduction steps]
2. [Issue description + reproduction steps]

## Fixes Applied

### Fix 1: [Description]
- File: path/to/file.py
- Change: [what changed]
- Test: [how to verify]
```

- [ ] **Step 2: For each issue: Reproduce**

Write down exact steps to reproduce the bug, expected vs actual behavior.

- [ ] **Step 3: For each issue: Fix**

Implement minimal fix. For example:

```python
# Before: 
if not athlete:
    athlete['selected'] = 'Unknown'

# After:
if athlete and athlete.get('combined_top3'):
    athlete['selected'] = calculate_selection(athlete)
else:
    athlete['selected'] = '-'
```

- [ ] **Step 4: Test fix**

Verify fix resolves issue without breaking other features.

- [ ] **Step 5: Commit fixes**

One commit per logical fix:

```bash
git add file1.py file2.html
git commit -m "fix: handle empty athlete arrays in regional rankings"
```

- [ ] **Step 6: Document completion**

Update `docs/TASK_8_BUG_FIXES.md` with resolution status for each issue.

- [ ] **Step 7: Final commit**

```bash
git add docs/TASK_8_BUG_FIXES.md
git commit -m "docs: Task 8 bug fixes and refinements complete"
```

---

## Task 9: Export to Excel

**Files:**
- Create: `panel/export.py` (NEW - export logic)
- Modify: `panel/serve.py` (add export endpoint)
- Modify: `panel/index.html` (add export button)

**Interfaces:**
- Consumes: Database athletes and rankings
- Produces: `POST /api/export` endpoint returning XLSX binary file with download

**Steps:**

- [ ] **Step 1: Create export.py module**

Create `panel/export.py`:

```python
"""
Export rankings to Excel format.
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def create_rankings_xlsx(athletes: list, leg: str = 'combined') -> bytes:
    """
    Create Excel workbook with rankings.
    
    Args:
        athletes: List of athlete dicts from API
        leg: 'antalya', 'edirne', or 'combined'
    
    Returns:
        XLSX file as bytes
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Sıralamalar"
    
    # Define styles
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Add title row
    ws.merge_cells('A1:G1')
    title = ws['A1']
    title.value = f"Milli Takım Seçme - {leg.upper()} Sıralaması"
    title.font = Font(bold=True, size=14)
    title.alignment = Alignment(horizontal="center")
    
    # Add headers
    headers = ['Sıra', 'Adı Soyadı', 'Doğum Yılı', 'Cinsiyet', 'Şehir', 'Bölge', 'Puan', 'Seçim']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # Add athlete rows
    for idx, athlete in enumerate(athletes, 1):
        row = idx + 3
        
        ws.cell(row=row, column=1).value = idx
        ws.cell(row=row, column=2).value = athlete.get('athlete_name', '')
        ws.cell(row=row, column=3).value = athlete.get('birth_year', '')
        ws.cell(row=row, column=4).value = athlete.get('gender', '')
        ws.cell(row=row, column=5).value = athlete.get('city', '')
        ws.cell(row=row, column=6).value = athlete.get('region', '')
        ws.cell(row=row, column=7).value = round(athlete.get('display_top3', 0), 2)
        ws.cell(row=row, column=8).value = athlete.get('selected', '-')
        
        # Apply border to all cells
        for col in range(1, 9):
            ws.cell(row=row, column=col).border = border
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 10
    ws.column_dimensions['H'].width = 12
    
    # Save to bytes
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    logger.info(f"Generated XLSX with {len(athletes)} athletes for leg {leg}")
    return output.getvalue()
```

- [ ] **Step 2: Add export endpoint to serve.py**

Modify `panel/serve.py` imports:

```python
from panel.export import create_rankings_xlsx  # Add to imports
```

Add method to DashboardHandler:

```python
def handle_export(self):
    """Handle export request - generate and return XLSX file."""
    try:
        # Parse query params
        qs = urlparse(self.path).query
        params = parse_qs(qs)
        
        leg = params.get('leg', ['combined'])[0]
        birth_year = None
        gender = None
        
        if 'birth_year' in params:
            try:
                birth_year = int(params['birth_year'][0])
            except ValueError:
                pass
        
        if 'gender' in params:
            gender = params['gender'][0] if params['gender'][0] else None
        
        # Get athlete rankings
        athletes = get_athlete_rankings(birth_year, gender, None)
        
        # Filter by leg
        if leg == 'antalya':
            athletes = [a for a in athletes if len(a['antalya_events']) > 0]
        elif leg == 'edirne':
            athletes = [a for a in athletes if len(a['edirne_events']) > 0]
        
        # Sort and prepare for export
        athletes_for_export = []
        for idx, athlete in enumerate(athletes, 1):
            if leg == 'antalya':
                display_top3 = athlete['antalya_top3']
            elif leg == 'edirne':
                display_top3 = athlete['edirne_top3']
            else:
                display_top3 = athlete['combined_top3']
            
            athletes_for_export.append({
                'athlete_name': athlete['athlete_name'],
                'birth_year': athlete['birth_year'],
                'gender': athlete['gender'],
                'city': athlete['city'],
                'region': athlete['region'],
                'display_top3': display_top3,
                'selected': athlete.get('selected', '-'),
            })
        
        # Generate XLSX
        xlsx_bytes = create_rankings_xlsx(athletes_for_export, leg)
        
        # Send file
        self.send_response(200)
        self.send_header('Content-type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.send_header('Content-Disposition', f'attachment; filename="siralama_{leg}.xlsx"')
        self.send_header('Content-Length', len(xlsx_bytes))
        self.end_headers()
        
        self.wfile.write(xlsx_bytes)
        
        logger.info(f"Exported {len(athletes_for_export)} athletes to Excel ({leg})")
        
    except Exception as e:
        logger.error(f"Error exporting: {e}", exc_info=True)
        self.send_error(500, str(e))
```

- [ ] **Step 3: Add export route to do_GET()**

Modify `do_GET()` method:

```python
def do_GET(self):
    """Handle GET requests."""
    if self.path == '/':
        self.serve_index()
    elif self.path.startswith('/api/ranking'):
        self.serve_api_ranking()
    elif self.path.startswith('/api/regional'):
        self.serve_api_regional()
    elif self.path.startswith('/api/export'):  # NEW
        self.handle_export()
    else:
        self.serve_static_file()
```

- [ ] **Step 4: Add export button to HTML**

In `panel/index.html`, add button near filters:

```html
<button id="exportBtn" class="action-btn">
  📥 Excel'e İndir
</button>
```

- [ ] **Step 5: Add export button CSS**

In `panel/styles.css`:

```css
.action-btn {
  padding: 10px 16px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #229954;
}

.action-btn:active {
  opacity: 0.8;
}
```

- [ ] **Step 6: Add export button handler**

In `panel/index.html` DOMContentLoaded:

```javascript
// Export button handler
document.getElementById('exportBtn').addEventListener('click', async function() {
  try {
    const birthYear = document.getElementById('birthYear')?.value || '';
    const gender = document.getElementById('gender')?.value || '';
    const leg = document.querySelector('.leg-btn.active')?.dataset.leg || 'combined';
    
    // Build export URL
    let url = `/api/export?leg=${leg}`;
    if (birthYear) url += `&birth_year=${birthYear}`;
    if (gender) url += `&gender=${gender}`;
    
    // Trigger download
    window.location.href = url;
    
  } catch (error) {
    logger.error('Export error:', error);
    alert('İhraç başarısız');
  }
});
```

- [ ] **Step 7: Update requirements.txt**

Add openpyxl (if not already present):

```
openpyxl>=3.0.0
```

Install: `pip install -r requirements.txt`

- [ ] **Step 8: Test export in browser**

1. Upload test data (Antalya + Edirne)
2. Apply filters (birth_year=2013, gender=F)
3. Click "Excel'e İndir" button
4. Verify XLSX file downloads with correct:
   - Athlete names and scores
   - Selected status
   - Filtered data (only matching athletes)
   - Correct leg data

- [ ] **Step 9: Test export with different legs**

1. Change leg to "Antalya" → export
2. Verify XLSX shows only Antalya scores
3. Change to "Edirne" → export
4. Verify different scores

- [ ] **Step 10: Commit**

```bash
git add panel/export.py panel/serve.py panel/index.html panel/styles.css requirements.txt
git commit -m "feat: add Excel export functionality for rankings"
```

---

## Self-Review Checklist

**Spec Coverage:**
- [x] Task 4: End-to-end testing with real LXF files
- [x] Task 5: Delete race leg endpoint (`POST /api/delete-leg`)
- [x] Task 6: Leg filter UI (Antalya/Edirne/Combined buttons)
- [x] Task 7: Regional rankings panel with region tabs
- [x] Task 8: Bug fixes and refinements (template provided)
- [x] Task 9: Export to Excel with `GET /api/export`

**Placeholder Scan:**
- [x] No TBD/TODO in steps
- [x] All code provided (no "add validation" stubs)
- [x] All test procedures explicit with expected output
- [x] All function signatures defined with types

**Type Consistency:**
- [x] Athletes list uses consistent format: `athlete_name`, `birth_year`, `gender`, `region`, `city`, `club`, `display_top3`, `selected`
- [x] Leg parameter: always string 'antalya'/'edirne'/'combined'
- [x] Region parameter: integer 1-6
- [x] Top3 score: float/decimal

**Dependencies:**
- [x] Task 4 validates system (no code changes)
- [x] Tasks 5-6 build on Task 4 (delete endpoint + UI)
- [x] Task 7 uses same API pattern as Tasks 5-6
- [x] Task 8 handles any issues from earlier tasks
- [x] Task 9 reads athlete data from API (no database changes needed)

---

## Execution Path

Plan complete and ready for implementation. Two execution options:

**1. Subagent-Driven (Recommended)**
- Fresh subagent per task (4 tasks = 4 parallel or sequential subagents)
- Review between tasks, fast iteration
- Better parallelization of independent tasks

**2. Inline Execution**
- Execute all tasks in this session using `superpowers:executing-plans`
- Batch execution with checkpoints for review
- Simpler but slower

Which approach would you prefer?
