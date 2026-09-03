# Task 7: Update Frontend — Athlete Profile Display

**Files:**
- Modify: `panel/index.html`

**Interfaces:**
- **Consumes:** Updated API response with 10 new yíldízlar fields from Task 6
- **Produces:** Athlete profile page displaying yíldízlar selections and coach status

**Steps:**

- [ ] **Step 1: Locate athlete profile section in `index.html`**

Find the HTML section where federation selections are currently displayed (e.g., "Seçilim: TR / BÖLGE / MULTINATIONS").

- [ ] **Step 2: Add yíldízlar display HTML section**

After the federation selections section, add:

```html
<div class="yildizlar-section">
  <h3>Yıldızlar Milli Takımları</h3>
  
  <div class="yildiz-item">
    <strong>Multinations Yıldızlar:</strong>
    <span id="yildiz-multi-status">-</span>
    <span id="yildiz-multi-coach">-</span>
  </div>
  
  <div class="yildiz-item">
    <strong>Comen Cup:</strong>
    <div>
      <span>Aralık: <span id="yildiz-comen-aralik">-</span> | 
      <span id="yildiz-comen-aralik-coach">-</span></span>
    </div>
    <div>
      <span>Nisan: <span id="yildiz-comen-nisan">-</span> | 
      <span id="yildiz-comen-nisan-coach">-</span></span>
    </div>
  </div>
  
  <div class="yildiz-item">
    <strong>Central European Countries Meet:</strong>
    <div>
      <span>Aralık: <span id="yildiz-central-aralik">-</span> | 
      <span id="yildiz-central-aralik-coach">-</span></span>
    </div>
    <div>
      <span>Nisan: <span id="yildiz-central-nisan">-</span> | 
      <span id="yildiz-central-nisan-coach">-</span></span>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Add JavaScript function to populate yíldízlar fields**

In the `<script>` section, add this function:

```javascript
function populateYildizarFields(athlete) {
  document.getElementById('yildiz-multi-status').textContent = 
    athlete.selected_yildiz_multinations ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-multi-coach').textContent = 
    athlete.coach_called_yildiz_multinations ? 'Antrenör barajı geçti' : '-';
  
  document.getElementById('yildiz-comen-aralik').textContent = 
    athlete.selected_yildiz_comen_cup_aralik ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-comen-aralik-coach').textContent = 
    athlete.coach_called_yildiz_comen_cup_aralik ? 'Antrenör barajı geçti' : '-';
  
  document.getElementById('yildiz-comen-nisan').textContent = 
    athlete.selected_yildiz_comen_cup_nisan ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-comen-nisan-coach').textContent = 
    athlete.coach_called_yildiz_comen_cup_nisan ? 'Antrenör barajı geçti' : '-';
  
  document.getElementById('yildiz-central-aralik').textContent = 
    athlete.selected_yildiz_central_europe_aralik ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-central-aralik-coach').textContent = 
    athlete.coach_called_yildiz_central_europe_aralik ? 'Antrenör barajı geçti' : '-';
  
  document.getElementById('yildiz-central-nisan').textContent = 
    athlete.selected_yildiz_central_europe_nisan ? 'Seçildi ✓' : '-';
  document.getElementById('yildiz-central-nisan-coach').textContent = 
    athlete.coach_called_yildiz_central_europe_nisan ? 'Antrenör barajı geçti' : '-';
}
```

Call this function immediately after the athlete data is received (e.g., in the existing code that displays the athlete profile, after fetching from `/api/ranking`).

- [ ] **Step 4: Add CSS styling for yíldízlar section**

In the `<style>` section (or inline CSS), add:

```css
.yildizlar-section {
  margin-top: 20px;
  padding: 15px;
  border-top: 1px solid #ccc;
  background: #f9f9f9;
}

.yildiz-item {
  margin: 10px 0;
  font-size: 14px;
}

.yildiz-item strong {
  display: block;
  margin-bottom: 5px;
}
```

- [ ] **Step 5: Test in browser**

1. Start the server: `python panel/serve.py`
2. Open http://localhost:8765
3. Click on an athlete to view their profile
4. Scroll down to "Yıldızlar Milli Takımları" section
5. Verify the section displays with all three competitions and two dates (where applicable)

Expected: 
- Section visible with proper styling
- Fields show "-" or selection status ("Seçildi ✓")
- Coach fields show "-" or "Antrenör barajı geçti"

- [ ] **Step 6: Commit**

```bash
git add panel/index.html
git commit -m "ui: add yildizlar selections display to athlete profile"
```
