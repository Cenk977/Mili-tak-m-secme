# Task 6: Leg Filter UI Buttons

## Context
This task adds UI buttons to toggle between Antalya, Edirne, and Combined (birleşik) views, updating the athlete list in real-time with the selected leg's scores.

## Requirements

**Files:**
- Modify: `panel/index.html` (add buttons, update loadRankings)
- Modify: `panel/styles.css` (add button styles)

**Interfaces:**
- Consumes: Existing `GET /api/ranking?leg=antalya|edirne|combined` endpoint
- Produces: UI buttons that toggle active leg, update athlete list dynamically

## Implementation Steps

### Step 1: Add leg filter buttons to HTML
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

### Step 2: Add CSS for buttons
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

### Step 3: Update loadRankings function
Modify `loadRankings()` in `panel/index.html`:
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

### Step 4: Add leg button click handlers
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

### Step 5: Test leg filtering in browser
1. Upload both Antalya and Edirne files (or test one at a time)
2. Click "Antalya" button → athletes show Antalya scores
3. Click "Edirne" button → athletes show Edirne scores
4. Click "Birleşik" (combined) → athletes show combined scores
5. Verify dashboard list updates with correct top3 scores each time

Expected: Different `display_top3` values for each leg, selection status updates accordingly.

## Global Constraints
- UTF-8 encoding
- Turkish characters must display correctly
- Responsive design (mobile, tablet, desktop)
- Integration with existing filter system

## Deliverables
- ✅ Leg filter buttons visible and functional
- ✅ Each leg toggle updates athlete list in real-time
- ✅ Button active state reflects current selection
- ✅ Tests pass: all three legs display correct data
- ✅ Git commit with changes

## Report File
Write detailed report to: `C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme\.superpowers\sdd\task4-9-completion\task-6-report.md`

Include:
- Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED
- Browser testing results (all three legs tested)
- Commits made
- Any issues or concerns
