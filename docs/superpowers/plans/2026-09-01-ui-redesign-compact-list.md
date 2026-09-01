# UI Redesign: Compact List Layout - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace table-based athlete ranking display with compact DIV-based list featuring dark mode, inline expandable detail rows, athlete name search, and responsive grid layout.

**Architecture:** Frontend-only redesign (no backend changes). Rewrite HTML structure from `<table>` to `<div>` grid layout, add CSS with dark mode variables and responsive breakpoints, adapt existing JavaScript render functions to populate new structure. Preserve existing inline expand toggle and API integration.

**Tech Stack:** HTML5, CSS3 (CSS Grid, CSS Variables, `@media`), JavaScript (ES6+), fetch API

**Spec:** `docs/superpowers/specs/2026-09-01-ui-redesign-compact-list-design.md`

## Global Constraints

- UTF-8 encoding throughout
- Turkish character support (İ, ş, ç, ğ, ü, ö)
- Dark theme default (system `prefers-color-scheme` detection)
- No backend/database changes
- No API response format changes
- Preserve existing filter logic (birth_year, gender, leg)
- Preserve inline expand mechanism

---

## File Structure

### Files to Modify

**`panel/index.html`**
- Replace existing `<table id="athletes-list">` section with new DIV-based structure
- New elements: `.athletes-list`, `.filter-bar`, `.list-header`, `.athlete-row`, `.detail-row`
- Responsibility: Semantic HTML for list container, filter controls, athlete rows, expandable detail sections
- Coordinate with: `styles.css` (CSS classes), `app.js` (JavaScript rendering)

**`panel/styles.css` (new or inline in HTML)**
- CSS variables for light/dark themes
- Grid layout for responsive design
- All styling for new structure
- Responsibility: Theme switching, responsive breakpoints, component styling
- Coordinate with: `index.html` (class names), dark mode detection

**`panel/app.js` (adapt existing)**
- Modify `renderAthletes()` function to build new DIV structure (not table rows)
- Add `getRankingBadge()` helper for madalya logic (1→🥇, 2→🥈, 3→🥉, 4+→number)
- Add `getSelectionBadgeColor()` helper for badge colors
- Adapt `renderDetailRow()` or similar to populate races table in new structure
- Add `initializeAthleteSearch()` for real-time name filtering
- Add `toggleDetailRow()` for inline expand/collapse
- Responsibility: Data-to-HTML rendering, event handlers, search/filter logic
- Coordinate with: `index.html` (HTML class names), API data structure

---

## Tasks

### Task 1: Create Stylesheet with Dark Mode & Grid Layout

**Files:**
- Create: `panel/styles.css` (or add inline to `panel/index.html` in `<style>` tag)

**Interfaces:**
- Consumes: CSS class names from index.html (`.athletes-list`, `.filter-bar`, `.list-header`, `.athlete-row`, `.detail-row`, `.col-badge`, `.col-name`, `.col-info`, `.col-stats`, `.col-action`, `.selection-badge`, `.races-table`, `.top-race`, `.tiebreaker-info`, `.selection-info`)
- Produces: Styled layout with dark/light theme support, responsive breakpoints

- [ ] **Step 1: Write CSS with dark mode variables**

Create `panel/styles.css` with the following content:

```css
/* ===== THEME VARIABLES ===== */
:root {
  /* Light theme (default / gündüz) */
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
  --badge-baraj: #999;
  --highlight-top3: #ffd700;
}

/* Dark theme (gece) - auto-activate on system dark mode preference */
@media (prefers-color-scheme: dark) {
  :root {
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
    --badge-baraj: #999;
    --highlight-top3: #ffd700;
  }
}

/* ===== MAIN CONTAINER ===== */
body {
  background: var(--bg-main);
  color: var(--text-main);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  padding: 0;
  transition: background 0.3s, color 0.3s;
}

#app {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

/* ===== FILTER BAR ===== */
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-bar input,
.filter-bar select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-row);
  color: var(--text-main);
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.filter-bar input::placeholder {
  color: var(--text-secondary);
}

.filter-bar input:focus,
.filter-bar select:focus {
  outline: none;
  border-color: #4a9eff;
  box-shadow: 0 0 4px rgba(74, 158, 255, 0.3);
}

/* ===== ATHLETES LIST CONTAINER ===== */
.athletes-list {
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

/* ===== LIST HEADER ===== */
.list-header {
  display: grid;
  grid-template-columns: 60px 200px 200px 1fr 60px;
  gap: 12px;
  padding: 12px;
  background: var(--header-bg);
  border-bottom: 2px solid var(--border-color);
  font-weight: bold;
  color: #4a9eff;
  position: sticky;
  top: 0;
  z-index: 10;
}

/* ===== ATHLETE ROW ===== */
.athlete-row {
  display: grid;
  grid-template-columns: 60px 200px 200px 1fr 60px;
  gap: 12px;
  padding: 12px;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-row);
  cursor: pointer;
  transition: background 0.2s;
}

.athlete-row:hover {
  background: var(--bg-row-hover);
}

/* ===== ROW COLUMNS ===== */
.col-badge {
  text-align: center;
  font-size: 24px;
  font-weight: bold;
}

.col-name {
  font-weight: 500;
  color: var(--text-main);
}

.col-info {
  font-size: 13px;
  color: var(--text-secondary);
}

.col-stats {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
}

.col-stats .points {
  font-weight: bold;
  color: #4a9eff;
}

.col-stats .age-gender {
  color: var(--text-secondary);
}

.col-action {
  text-align: center;
}

.col-action button {
  background: var(--badge-tr);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: opacity 0.2s;
}

.col-action button:hover {
  opacity: 0.8;
}

/* ===== SELECTION BADGES ===== */
.selection-badge {
  display: inline-block;
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

.selection-badge[data-status="BARAJ_YOK"] {
  background: var(--badge-baraj);
  color: white;
}

.multinations-star {
  display: inline-block;
  margin-left: 4px;
}

/* ===== DETAIL ROW (INLINE EXPANDABLE) ===== */
.detail-row {
  grid-column: 1 / -1;
  padding: 16px;
  background: var(--bg-row-hover);
  border-top: 1px solid var(--border-color);
  display: none;
}

.detail-row.visible {
  display: block;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== RACES TABLE (IN DETAIL ROW) ===== */
.races-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-main);
  margin: 0;
}

.races-table thead {
  background: var(--header-bg);
}

.races-table th {
  padding: 8px;
  text-align: left;
  font-weight: bold;
  border-bottom: 1px solid var(--border-color);
  color: #4a9eff;
}

.races-table td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.races-table .top-race {
  background: var(--highlight-top3);
  color: black;
  font-weight: bold;
}

.races-table .top-race td {
  background: var(--highlight-top3);
  color: black;
}

/* ===== TIEBREAKER INFO ===== */
.tiebreaker-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  padding: 12px;
  background: var(--bg-row);
  border-radius: 4px;
  font-size: 13px;
}

.tiebreaker-info > div {
  display: flex;
  flex-direction: column;
}

.tiebreaker-info strong {
  color: #4a9eff;
  font-weight: bold;
}

/* ===== SELECTION INFO ===== */
.selection-info {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: var(--bg-row);
  border-radius: 4px;
  font-size: 13px;
  flex-wrap: wrap;
}

.selection-info > div {
  display: flex;
  gap: 8px;
  align-items: center;
}

.selection-info strong {
  color: #4a9eff;
  font-weight: bold;
}

/* ===== NO RESULTS MESSAGE ===== */
.no-results {
  grid-column: 1 / -1;
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
}

/* ===== RESPONSIVE DESIGN ===== */

/* Tablet: 768px - 1199px */
@media (max-width: 1199px) {
  .list-header,
  .athlete-row {
    grid-template-columns: 60px 1fr 60px;
  }

  .col-name {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .col-name .info-secondary {
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: normal;
  }

  .col-info {
    display: none;
  }

  .col-stats {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* Mobile: < 768px */
@media (max-width: 768px) {
  #app {
    padding: 12px;
  }

  .filter-bar {
    gap: 8px;
    margin-bottom: 16px;
  }

  .filter-bar input,
  .filter-bar select {
    flex: 1;
    min-width: 120px;
  }

  .list-header,
  .athlete-row {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 8px;
  }

  .col-badge {
    display: none;
  }

  .col-action {
    display: none;
  }

  .col-name {
    font-size: 15px;
    font-weight: 600;
  }

  .col-info {
    display: block;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .col-stats {
    display: flex;
    flex-direction: row;
    gap: 8px;
    font-size: 12px;
    flex-wrap: wrap;
  }

  .detail-row {
    padding: 12px;
  }

  .tiebreaker-info {
    grid-template-columns: 1fr;
  }

  .selection-info {
    flex-direction: column;
    gap: 8px;
  }

  .races-table {
    font-size: 12px;
  }

  .races-table th,
  .races-table td {
    padding: 6px;
  }
}
```

