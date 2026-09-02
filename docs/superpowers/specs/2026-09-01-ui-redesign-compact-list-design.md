# UI Redesign: Compact List Layout (DIV-based)

**Date:** 2026-09-01  
**Status:** Approved  
**Scope:** Complete redesign of athlete ranking display from table format to compact list with inline expandable details

---

## 1. Overview

Replace existing table-based athlete ranking UI with a **compact list layout** (DIV-based) featuring:
- Responsive row-based design with badge/madalya column
- Inline expandable detail rows (existing expand logic preserved)
- Dark theme (system preference detection) + optional light theme toggle
- Real-time athlete name search/filter
- Selection badges (TR, BÖLGE, MULTINATIONS)
- Tiebreaker information in detail rows

**Why DIV-based?**
- More flexible for badge/madalya placement
- Cleaner HTML semantics (table = tabular data, not UI layout)
- Easier to extend with future features
- Better CSS Grid control for responsive design

---

## 2. Architecture

### Overall Structure
```
<div id="athletes-list" class="theme-container">
  <!-- Filter bar -->
  <div class="filter-bar">
    <input type="search" placeholder="Sporcu adı ara..." class="athlete-search">
    <select class="birth-year-filter">...</select>
    <select class="gender-filter">...</select>
    <select class="leg-filter">...</select>
  </div>

  <!-- List header -->
  <div class="list-header">
    <div class="col-badge">Sıra</div>
    <div class="col-name">Sporcu</div>
    <div class="col-info">Şehir (Kulüp)</div>
    <div class="col-stats">Puan | Seçim | Yaş/Cinsiyet</div>
    <div class="col-action"></div>
  </div>

  <!-- Athlete rows -->
  <div class="athlete-row" data-athlete-id="1">
    <div class="col-badge">🥇</div>
    <div class="col-name">Cemre İnce</div>
    <div class="col-info">Antalya (Kızılot SK)</div>
    <div class="col-stats">19 | TR-1 | 2011 Kadın</div>
    <div class="col-action"><button class="expand-btn">↓</button></div>
    
    <!-- Detail row (hidden by default, toggle on click) -->
    <div class="detail-row" hidden>
      <div class="detail-content">
        [races table, tiebreaker, selection info]
      </div>
    </div>
  </div>
  
  <!-- More rows... -->
</div>
```

### Component Hierarchy
- **List container** (`.athletes-list`): Main wrapper with dark mode toggle
- **Filter bar** (`.filter-bar`): Search + existing filters (birth_year, gender, leg)
- **List header** (`.list-header`): Column labels
- **Athlete row** (`.athlete-row`): Single athlete entry with badge, info, action
- **Detail row** (`.detail-row`): Inline expandable showing races, tiebreaker, selection

### Responsiveness
- **Desktop (1200px+):** 5-column grid: badge (60px) | name (200px) | info (200px) | stats (flexible) | action (60px)
- **Tablet (768px-1199px):** 3-column: badge | name+info | stats+action
- **Mobile (< 768px):** Single column (stack layout)

---

## 3. Components

### Athlete Row Component

**Structure:**
```html
<div class="athlete-row" data-athlete-id="1" data-ranking="1">
  <div class="col-badge">🥇</div>
  <div class="col-name">Cemre İnce</div>
  <div class="col-info">Antalya (Kızılot SK)</div>
  <div class="col-stats">
    <span class="points">19</span>
    <span class="selection-badge" data-status="TR">TR-1</span>
    <span class="age-gender">2011 Kadın</span>
  </div>
  <div class="col-action">
    <button class="expand-btn" aria-label="Detayları aç">↓</button>
  </div>
</div>
```

**Badge/Madalya Logic:**
- `ranking=1` → `🥇` (gold medal)
- `ranking=2` → `🥈` (silver medal)
- `ranking=3` → `🥉` (bronze medal)
- `ranking≥4` → number (4., 5., 6., etc.)

**Selection Badge Colors:**
- `TR` → Blue (`#4a9eff`)
- `BÖLGE` → Orange (`#ff9800`)
- `MULTINATIONS` → Purple (`#9c27b0`)
- `BARAJ_YOK` → Gray (`#999`)

**Multinations Indicator:** ⭐ star icon if `multinations=true`

### Detail Row Component

