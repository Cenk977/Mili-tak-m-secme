# Federasyon Modul — Milli Takım Seçimleri

## Genel Bakış

Federasyon module'ü milli takım seçim sisteminin puanlama, ranking, ve seçim kararı verme işlemlerini yönetir.

## Bileşenler

### db_fed.py — Database Layer
- `upsert_fed_results()`: Sporcu sonuçlarını kaydetme
- `update_athlete_selection()`: Seçim durumunu güncelleme
- `get_selected_athletes()`: Seçilmiş sporcuları sorgulama
- `migrate_add_selection_columns()`: Veritabanı şeması güncelleme

### scorer.py — Puanlama Motoru
- `score_event()`: Tek branş için puan hesaplama (0-9, 8 yok)
- `score_athlete_row()`: Sporcu başına tüm branş puanları
- `compute_ranking_key()`: Tiebreaker tuşu
- `qualifies_minimum()`: Baraj kontrol (min 7 puan)

### ranker.py — Sıralama Motoru
- `rank_all()`: Tüm sporcuları sırala, seçim kararı ver
- Kuota kontrolü: TR, BÖLGE per region, BARAJ_YOK
- Slot labeling: TR-1, B1-1, B2-1, etc.

### pipeline.py — Orkestrasyonu
- `MiltiTakimPipeline.process()`: End-to-end LXF→selection
  1. Parse LXF
  2. Score athletes
  3. Rank athletes
  4. Save to database
  5. Return response

## Kullanım

### API: MiltiTakimPipeline.process()

```python
from federasyon.pipeline import MiltiTakimPipeline

pipeline = MiltiTakimPipeline()
result = pipeline.process('/path/to/antalya.lxf')

# result keys: success, message, selected_tr, selected_bolge, 
#              baraj_yok_count, total_athletes, summary
```

### Database: Selected Athletes

```python
from federasyon.db_fed import get_selected_athletes

# Tüm seçilmiş sporcuları al
all_selected = get_selected_athletes(selected='TR')

# Doğum yılına göre filtrele
selected_2013 = get_selected_athletes(birth_year=2013, selected='BÖLGE')
```

## Kurallar

### Seçim Kategorileri
- **TR**: Türkiye seçimi (tüm ülkeden ilk 20F+10M, vb.)
- **BÖLGE**: Bölge seçimi (bölge başına kota)
- **BARAJ_YOK**: Barajı geçememişler (top3 < 7 puan)
- **-**: Seçilmemiş (BÖLGE kotası dolu)

### Puanlama Sistemi
- Time thresholds: TABLES[birth_year][gender][(stroke, distance)]
- Puan aralığı: 0 (baraj yok), 1-7, 9 (en iyi)
- Top 3 seçim: En iyi 3 branş toplanır (max 1 × 50m)
- Tiebreaker: Kümülatif toplamlar (-top3, -top4, -top5, -top6)

## Testing

```bash
# Unit tests
pytest federasyon/tests/ -v

# Integration tests
pytest tests/test_upload_endpoint.py -v

# Coverage
pytest --cov=federasyon
```

## Errors & Troubleshooting

| Hata | Sebep | Çözüm |
|------|-------|-------|
| LXF Parse Error | Hatalı XML | LXF dosya formatını kontrol et |
| Unknown Event | Branş TABLES'te yok | scoring_tables.py güncelle |
| Missing birth_year | Sporcu yaşı bulunamadı | LXF dosyada birth_year alanı kontrol et |
| Database Error | FK constraint, disk dolu | Disk alanını kontrol, migration çalıştır |

## Yapı

```
federasyon/
├── db_fed.py           # Database CRUD
├── scorer.py           # Puanlama motoru
├── ranker.py           # Ranking ve seçim
├── pipeline.py         # Orkestrasyonu
├── scoring_tables.py   # BARAJ thresholds
└── tests/
    └── test_*.py       # Unit tests
```
