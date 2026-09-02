# Phase 2 Tasarımı: API + City/Region Mapping Entegrasyonu

**Tarih:** 2026-08-31  
**Proje:** Milli Takım Seçme Sistemi  
**Faz:** 2 (Kritik)  
**Durum:** Design Approved

---

## 1. Genel Bakış

Phase 2'nin amacı, Phase 1'deki LXF parser'ı tamamlamaktır:
- ✅ Sporcu parsing ve puanlama (Phase 1)
- 🚀 **City/Region mapping** (Phase 2)
- 🚀 **API endpoint** (Phase 2)
- 🚀 **HTTP panel** (Phase 2)
- ✅ **Database** (Phase 2)

**Sonuç:** Antalya ve Edirne LXF dosyalarını yükleyebilen, seçilmiş sporcuları API'dan dönen, çalışan sistem.

---

## 2. Mimari Genel Görünüm

```
LXF Upload
    ↓
modules/lxf_parser.py
  ├─ XML parse
  └─ Athlete extract
    ↓
modules/m4_mapping.py
  ├─ Excel load (cache)
  └─ Club → City/Region lookup
    ↓
database/db.py
  ├─ Athletes table insert
  └─ Scoring/Ranking update
    ↓
panel/serve.py
  ├─ GET /api/ranking?birth_year=2013&gender=F → JSON
  ├─ POST /upload → Process LXF
  └─ GET / → Dashboard HTML
    ↓
data/results/
  ├─ results.json
  ├─ results_inline.js
  └─ rankings_*.json
```

---

## 3. Bileşenler

### 3.1 Database Layer (`database/db.py`)

**Tablo: `athletes`**
```sql
CREATE TABLE athletes (
    athlete_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    birth_year INTEGER,
    gender TEXT,              -- F / M
    club_name TEXT,
    city TEXT,                -- Mapping'den
    region INTEGER,           -- Mapping'den (1-6)
    best_score INTEGER,
    selected BOOLEAN,
    selection_type TEXT,      -- TR / B1 / Bölge / NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**CRUD İşlemler:**
```python
def insert_athlete(athlete_dict) -> bool
def get_athletes_by_filter(birth_year, gender) -> List[Dict]
def update_athlete_ranking(athlete_id, score, selected, type) -> bool
def clear_athletes() -> bool
def get_connection() -> sqlite3.Connection
```

**Başlangıç:**
```python
def init_db():
    """Veritabanı kurulumu, migration vb."""
    if not Path(DB_PATH).exists():
        create_tables()
    apply_migrations()
```

### 3.2 Mapping Modülü (`modules/m4_mapping.py`)

**Fonksiyon: `lookup_club(club_name: str) -> ClubInfo | None`**

```python
from typing import TypedDict
import openpyxl
from config import MAPPING_EXCEL_PATH, MAPPING_SHEET_NAME

class ClubInfo(TypedDict):
    city: str
    region: int
    club_canonical: str

_mapping_cache = None

def load_mapping():
    """Excel'i bir kez yükle, cache'e koy"""
    global _mapping_cache
    if _mapping_cache is not None:
        return
    
    _mapping_cache = {}
    wb = openpyxl.load_workbook(MAPPING_EXCEL_PATH, read_only=True, data_only=True)
    ws = wb[MAPPING_SHEET_NAME]
    
    # Row 5'ten başla (başlık sonrası)
    # Sütun: A=kulüp_alt, C=kulüp_kanonik, E=şehir, G=bölge
    for row in ws.iter_rows(min_row=5, values_only=True):
        if not row or len(row) < 7:
            continue
            
        club_name = row[0] or row[2]  # A veya C
        city = row[4]                  # E
        region = row[6]                # G
        
        if club_name and city and region:
            try:
                key = str(club_name).strip().upper()
                _mapping_cache[key] = {
                    'city': str(city).strip(),
                    'region': int(region),
                    'club_canonical': str(club_name).strip()
                }
            except (ValueError, TypeError):
                continue
    
    wb.close()

def lookup_club(club_name: str) -> ClubInfo | None:
    """Kulüp adına göre şehir/bölge döner"""
    if not club_name:
        return None
    
    load_mapping()
    key = str(club_name).strip().upper()
    return _mapping_cache.get(key)

def get_missing_clubs(athletes: List[Dict]) -> Set[str]:
    """Bulunamayan kulüpler (loglama için)"""
    missing = set()
    for athlete in athletes:
        if not lookup_club(athlete.get('club_name')):
            missing.add(athlete.get('club_name', 'Unknown'))
    return missing
