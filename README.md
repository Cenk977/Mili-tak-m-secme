# Milli Takım Seçme 2026 — Ulusal Takım Sporcuları Değerlendirme Sistemi

Türkiye Yüzme Federasyonu için ulusal takım sporcuları seçim sistemi. LENEX XML format yarışma sonuçlarını ayrıştırarak, Türkiye federasyonu standartlarına göre sporcuları puanlayan ve ulusal takım üyelerini seçen bir sistemdir.

## Özellikler

- **LXF Dosya Ayrıştırma**: LENEX 3.0 XML formatında yarışma sonuçlarını okur
- **Otomatik Eşleştirme**: Kulüp adlarını Excel mapping dosyası ile otomatik olarak şehir/bölgeye eşler
- **Web Arayüzü**: Dosya yükleme, sporcu sorgulama ve veritabanı yönetimi için tarayıcı tabanlı arayüz
- **REST API**: Sporcu rankings için sorgulanabilir API endpoint'i
- **SQLite Veritabanı**: Sporcu bilgilerini ve müsabaka sonuçlarını depolar
- **Türkçe Dil Desteği**: Tüm metin ve karakterler Türkçe karakter desteği ile

## Kurulum

### Gereksinimler
- Python 3.8+
- openpyxl (Excel dosya okuma)

### Paketleri Yükle
```bash
pip install openpyxl
```

### Veri Dosyalarını Hazırla

1. **LXF Dosyaları**: Yarışma sonuç dosyalarını `data/` dizinine kopyala
   ```
   data/antalya_millitakim_secme_sonuc.lxf
   data/edirne_millitakim_secme_sonuc.lxf
   ```

2. **Excel Mapping Dosyası**: Kulüp-Şehir-Bölge eşleştirme dosyasını hazırla
   ```
   Kulüp Şehir Mapping Exceli/Kulüp Şehir Mapping.xlsx
   ```
   
   Dosya yapısı:
   - Sayfa: "Kulüp-Bölge-Şehir"
   - Sütun A: Kulüp adı (alternatif)
   - Sütun C: Kulüp adı (kanonik)
   - Sütun E: Şehir adı
   - Sütun G: Bölge numarası (1-6)
   - Veri satırı 5'ten başlar

## Kullanım

### Web Arayüzü

Sunucuyu başlat:
```bash
python panel/serve.py
```

Tarayıcıda açılır: http://localhost:8765/

**Özellikler:**
- **Dosya Yükle**: LXF dosyasını sürükle-bırak veya tıkla
- **Filtrele**: Doğum yılı ve cinsiyet ile sonuçları filtrele
- **Verileri Temizle**: Veritabanını boşalt

### REST API

#### GET /api/ranking
Sporcuları sorgula (opsiyonel filtreler):

```bash
# Tüm sporcular
curl http://localhost:8765/api/ranking

# Doğum yılına göre filtrele
curl http://localhost:8765/api/ranking?birth_year=2005

# Cinsiyet ve doğum yılına göre filtrele
curl "http://localhost:8765/api/ranking?birth_year=2005&gender=M"
```

Yanıt:
```json
[
  {
    "athlete_id": "12345",
    "firstname": "Furkan",
    "lastname": "Ablak",
    "birthdate": "2005-03-15",
    "birth_year": 2005,
    "gender": "M",
    "club_name": "Rota Koleji",
    "city": "İzmir",
    "region": 3,
    "best_score": 123.45,
    "selected": true,
    "selection_type": "TR"
  }
]
```

#### POST /upload
LXF dosyası yükle (Form data):

```bash
curl -F "file=@data/antalya_millitakim_secme_sonuc.lxf" \
     http://localhost:8765/upload
```

Yanıt:
```json
{
  "status": "success",
  "count": 763,
  "missing_clubs": ["UNKNOWN CLUB"],
  "message": "Imported 763 athletes"
}
```

#### POST /clear
Veritabanını temizle:

```bash
curl -X POST http://localhost:8765/clear
```

## Proje Yapısı

```
milli_takim_secme/
├── config.py                    # Yapılandırma sabitleri
├── database/
│   ├── __init__.py
│   └── db.py                   # SQLite veritabanı işlemleri
├── modules/
│   ├── __init__.py
│   ├── lxf_parser.py           # LENEX XML ayrıştırıcı
│   └── m4_mapping.py           # Excel kulüp eşleştirme
├── panel/
│   ├── __init__.py
│   ├── serve.py                # HTTP sunucusu
│   └── index.html              # Dashboard arayüzü
├── data/
│   ├── antalya_millitakim_secme_sonuc.lxf
│   ├── edirne_millitakim_secme_sonuc.lxf
│   └── selection.db            # SQLite veritabanı
└── README.md                    # Bu dosya
```

## Veritabanı Şeması

### athletes tablosu
- athlete_id (TEXT PRIMARY KEY)
- name (TEXT)
- firstname (TEXT)
- lastname (TEXT)
- birthdate (TEXT)
- birth_year (INTEGER)
- gender (TEXT)
- club_id (TEXT)
- club_name (TEXT)
- city (TEXT, default: 'Unknown')
- region (INTEGER, default: 0)
- best_score (REAL, default: 0)
- selected (BOOLEAN, default: 0)
- selection_type (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### results tablosu
- result_id (INTEGER PRIMARY KEY)
- athlete_id (TEXT FOREIGN KEY)
- race_number (TEXT)
- race_name (TEXT)
- time (REAL)
- race_source (TEXT)
- created_at (TIMESTAMP)

### sync_log tablosu
- sync_id (INTEGER PRIMARY KEY)
- filename (TEXT)
- athlete_count (INTEGER)
- result_count (INTEGER)
- sync_date (TIMESTAMP)

## Ekip

Sistem geliştiriciler:
- Database Layer & API Design
- LXF Parser & Integration
- Excel Mapping Module
- HTTP Server & Dashboard
- Testing & Documentation

## Lisans

Türkiye Yüzme Federasyonu — 2026

## İletişim

Destek ve sorular için: [İletişim bilgisi]