- [ ] **Step 2: Link stylesheet to index.html**

In `panel/index.html`, add this line in `<head>`:
```html
<link rel="stylesheet" href="styles.css">
```

Or add inline in `<style>` tag if preferred. Confirm stylesheet loads in browser DevTools.

- [ ] **Step 3: Verify dark mode detection works**

Open page in browser, toggle system dark mode (Settings > Display > Dark mode). Confirm colors change automatically without page reload. Check both light and dark themes have sufficient contrast.

- [ ] **Step 4: Commit stylesheet**

```bash
git add panel/styles.css
git commit -m "feat: add stylesheet with dark mode variables and grid layout"
```

---

### Task 2: Rewrite HTML Structure (DIV-based List)

**Files:**
- Modify: `panel/index.html`

**Interfaces:**
- Consumes: CSS classes from `styles.css`
- Produces: HTML structure with `.athletes-list`, `.filter-bar`, `.list-header`, `.athlete-row`, `.detail-row` (empty, to be populated by JavaScript)

- [ ] **Step 1: Identify existing athlete list section in index.html**

Find the `<table id="athletes-list">` or similar section. Note the existing structure and filter controls (birth year, gender, leg).

- [ ] **Step 2: Replace table with new DIV structure**

Replace the entire athlete list section with:

```html
<div class="filter-bar">
  <input 
    type="search" 
    id="athlete-search" 
    class="athlete-search" 
    placeholder="Sporcu adı ara..." 
    autocomplete="off"
  >
  <select id="birth-year-filter" class="birth-year-filter">
    <option value="">Doğum Yılı</option>
    <option value="2011">2011</option>
    <option value="2012">2012</option>
    <option value="2013">2013</option>
    <option value="2009">2009</option>
    <option value="2010">2010</option>
    <option value="2014">2014</option>
  </select>
  <select id="gender-filter" class="gender-filter">
    <option value="">Cinsiyet</option>
    <option value="F">Kadın</option>
    <option value="M">Erkek</option>
  </select>
  <select id="leg-filter" class="leg-filter">
    <option value="">Leg</option>
    <option value="antalya">Antalya</option>
    <option value="edirne">Edirne</option>
    <option value="combined">Combined</option>
  </select>
</div>

<div id="athletes-list" class="athletes-list">
  <div class="list-header">
    <div class="col-badge">Sıra</div>
    <div class="col-name">Sporcu</div>
    <div class="col-info">Şehir (Kulüp)</div>
    <div class="col-stats">Puan | Seçim | Yaş/Cinsiyet</div>
    <div class="col-action"></div>
  </div>
  <!-- Athlete rows will be populated by JavaScript -->
  <div id="athletes-container"></div>
</div>

<div id="loading" style="display:none; text-align: center; padding: 20px;">
  <p>Sporcular yükleniyor...</p>
</div>

<div id="no-results" class="no-results" style="display:none;">
  Arama kriterlerine uygun sporcu bulunamadı.
</div>
```