```

**Davranış:**
- İlk çağrıda Excel oku, cache'e koy (performans)
- Sonraki çağrılar cache'den gelir
- Bulunamayan kulüpler → `city='Unknown'`, `region=0`

### 3.3 Parser Güncelleme (`modules/lxf_parser.py`)

**Değişiklik: `parse_lxf_file()` fonksiyonunda**

```python
from modules.m4_mapping import lookup_club

def parse_lxf_file(file_path: str) -> tuple[List[Dict], List[Dict]]:
    """
    Parse LXF file and extract athletes and results.
    
    Ekleme: Her athlete'e city/region eklenir
    """
    athletes_list = []
    results_list = []
    
    # ... mevcut XML parse kodu ...
    
    for athlete_elem in athlete_elements:
        athlete = {
            'athlete_id': athlete_elem.get('athleteid'),
            'firstname': athlete_elem.get('firstname'),
            'lastname': athlete_elem.get('lastname'),
            'birthdate': athlete_elem.get('birthdate'),
            'gender': athlete_elem.get('gender'),
            'club_id': club_elem.get('clubid') if club_elem else None,
            'club_name': club_elem.get('clubname') if club_elem else 'Unknown',
            # ← YENİ: City/Region mapping
            'city': 'Unknown',
            'region': 0,
        }
        
        # City/Region lookup
        if athlete['club_name'] and athlete['club_name'] != 'Unknown':
            mapping = lookup_club(athlete['club_name'])
            if mapping:
                athlete['city'] = mapping['city']
                athlete['region'] = mapping['region']
        
        athletes_list.append(athlete)
        
        # ... results parsing ...
    
    return athletes_list, results_list
