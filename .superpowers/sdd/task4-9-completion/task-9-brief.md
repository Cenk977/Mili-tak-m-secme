# Task 9: Export to Excel

## Context
This task adds Excel export functionality, allowing users to download athlete rankings as an XLSX file with proper formatting, headers, and styling.

## Requirements

**Files:**
- Create: `panel/export.py` (NEW - export logic)
- Modify: `panel/serve.py` (add export endpoint)
- Modify: `panel/index.html` (add export button)
- Modify: `requirements.txt` (add openpyxl dependency)

**Interfaces:**
- Consumes: Database athletes and rankings via API
- Produces: `GET /api/export` endpoint returning XLSX binary file + download button in UI

## Implementation Steps

### Step 1: Create export.py module

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

### Step 2: Add export endpoint to serve.py

Modify imports at top of `panel/serve.py`:
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

### Step 3: Add export route to do_GET()

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

### Step 4: Add export button to HTML

In `panel/index.html`, add button near filters:
```html
<button id="exportBtn" class="action-btn">
  📥 Excel'e İndir
</button>
```

### Step 5: Add export button CSS

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

### Step 6: Add export button handler

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

### Step 7: Update requirements.txt

Add openpyxl dependency:
```
openpyxl>=3.0.0
```

Run: `pip install -r requirements.txt`

### Step 8: Test export in browser

1. Upload test data (Antalya + Edirne)
2. Apply filters (birth_year=2013, gender=F)
3. Click "Excel'e İndir" button
4. Verify XLSX file downloads with correct:
   - Athlete names and scores
   - Selected status
   - Filtered data (only matching athletes)
   - Correct leg data

### Step 9: Test export with different legs

1. Change leg to "Antalya" → export
2. Verify XLSX shows only Antalya scores
3. Change to "Edirne" → export
4. Verify different scores
5. Change to "Birleşik" (combined) → export
6. Verify combined scores

## Global Constraints
- UTF-8 encoding
- Turkish characters must display correctly
- Response: XLSX binary file with proper headers
- Filename format: `siralama_{leg}.xlsx`
- Excel styling: blue headers, proper columns widths, borders

## Deliverables
- ✅ `panel/export.py` module created with `create_rankings_xlsx()` function
- ✅ `GET /api/export` endpoint working
- ✅ Export button in UI functional
- ✅ XLSX files generated with proper formatting
- ✅ Tests pass: files download and open correctly in Excel
- ✅ `requirements.txt` updated with openpyxl
- ✅ Git commit with all changes

## Report File
Write detailed report to: `C:\Users\PC\OneDrive - TED BURSA KOLEJİ\Masaüstü\Mili_takım_secme\.superpowers\sdd\task4-9-completion\task-9-report.md`

Include:
- Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED
- Tests performed (export different legs, verify file contents)
- XLSX file generation confirmed
- Commits made
- Any issues or concerns