- [ ] **Step 3: Remove old table structure completely**

Delete the old `<table>`, `<tr>`, `<td>` elements. Keep all filtering logic and JavaScript references.

- [ ] **Step 4: Verify HTML renders without errors**

Open `http://localhost:8765` in browser. Confirm filter bar appears, athletes-list container visible, no JavaScript errors in console.

- [ ] **Step 5: Commit HTML changes**

```bash
git add panel/index.html
git commit -m "refactor: replace table with DIV-based list structure"
```

---

### Task 3: Implement Athlete Row Rendering

**Files:**
- Modify: `panel/app.js` (or main JavaScript in index.html)

**Interfaces:**
- Consumes: API response with `athletes` array containing: `id`, `name`, `birth_year`, `gender`, `city`, `club`, `region`, `points`, `selection_status`, `selection_slot`, `multinations`, `ranking`, `events`, `tiebreaker`
- Produces: Function `renderAthletes(athletes, searchQuery = '')` that populates `#athletes-container` with `.athlete-row` divs

- [ ] **Step 1: Add helper functions for badge logic**

Add these functions to JavaScript:

```javascript
// Map ranking number to madalya emoji
function getRankingBadge(ranking) {
  if (ranking === 1) return '🥇';
  if (ranking === 2) return '🥈';
  if (ranking === 3) return '🥉';
  return ranking + '.';
}

// Get badge color class based on selection status
function getSelectionBadgeStatus(status) {
  return status || 'BARAJ_YOK';
}

// Format event key tuple string to readable text (e.g., "(serbest, 100)" → "Serbest 100m")
function formatEventKey(keyStr) {
  // keyStr format: "(stroke, distance)" e.g., "(serbest, 100)"
  const match = keyStr.match(/\(([^,]+),\s*(\d+)\)/);
  if (!match) return keyStr;
  
  const stroke = match[1].trim();
  const distance = match[2];
  
  const strokeNames = {
    'serbest': 'Serbest Stil',
    'kelebek': 'Kelebek',
    'sirt': 'Sırt',
    'kurbağa': 'Kurbağa',
    'karışık': 'Karışık'
  };
  
  const strokeDisplay = strokeNames[stroke.toLowerCase()] || stroke;
  return `${strokeDisplay} ${distance}m`;
}

// Filter athletes by search query (case-insensitive, Turkish chars)
function filterAthletesBySearch(athletes, query) {
  if (!query) return athletes;
  
  const lowerQuery = query.toLowerCase().trim();
  return athletes.filter(a => 
    a.name.toLowerCase().includes(lowerQuery)
  );
}
```

- [ ] **Step 2: Implement main renderAthletes function**

```javascript
function renderAthletes(athletes, searchQuery = '') {
  const container = document.getElementById('athletes-container');
  const noResultsDiv = document.getElementById('no-results');
  
  if (!athletes || athletes.length === 0) {
    container.innerHTML = '';
    noResultsDiv.style.display = 'block';
    return;
  }
  
  // Filter by search query
  const filtered = filterAthletesBySearch(athletes, searchQuery);
  
  if (filtered.length === 0) {
    container.innerHTML = '';
    noResultsDiv.style.display = 'block';
    return;
  }
  
  noResultsDiv.style.display = 'none';
  
  // Render each athlete row
  container.innerHTML = filtered.map(athlete => {
    const badge = getRankingBadge(athlete.ranking);
    const status = getSelectionBadgeStatus(athlete.selection_status);
    const multinationsIndicator = athlete.multinations 
      ? '<span class="multinations-star">⭐</span>' 
      : '';
    
    return `
      <div class="athlete-row" data-athlete-id="${athlete.id}" data-ranking="${athlete.ranking}">
        <div class="col-badge">${badge}</div>
        <div class="col-name">
          ${athlete.name}
          ${multinationsIndicator}
        </div>
        <div class="col-info">
          ${athlete.city} (${athlete.club})
        </div>
        <div class="col-stats">
          <span class="points">${athlete.points}</span>
          <span class="selection-badge" data-status="${status}">
            ${athlete.selection_slot}
          </span>
          <span class="age-gender">${athlete.birth_year} ${athlete.gender === 'F' ? 'Kadın' : 'Erkek'}</span>
        </div>
        <div class="col-action">
          <button class="expand-btn" aria-label="Detayları aç">↓</button>
        </div>
      </div>
      <div class="detail-row" data-athlete-id="${athlete.id}">
        <div class="detail-content">
          <!-- Races table will be populated on expand -->
          <div class="races-placeholder">Yükleniyor...</div>
        </div>
      </div>
    `;
  }).join('');
  
  // Attach event listeners to expand buttons
  container.querySelectorAll('.expand-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const row = this.closest('.athlete-row');
      const athleteId = row.dataset.athleteId;
      toggleDetailRow(athleteId);
    });
  });
}
```