```

### 3.4 HTTP Panel (`panel/serve.py`)

**Endpoints:**

1. **`GET /`** — Dashboard HTML
   - Upload form + ranking tablosu

2. **`POST /upload`** — LXF yükleme
   ```
   Form: file (multipart/form-data)
   
   İşlem:
     1. Dosya temp'e kaydet
     2. parse_lxf_file() çağır
     3. get_missing_clubs() kontrol et (uyarı loglama)
     4. DB'ye insert_athlete() çağrı
     5. Athletes tablosunu re-rank (scoring/selection)
   
   Response: { "status": "success", "count": 234, "missing_clubs": ["ABC SK"] }
   ```

3. **`GET /api/ranking`** — Rankings API
   ```
   Query params:
     - birth_year: int (default: 2013)
     - gender: str (default: tümü; F/M)
   
   Response:
   [
     {
       "athlete_id": "ATH123",
       "name": "Ayşe Yılmaz",
       "club": "Ankara BEL. SK",
       "city": "Ankara",
       "region": 4,
       "birth_year": 2013,
       "gender": "F",
       "best_score": 5,
       "selected": true,
       "selection_type": "TR"
     },
     ...
   ]
   ```

**Başlangıç:**
```python
#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from database.db import init_db, get_athletes_by_filter
from modules.lxf_parser import parse_lxf_file

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Serve index.html
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('panel/index.html', 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        
        elif self.path.startswith('/api/ranking'):
            # Parse query params
            qs = urlparse(self.path).query
            params = parse_qs(qs)
            birth_year = int(params.get('birth_year', ['2013'])[0])
            gender = params.get('gender', [None])[0]
            
            # Query DB
            athletes = get_athletes_by_filter(birth_year, gender)
            
            # Send JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(athletes, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        if self.path == '/upload':
            # Parse multipart form data
            # Read LXF file, parse, insert to DB
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

if __name__ == '__main__':
    init_db()
    server = HTTPServer(('localhost', 8765), Handler)
    print("Server running at http://localhost:8765")
    server.serve_forever()
```

### 3.5 Klasör Yapısı

**Oluşturulacaklar:**
```
mili_takim_secme/
├── data/                          ← mkdir
│   ├── antalya_millitakim_secme_sonuc.lxf    ← copy
│   ├── edirne_millitakim_secme_sonuc.lxf     ← copy
│   ├── selection.db               ← create (init_db())
│   └── results/                   ← mkdir (output)
│
├── panel/                         ← mkdir
│   ├── serve.py                   ← yeni
│   ├── index.html                 ← yeni
│   └── __init__.py
│
├── docs/superpowers/specs/        ← mkdir (this file)
```

**Güncellenenler:**
- `config.py` — MAPPING_EXCEL_PATH, MAPPING_SHEET_NAME, sütun indeksleri
- `modules/lxf_parser.py` — mapping import + lookup çağrı
- `requirements.txt` — openpyxl kütüphanesi ekle
- `.gitignore` — `data/*.db`, `data/results/*` ekle

---

## 4. Veri Akışı

### Upload Süreci
```
1. User: panel/index.html'de LXF seç
2. Panel: POST /upload → LXF dosyası
3. serve.py:
   a. Dosya temp'e kaydet
   b. parse_lxf_file(temp_file) → athletes[], results[]
   c. For each athlete:
      - lookup_club() → city, region
      - insert_athlete() → DB
   d. Update ranking scores
4. Response: { "count": 234, "missing_clubs": [...] }
5. Panel: Dashboard refresh → GET /api/ranking
6. Dashboard: Athletes tablosu güncellenir
```

### API Response Süreci
```
1. User: GET /api/ranking?birth_year=2013&gender=F
2. serve.py:
   a. Parse query params
   b. get_athletes_by_filter(2013, 'F') → DB query
   c. JSON serialize
3. Response: [{ "name": "...", "city": "...", ... }]
4. Frontend: Tabloyu render et
```

---

## 5. Testing Stratejisi

### 5.1 Test Verisi

**Antalya LXF:**
- Path: `data/antalya_millitakim_secme_sonuc.lxf`
- İçerik: ~2,888 results
- Beklenti: 
  - 2013F: 45 seçilmiş
  - 2013M: 29 seçilmiş
  - Tüm athletes city/region bilgisine sahip

**Edirne LXF:**
- Path: `data/edirne_millitakim_secme_sonuc.lxf`
- Test: Kombinasyon (her iki LXF de yüklü)

### 5.2 Test Adımları

```bash
# 1. Setup
mkdir -p data/results
cp /Desktop/antalya_millitakim_secme_sonuc.lxf data/
cp /Desktop/edirne_millitakim_secme_sonuc.lxf data/

# 2. Database init (ilk kez)
python -c "from database.db import init_db; init_db()"

# 3. Server başlat
python panel/serve.py
# → http://localhost:8765

# 4. Manual test
# a. Browser: http://localhost:8765
# b. "Dosya seç" → data/antalya_millitakim_secme_sonuc.lxf
# c. "Yükle" tıkla
# d. Response kontrol: { "status": "success", "count": ... }

# 5. API test
curl "http://localhost:8765/api/ranking?birth_year=2013&gender=F"
# → JSON array of athletes
# → city="Ankara", region=4, etc.

# 6. Database kontrol
sqlite3 data/selection.db "SELECT COUNT(*) FROM athletes WHERE selected=1"
# → ~45 (Antalya 2013F)

# 7. Edirne yükle (kombinasyon test)
# Repeat steps 4-5

# 8. JSON outputs
ls -la data/results/
# → results.json, results_inline.js, rankings_*.json
```

### 5.3 Başarı Kriterleri

- ✅ `panel/serve.py` localhost:8765'te çalışır
- ✅ LXF upload endpoint data parse eder
- ✅ Athletes DB'ye city/region ile kaydedilir
- ✅ GET /api/ranking JSON döner (seçilmiş sporcular)
- ✅ Dashboard athletes tablosunu render eder
- ✅ Antalya + Edirne kombinasyon başarıyla işlenir
- ✅ Excel mapping'de olmayan kulüpler `city='Unknown'`, `region=0` olur

---

## 6. Bağımlılıklar

### Harici Kütüphaneler
```
openpyxl>=3.0.0      # Excel okuma
```

### İç Bağımlılıklar
```
config.py            → paths, constants
modules/lxf_parser.py
modules/m4_mapping.py
database/db.py
panel/serve.py
```

### Dosya Bağımlılıkları
```
Kulüp Şehir Mapping Exceli/Kulüp Şehir Mapping.xlsx
  → m4_mapping.py'de kullanılır
  → config.MAPPING_EXCEL_PATH ile referans edilir
```

---

## 7. Not ve Kısıtlamalar

### Simplicity (KISS)
- Database sync (Excel → DB) Phase 3'e ertele
- Manual Excel güncellemeleri şimdilik kabul edilir
- Conflict resolution (duplicate athletes) Phase 3'e ertele

### Encoding
- Tüm file I/O: `encoding='utf-8'`
- JSON output: `ensure_ascii=False` (Turkish characters)

### Error Handling
- Missing clubs: Log et, `region=0` fallback
- Excel not found: Exception throw, user bildiren
- Database errors: Try-except, user feedback

### Database
- SQLite (built-in, no extra server)
- Path: `config.DB_PATH` = `data/selection.db`
- Auto-create on first run (init_db())
- `.gitignore`: `data/*.db`

---

## 8. Sonraki Aşamalar (Phase 3)

- Delete race leg endpoint
- Leg toggle (Antalya/Edirne/Combined)
- Region-specific rankings panel
- Excel export
- Database sync (Excel → DB caching)
- Conflict resolution UI

---

## Onay

- **Design:** ✅ Approved (2026-08-31)
- **Implementer:** Claude
- **Timeline:** Phase 2 (crítico) → writing-plans skill