**Revealed on athlete row click:**
```html
<div class="detail-row">
  <div class="detail-content">
    <!-- Races table -->
    <table class="races-table">
      <thead>
        <tr>
          <th>Stil</th>
          <th>Mesafe</th>
          <th>Derece (Zaman)</th>
          <th>Puan</th>
          <th>Seçim Sırası</th>
        </tr>
      </thead>
      <tbody>
        <!-- Sorted by points (desc), top 3 highlighted -->
        <tr class="top-race">
          <td>Serbest Stil</td>
          <td>100m</td>
          <td>1:02.45</td>
          <td>9</td>
          <td>1</td>
        </tr>
        <!-- More rows... -->
      </tbody>
    </table>

    <!-- Tiebreaker info -->
    <div class="tiebreaker-info">
      <div>Top 3 Toplam: 23</div>
      <div>Top 4 Toplam: 30</div>
      <div>Top 5 Toplam: 36</div>
      <div>Top 6 Toplam: 41</div>
    </div>

    <!-- Selection info -->
    <div class="selection-info">
      <div class="badge-info">Seçim Durumu: <span class="badge">TR-1</span></div>
      <div class="region-info">Bölge: Akdeniz</div>
      <div class="multinations-info" v-if="multinations">⭐ Multinations</div>
    </div>
  </div>
</div>
```

**Top 3 Races:** Yellow background (`background: #ffd700`)

---

## 4. Styling & Layout

### CSS Variables (Dark Mode Primary)
```css
:root {
  /* Light theme (gündüz) */
  --bg-main: #ffffff;
  --bg-row: #f9f9f9;
  --bg-row-hover: #f0f0f0;
  --text-main: #000000;
  --text-secondary: #666;
  --border-color: #ddd;
  --header-bg: #f5f5f5;
  --badge-tr: #4a9eff;
  --badge-bolge: #ff9800;
  --badge-multi: #9c27b0;
  --highlight-top3: #ffd700;
}

@media (prefers-color-scheme: dark) {
  :root {
    /* Dark theme (gece) */
    --bg-main: #1a1a1a;
    --bg-row: #2a2a2a;
    --bg-row-hover: #333;
    --text-main: #ffffff;
    --text-secondary: #aaa;
    --border-color: #444;
    --header-bg: #0d0d0d;
    --badge-tr: #5ba3ff;
    --badge-bolge: #ffb84d;
    --badge-multi: #bb86fc;
    --highlight-top3: #ffd700;
  }
}
```

### Grid Layout
```css
.list-header, .athlete-row {
  display: grid;
  grid-template-columns: 60px 200px 200px 1fr 60px;
  gap: 12px;
  padding: 12px;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-row);
}

.list-header {
  background: var(--header-bg);
  font-weight: bold;
  color: #4a9eff;
  position: sticky;
  top: 0;
  z-index: 10;
}

.athlete-row {
  cursor: pointer;
  transition: background 0.2s;
}

.athlete-row:hover {
  background: var(--bg-row-hover);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .list-header, .athlete-row {
    grid-template-columns: 1fr;
    padding: 8px;
  }
  
  .col-badge, .col-action {
    display: none;
  }
}
```

### Badges & Selection Styling
```css
.selection-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.selection-badge[data-status="TR"] {
  background: var(--badge-tr);
}

.selection-badge[data-status="BÖLGE"] {
  background: var(--badge-bolge);
  color: white;
}

.selection-badge[data-status="MULTINATIONS"] {
  background: var(--badge-multi);
  color: white;
}
```

### Detail Row Styling
```css
.detail-row {
  grid-column: 1 / -1;
  padding: 16px;
  background: var(--bg-row-hover);
  border-top: 1px solid var(--border-color);
}

.races-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}

.races-table th, .races-table td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.races-table .top-race {
  background: var(--highlight-top3);
  color: black;
  font-weight: bold;
}

.tiebreaker-info, .selection-info {
  margin: 8px 0;
  font-size: 14px;
}
```

---

## 5. Data Flow

### API Response Format (GET /api/ranking)
```json
{
  "athletes": [
    {
      "id": 1,
      "name": "Cemre İnce",
      "birth_year": 2011,
      "gender": "F",
      "city": "Antalya",
      "club": "Kızılot SK",
      "region": "Akdeniz",
      "points": 19,
      "selection_status": "TR",
      "selection_slot": "TR-1",
      "multinations": false,
      "ranking": 1,
      "events": {
        "(serbest, 100)": { "points": 9, "time": "1:02.45" },
        "(kelebek, 100)": { "points": 7, "time": "1:15.20" },
        "(sirt, 100)": { "points": 5, "time": "1:10.30" }
      },
      "tiebreaker": {
        "top3": 23,
        "top4": 30,
        "top5": 36,
        "top6": 41
      }
    }
  ]
}
```

### Rendering Pipeline

