# Task 7: Regional Rankings Panel

## Context
This task adds a separate regional rankings view showing athletes grouped by region (İstanbul, Marmara, Ege, etc.) with region-specific quotas applied.

## Requirements

**Files:**
- Modify: `panel/index.html` (add regional section and tabs)
- Modify: `panel/styles.css` (add regional panel styles)
- Modify: `panel/serve.py` (add `/api/regional` endpoint)

**Interfaces:**
- Consumes: Existing database queries and athlete data
- Produces: `GET /api/regional?region=1-6&leg=combined` endpoint + UI panel with region tabs

## Implementation Steps

### Step 1: Add regional rankings section to HTML
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

### Step 2: Add CSS for regional panel
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

### Step 3: Add regional ranking endpoint to serve.py
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

### Step 4: Add route to do_GET()
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

### Step 5: Add JavaScript to handle regional tabs
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

### Step 6: Test regional rankings in browser
1. Click "Bölge Sıralamaları" to show section
2. Click "İstanbul" tab → see Istanbul athletes ranked
3. Click other regions → different athletes appear
4. Test with different legs (Antalya/Edirne/Combined)
5. Verify selection status (TR, BÖLGE, -) reflects region quotas

Expected: Separate regional rankings showing correct athletes and scores per region.

## Global Constraints
- UTF-8 encoding
- Turkish characters display correctly
- Region IDs: 1=İstanbul, 2=Marmara, 3=Ege, 4=İç Anadolu, 5=Karadeniz, 6=Güneydoğu
- Selection quotas: Region 1 (İstanbul) has higher limits than others

## Deliverables
- ✅ Regional rankings panel visible and functional
- ✅ All 6 region tabs work and display correct athletes
- ✅ Leg filtering works with regional rankings
- ✅ Tests pass: different regions show different athletes
- ✅ Git commit with all changes

## Report File
Write detailed report to: `C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme\.superpowers\sdd\task4-9-completion\task-7-report.md`

Include:
- Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED
- Browser testing results (region tabs, leg filtering)
- Commits made
- Any issues or concerns