- [ ] **Step 3: Test rendering without detail rows**

Call `renderAthletes(athletes)` with mock data. Confirm:
- Each athlete appears as a row
- Badges display correctly (🥇🥈🥉 or 4., 5., etc.)
- Selection badges show with correct text (TR-1, BÖLGE 1-1, etc.)
- Multinations ⭐ shows when applicable
- No layout breaks

- [ ] **Step 4: Commit athlete row rendering**

```bash
git add panel/app.js
git commit -m "feat: implement athlete row rendering with badges and selection info"
```

---

### Task 4: Implement Detail Row Rendering (Races Table)

**Files:**
- Modify: `panel/app.js`

**Interfaces:**
- Consumes: Single `athlete` object with `events`, `tiebreaker`, `selection_status`, `selection_slot`, `region`, `multinations`
- Produces: Function `populateDetailRow(athlete)` that generates races table HTML with top-3 highlights, tiebreaker sums, selection info

- [ ] **Step 1: Add function to sort and render races**

```javascript
function populateDetailRow(athlete) {
  // events is a dict: "(stroke, distance)" -> {points, time}
  const events = athlete.events || {};
  
  // Convert to array, sort by points descending
  const eventsList = Object.entries(events)
    .map(([key, data]) => ({
      key,
      ...data
    }))
    .sort((a, b) => (b.points || 0) - (a.points || 0));
  
  // Create races table HTML
  const racesHTML = `
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
        ${eventsList.map((event, idx) => {
          const isTopRace = idx < 3; // Top 3 races
          const rowClass = isTopRace ? 'top-race' : '';
          const [stroke, distance] = event.key.match(/\(([^,]+),\s*(\d+)\)/)?.slice(1) || ['', ''];
          const displayStroke = {
            'serbest': 'Serbest Stil',
            'kelebek': 'Kelebek',
            'sirt': 'Sırt',
            'kurbağa': 'Kurbağa',
            'karışık': 'Karışık'
          }[stroke?.trim()] || stroke;
          
          return `
            <tr class="${rowClass}">
              <td>${displayStroke}</td>
              <td>${distance}m</td>
              <td>${event.time || '-'}</td>
              <td>${event.points || 0}</td>
              <td>${idx + 1}</td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
  
  // Create tiebreaker info
  const tiebreaker = athlete.tiebreaker || {};
  const tiebreakerHTML = `
    <div class="tiebreaker-info">
      <div>
        <strong>Top 3:</strong>
        <span>${tiebreaker.top3 || 0}</span>
      </div>
      <div>
        <strong>Top 4:</strong>
        <span>${tiebreaker.top4 || 0}</span>
      </div>
      <div>
        <strong>Top 5:</strong>
        <span>${tiebreaker.top5 || 0}</span>
      </div>
      <div>
        <strong>Top 6:</strong>
        <span>${tiebreaker.top6 || 0}</span>
      </div>
    </div>
  `;
  
  // Create selection info
  const selectionHTML = `
    <div class="selection-info">
      <div>
        <strong>Seçim Durumu:</strong>
        <span class="selection-badge" data-status="${getSelectionBadgeStatus(athlete.selection_status)}">
          ${athlete.selection_slot}
        </span>
      </div>
      <div>
        <strong>Bölge:</strong>
        <span>${athlete.region || '-'}</span>
      </div>
      ${athlete.multinations ? '<div><strong>⭐ Multinations</strong></div>' : ''}
    </div>
  `;
  
  return racesHTML + tiebreakerHTML + selectionHTML;
}
```

- [ ] **Step 2: Add toggleDetailRow function**

```javascript
function toggleDetailRow(athleteId) {
  const detailRow = document.querySelector(`.detail-row[data-athlete-id="${athleteId}"]`);
  if (!detailRow) return;
  
  // Toggle visibility
  const isVisible = detailRow.classList.contains('visible');
  
  if (!isVisible) {
    // Expanding - populate detail content
    const row = document.querySelector(`.athlete-row[data-athlete-id="${athleteId}"]`);
    const athleteData = window.athletesData?.find(a => a.id == athleteId);
    
    if (athleteData) {
      const contentDiv = detailRow.querySelector('.detail-content');
      contentDiv.innerHTML = populateDetailRow(athleteData);
    }
    
    detailRow.classList.add('visible');
  } else {
    // Collapsing
    detailRow.classList.remove('visible');
  }
}
```

- [ ] **Step 3: Store athletes data globally for detail row access**

When fetching athletes from API, store in global:

```javascript
let window.athletesData = [];

// In fetch callback:
fetch('/api/ranking?...')
  .then(r => r.json())
  .then(data => {
    window.athletesData = data.athletes;
    renderAthletes(data.athletes);
  });
```

- [ ] **Step 4: Test detail row expansion**

Click expand button on an athlete row. Verify:
- Detail row slides open
- Races table appears with correct data
- Races sorted by points (descending)
- Top 3 races have yellow background
- Tiebreaker sums show correctly
- Selection info displays
- Click again → collapses

- [ ] **Step 5: Commit detail row implementation**

```bash
git add panel/app.js
git commit -m "feat: implement detail row with races table, tiebreaker, and selection info"
```

---

### Task 5: Implement Real-Time Athlete Name Search

**Files:**
- Modify: `panel/app.js`

**Interfaces:**
- Consumes: Search input from `.athlete-search` input field
- Produces: Real-time filtered athlete list; function `initializeAthleteSearch(athletes)` that attaches event listener to search input

- [ ] **Step 1: Add search initialization function**

```javascript
function initializeAthleteSearch(athletes) {
  const searchInput = document.getElementById('athlete-search');
  if (!searchInput) return;
  
  searchInput.addEventListener('input', function(e) {
    const query = e.target.value;
    renderAthletes(athletes, query);
  });
}
```

- [ ] **Step 2: Call initialization in API fetch callback**

After fetching athletes:

```javascript
fetch('/api/ranking?...')
  .then(r => r.json())
  .then(data => {
    window.athletesData = data.athletes;
    renderAthletes(data.athletes);
    initializeAthleteSearch(data.athletes);
  });
```

- [ ] **Step 3: Test real-time search**

Type athlete name in search box. Verify:
- List filters in real-time (no delay)
- Works with partial names ("Cem" → shows Cemre İnce)
- Case-insensitive ("cemre" = "CEMRE" = "Cemre")
- Turkish characters work (search "Çağrı", "İpek", etc.)
- Clear search box → full list returns
- Empty results show "No results" message

- [ ] **Step 4: Commit search functionality**

```bash
git add panel/app.js
git commit -m "feat: implement real-time athlete name search"
```

---

### Task 6: Connect Existing Filters to New Rendering

**Files:**
- Modify: `panel/app.js`

**Interfaces:**
- Consumes: Existing filter logic (birth_year, gender, leg filters)
- Produces: Updated fetch calls and rendering to work with new athlete row structure

- [ ] **Step 1: Update filter event listeners**

Find existing filter change handlers and update them to call `renderAthletes()` with new data:

```javascript
// For each filter (birth-year-filter, gender-filter, leg-filter)
document.getElementById('birth-year-filter')?.addEventListener('change', function() {
  const birthYear = this.value;
  const gender = document.getElementById('gender-filter')?.value || '';
  const leg = document.getElementById('leg-filter')?.value || 'combined';
  
  const params = new URLSearchParams();
  if (birthYear) params.append('birth_year', birthYear);
  if (gender) params.append('gender', gender);
  if (leg) params.append('leg', leg);
  
  const url = `/api/ranking${params.toString() ? '?' + params : ''}`;
  
  fetch(url)
    .then(r => r.json())
    .then(data => {
      window.athletesData = data.athletes;
      renderAthletes(data.athletes);
      initializeAthleteSearch(data.athletes);
    });
});

// Similar for gender-filter and leg-filter
document.getElementById('gender-filter')?.addEventListener('change', /* same logic */);
document.getElementById('leg-filter')?.addEventListener('change', /* same logic */);
```

- [ ] **Step 2: Test filter functionality**

Interact with each filter:
- Birth year filter → list updates, only matching birth year athletes shown
- Gender filter → list updates, correct gender athletes shown
- Leg filter → list updates, scores recalculate based on leg (Antalya/Edirne/Combined)
- Combine multiple filters → correct intersection shown

- [ ] **Step 3: Verify search still works after filtering**

Apply a filter, then type in search box. Confirm search works on filtered results.

- [ ] **Step 4: Commit filter integration**

```bash
git add panel/app.js
git commit -m "feat: connect existing filters to new athlete list rendering"
```

---

### Task 7: Test Rendering, Dark Mode, Expand, Responsive Design

**Files:**
- Test: `panel/index.html` + `panel/app.js` in browser

**Testing checklist:**

- [ ] **Step 1: Test rendering**

Open `http://localhost:8765`:
- [ ] Athletes list loads with compact row format
- [ ] Madalyas display correctly (🥇🥈🥉 or 4., 5., 6.)
- [ ] Selection badges appear with correct colors
- [ ] Multinations ⭐ badge shows when applicable
- [ ] All athlete rows visible (no layout breaks)
- [ ] No JavaScript errors in console

- [ ] **Step 2: Test dark mode**

In browser DevTools or system settings:
- [ ] Toggle system dark mode → page theme changes
- [ ] Light mode active → light colors render
- [ ] Dark mode active → dark colors render
- [ ] Text readable in both modes
- [ ] Badges visible and contrasted properly
- [ ] Yellow highlight (top-3 races) visible in both modes

- [ ] **Step 3: Test inline expand**

Click athlete rows:
- [ ] Click row → detail-row expands below
- [ ] Races table appears with correct data
- [ ] Races sorted by points (descending)
- [ ] Top 3 races highlighted yellow
- [ ] Tiebreaker sums show correctly
- [ ] Selection info visible
- [ ] Click again → detail-row collapses
- [ ] No JavaScript errors

- [ ] **Step 4: Test responsive design**

Resize browser window:
- [ ] Desktop (1920px): 5-column grid, badge visible, all info visible
- [ ] Tablet (768px): Adjust layout, badge visible but columns stack
- [ ] Mobile (375px): Single column, badge/action hidden on mobile, readable
- [ ] No horizontal scroll at any width
- [ ] Touch-friendly on mobile (buttons clickable)

- [ ] **Step 5: Test filters & search**

Interact with controls:
- [ ] Birth year filter → correct athletes shown
- [ ] Gender filter → correct athletes shown
- [ ] Leg filter → scores update, correct athletes shown
- [ ] Athlete name search → real-time filtering works
- [ ] Turkish character search works
- [ ] Combine multiple filters → correct intersection
- [ ] Clear search → full list returns

- [ ] **Step 6: Test edge cases**

- [ ] No athletes match filter → "No results" message shown
- [ ] Long athlete name → doesn't break layout
- [ ] Long club name → doesn't break layout
- [ ] Athlete with few races → detail row shows correctly
- [ ] Athlete with many races → table scrolls, readable

Document any issues found. If minor CSS tweaks needed (spacing, colors, responsive breakpoints), update `styles.css` inline.

- [ ] **Step 7: Create testing summary**

All tests pass? Commit final state:

```bash
git add panel/index.html panel/app.js panel/styles.css
git commit -m "test: verify rendering, dark mode, expand, responsive, filters"
```

---

### Task 8: Final Integration & Browser Testing

**Files:**
- Test: Full system in browser

**Checklist:**

- [ ] **Step 1: Start server**

```bash
python panel/serve.py
```

Verify server running on `localhost:8765`.

- [ ] **Step 2: Open in browser**

Open `http://localhost:8765` in Chrome/Firefox/Safari.

- [ ] **Step 3: Full flow test**

1. Page loads → athletes list visible
2. Apply birth year filter (2011) → list updates, only 2011 athletes
3. Apply gender filter (F) → list updates, only female 2011 athletes
4. Search "Cemre" → filters to Cemre İnce
5. Click Cemre's expand button → detail row opens, races shown, sorted by points
6. Close detail row → collapses
7. Clear search → full filtered list returns
8. Toggle leg filter (Antalya/Edirne/Combined) → scores update
9. In DevTools, toggle system dark mode → page theme changes
10. Resize to mobile → responsive layout works, readable

- [ ] **Step 4: Verify no console errors**

Open DevTools → Console tab. Confirm no red errors.

- [ ] **Step 5: Test on different browsers**

If possible, test on:
- Chrome
- Firefox
- Safari
- Mobile browser (iOS Safari or Chrome Android)

- [ ] **Step 6: Commit integration**

```bash
git add -A
git commit -m "feat: complete UI redesign - compact list, dark mode, inline expand, search"
```

---

### Task 9: Performance & Polish (Optional)

**Files:**
- Modify: `panel/app.js`, `panel/styles.css`

**Optional improvements:**

- [ ] **Step 1: Lazy load detail rows** (if many athletes)

Only render detail-row content when expanded, not for all rows upfront.

- [ ] **Step 2: Add loading indicator**

Show loading message while fetching from API.

- [ ] **Step 3: Optimize CSS transitions**

Ensure smooth animations when expanding/collapsing.

- [ ] **Step 4: Add accessibility attributes**

Ensure:
- ARIA labels on buttons (`aria-label`)
- Semantic HTML (use `<button>` not `<div onclick>`)
- Keyboard navigation works (Tab through rows)

- [ ] **Step 5: Final polish**

Review styling, spacing, colors. Tweak minor issues if needed.

- [ ] **Step 6: Commit polish**

```bash
git add panel/app.js panel/styles.css
git commit -m "polish: add loading indicator, accessibility, optimize animations"
```

---

## Summary

**Goal achieved:** Complete UI redesign from table to compact DIV-based list with:
- ✅ Responsive grid layout (desktop/tablet/mobile)
- ✅ Dark mode with system preference detection
- ✅ Inline expandable detail rows (races table, tiebreaker, selection info)
- ✅ Real-time athlete name search
- ✅ Madalya badges (🥇🥈🥉)
- ✅ Selection badges with colors (TR/BÖLGE/MULTINATIONS)
- ✅ Preserved existing filters (birth_year, gender, leg)
- ✅ No backend changes

**Files modified:** `panel/index.html`, `panel/styles.css`, `panel/app.js`

**Testing:** Manual browser testing covers rendering, dark mode, inline expand, responsive, filters, search, edge cases.

**Rollback:** If issues arise, revert last commits to restore old table-based UI. No database changes, so safe to revert.

---

**Plan Status:** Ready for implementation
