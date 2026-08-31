# Milli Takım Seçme Sistemi

Türkiye Yüzme Federasyonu Milli Takım seçme sistemi. Sporcu performanslarını değerlendirerek milli takım ve bölge seçimlerini yapan veri işleme sistemi.

## Özellikler

- **BARAJ Puanlama**: Türkiye'nin resmi yüzme barajlarına göre puanlama
- **Otomatik Seçim**: TR Milli Takım ve Bölge Karma seçimleri
- **Veri Normalizasyon**: Türkçe karakter desteği, OCR artifact giderme
- **Kulüp Mapping**: Kulüp → Şehir → Bölge otomatik eşleme
- **Esnek Konfigürasyon**: Manual override desteği

## Proje Yapısı

```
├── federation/          # Core scoring sistemi
│   ├── scoring_tables.py
│   ├── scorer.py
│   ├── ranker.py
│   └── db_fed.py
├── modules/            # Data processing
│   ├── m1_normalize.py
│   ├── m3_age.py
│   └── m4_mapping.py
├── database/           # Database utilities
│   └── db.py
├── data/              # Veri depolama
├── config.py          # Konfigürasyon
└── README.md
```

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

```bash
python process_antalya_karma.py
python process_edirne_karma.py
python generate_rankings_json.py
```

## Veri Formatları

### Giriş (Excel)
- Antalya: `Çıktılar/Yarış Sonuçları Çıktı/2025.12.20_cs371_Antalya_0_Lenex.xlsx`

### Giriş (CSV)
- MeetData.txt format desteği (Milli Takım seçimi için)

### Çıkış (JSON)
- `panel/results.json` - Seçilmiş sporcuların detaylı bilgileri
- `panel/results_inline.js` - Static hosting için

## Lisans

MIT