1. **Fetch athletes** from `/api/ranking?leg=combined&birth_year=2011&gender=F` (with filters)
2. **Parse response** → build athlete row HTML
3. **Madalya mapping:** `ranking → badge` (1→🥇, 2→🥈, 3→🥉, 4+→number)
4. **Selection badge:** color by `selection_status`
5. **Multinations indicator:** show ⭐ if `multinations=true`
6. **Detail row population (on expand):**
   - Sort `events` by points (descending)
   - Highlight top 3 races (yellow background)
   - Render `tiebreaker` sums
   - Show `selection_slot` and region

### Search/Filter Flow

**Real-time athlete name search:**
```javascript
// On input change
const searchQuery = inputValue.toLowerCase();
athletes.filter(a => a.name.toLowerCase().includes(searchQuery));
// Also handle Turkish characters: İ→i, ç→c, etc. (Turkish locale)
```

---

## 6. Testing Strategy

### Manual Test Checklist

**6.1 Rendering**
- [ ] Athletes list loads with compact row format
- [ ] Madalyalar display correctly (🥇🥈🥉 or 4., 5., 6.)
- [ ] Selection badges appear with correct colors (TR=blue, BÖLGE=orange, MULTINATIONS=purple)
- [ ] Multinations ⭐ badge shows when applicable
- [ ] All athlete rows are visible (no layout breaks)

**6.2 Dark Mode**
- [ ] System dark mode ON → dark theme activates automatically
- [ ] System light mode ON → light theme activates automatically
- [ ] Color contrast meets accessibility standards (WCAG AA)
- [ ] Text readable in both themes
- [ ] Badges visible in both themes

**6.3 Inline Expand**
- [ ] Click athlete row → detail-row expands
- [ ] Races sorted by points (descending)
- [ ] Top 3 races highlighted with yellow background
- [ ] Tiebreaker sums (top3, top4, top5, top6) displayed correctly
- [ ] Selection slot and region info shown
- [ ] Click again or close button → detail-row collapses
- [ ] Detail row HTML matches existing expand logic

**6.4 Responsive Design**
- [ ] Desktop (1920px): 5-column grid displays normally
- [ ] Tablet (768px): 3-column grid, layout adjusts
- [ ] Mobile (375px): Single column stack, readable on small screen
- [ ] No horizontal scroll at any breakpoint
- [ ] Badge and action columns hide on mobile (show on desktop)

**6.5 Filters & Search**
- [ ] Birth year filter → list updates (only 2011/2012/2013 score points)
- [ ] Gender filter → list updates
- [ ] Leg filter (Antalya/Edirne/Combined) → scores recalculate
- [ ] Athlete name search (real-time) → filters list
- [ ] Turkish character search works (İ, ş, ç, ğ, ü, ö)
- [ ] Search case-insensitive
- [ ] Clear search → full list returns

**6.6 Edge Cases**
- [ ] Empty result set (no athletes match filter) → show "No results" message
- [ ] Athlete with no races → handle gracefully
- [ ] Very long athlete name → truncate or wrap properly
- [ ] Very long club name → truncate or wrap properly

---

## 7. Implementation Notes

### Files to Modify
- **panel/index.html:** Complete rewrite of athlete list section (table → DIV layout)
- **panel/styles.css** (new or inline): Dark mode variables, grid layout, responsive design
- **panel/app.js** (existing): Adapt render logic to populate new DIV structure

### Preserve Existing Logic
- Inline expand mechanism (toggle detail-row visibility)
- API endpoint structure (no backend changes)
- Filter logic (birth_year, gender, leg)
- Tiebreaker calculation (no changes needed)

### New Features
- System dark mode detection (`prefers-color-scheme`)
- Real-time athlete name search (frontend-only)
- Madalya/badge display logic
- Responsive grid layout

### Backward Compatibility
- No database schema changes
- No API response structure changes
- No server-side logic changes
- Pure frontend redesign

---

## 8. Success Criteria

✅ Compact list layout renders correctly (DIV-based, not table)  
✅ Dark mode auto-activates based on system preference  
✅ Inline expand shows detail rows with races sorted by points  
✅ Madalya badges (🥇🥈🥉) display for top 3 athletes  
✅ Selection badges colored by status (TR/BÖLGE/MULTINATIONS)  
✅ Real-time athlete name search filters list  
✅ Responsive on desktop/tablet/mobile  
✅ All existing filters (birth_year, gender, leg) still work  
✅ Tiebreaker info shows in detail rows  
✅ Dark and light themes both readable  

---

## 9. Rollback Plan

If issues arise post-deploy:
1. Revert `panel/index.html` to previous commit (old table-based UI)
2. Revert `panel/styles.css` if added separately
3. Clear browser cache (`Ctrl+F5`)
4. Restart server

No database or server-side rollback needed.

---

**Spec Status:** Ready for implementation plan
