# Seçim Yarışları Gösterimi + Gençler Liste Rozetleri — Tasarım

**Tarih:** 2026-09-08
**Tip:** UI + küçük backend genişletme. Additive.

## Amaç

1. Sporcu detay panelindeki yarış tablosunda (stil/mesafe/derece), sporcunun bir milli takıma **hangi yarışta** seçildiğini kısa rozetle göstermek — kuralların karar verdiği yarışlar.
2. Sporcu liste satırında (isim/kulüp/şehir + mevcut MULTI/COMEN/... rozetleri), Gençler (Multi Gençler + Avrupa Gençler) rozetlerini de göstermek — Yıldızlar rozetleriyle **aynı stil**.

## Backend — "karar veren yarışları" API'ye çıkar

Her sporcu dict'ine, ilgili müsabakaya seçilmesini/aday olmasını sağlayan `(stil, mesafe)` listesi. Yalnız o müsabakaya seçili/aday sporcularda dolu; diğerlerinde `[]`.

| Alan | İçerik | Kaynak |
|---|---|---|
| `multinations_events` | branş birinciliği event'leri | `_select_branch_winners_core` → `_first_events` |
| `multinations_gencler_events` | branş birinciliği event'leri | aynı çekirdek |
| `comen_cup_events` | branş birinciliği event'leri (Aralık ∪ Nisan) | Comen fonksiyonlarındaki `_first_events` |
| `central_europe_events` | branş birinciliği event'leri (Aralık ∪ Nisan) | Central fonksiyonlarındaki `_first_events` |
| `avrupa_gencler_events` | **zaten var** (baraj geçilen) | — |

Uygulama:
- `_select_branch_winners_core`: `_compute_group_stats` sonucundaki `first_events`'i de sporculara yaz (`a['_first_events'] = s['first_events']`).
- `select_yildizlar_multinations`: seçili/aday sporcuya `athlete['multinations_events'] = list(athlete.get('_first_events', []))`; diğerlerine `[]`. `_first_events`'i sonda pop et.
- `select_multinations_gencler`: aynı, `multinations_gencler_events`.
- `select_yildizlar_comen_cup_aralik` **ve** `_nisan`: iki müsabaka birleşik kadro; her fonksiyon kendi `_first_events`'ini hesaplıyor. `athlete['comen_cup_events']` = iki fonksiyonun kümesel birleşimi (`_nisan` çalışırken `_aralik`'in yazdığına ekle: `set(mevcut) | set(yeni)` → sıralı liste). Seçili değilse `[]`.
- `select_yildizlar_central_europe_aralik` **ve** `_nisan`: aynı desen, `central_europe_events`.
- Event'ler `(stroke, distance)` tuple; pop'lanmadan önce public alana kopyalanır.

## Backend — serve.py

`/api/ranking` yanıt sözlüğüne (mevcut `selected_yildiz_*` / `*_gencler` satırlarının yanına), JSON-uyumlu biçimde:

```python
'multinations_events': [list(e) for e in athlete.get('multinations_events', [])],
'comen_cup_events': [list(e) for e in athlete.get('comen_cup_events', [])],
'central_europe_events': [list(e) for e in athlete.get('central_europe_events', [])],
'multinations_gencler_events': [list(e) for e in athlete.get('multinations_gencler_events', [])],
# avrupa_gencler_event_count zaten var; ek olarak:
'avrupa_gencler_events': [list(e) for e in athlete.get('avrupa_gencler_events', [])],
```

(`[[stil, mesafe], ...]` — ör. `[["Serbest", 50], ["Kelebek", 100]]`.)

## Frontend — panel/index.html

### 1. Yarış tablosu rozetleri (`renderEventsTable`)

`renderEventsTable(events, title)` → `renderEventsTable(events, title, eventBadges)` imzasına genişlet.
`eventBadges`: `{ "Serbest|50": ["Multi", "Avrupa Gençler"], ... }` — anahtar `stroke + '|' + distance`.

`showAthleteDetail` içinde, tablo çağrılarından önce bir kez kur:

```javascript
const badgeMap = {};
const addBadges = (arr, label) => (arr || []).forEach(([s, d]) => {
    const k = s + '|' + d;
    (badgeMap[k] = badgeMap[k] || []).push(label);
});
addBadges(athlete.multinations_events, 'Multi');
addBadges(athlete.comen_cup_events, 'Comen');
addBadges(athlete.central_europe_events, 'Central');
addBadges(athlete.multinations_gencler_events, 'Multi Gençler');
addBadges(athlete.avrupa_gencler_events, 'Avrupa Gençler');
```

`renderEventsTable`'ın satır döngüsünde, derece hücresinden sonra:

```javascript
const bs = (eventBadges && eventBadges[race.stroke + '|' + race.distance]) || [];
const badgeHtml = bs.map(b =>
    `<span style="display:inline-block;margin-left:4px;background:#eef;border:1px solid #99c;color:#334;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:600;">🏅 ${b}</span>`
).join('');
```

Bu `badgeHtml`'i derece `<td>`'sinin içine ekle (ayrı sütun değil, yanına).

Aynı `badgeMap` her iki tabloya da (Antalya + Edirne) geçirilir; hangi tabloda o yarış varsa orada görünür.

### 2. Liste satırı Gençler rozetleri (`renderAthletes`)

Mevcut badge-strip'te (grep `MULTI-ADAY` — **2 render bloğu var, ikisine de**), `FED.KARMA` rozetinden önce, Yıldızlar rozetleriyle aynı inline-style deseninde:

```javascript
${athlete.selected_multinations_gencler ? '<span style="display:inline-block;margin-left:4px;background:#ad1457;color:white;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:600;">MULTI-G</span>' : ''}${athlete.candidate_multinations_gencler ? '<span style="display:inline-block;margin-left:4px;background:transparent;color:#ad1457;border:1px solid #ad1457;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;" title="Madde 5 kota kırpması - aday">MULTI-G ADAY</span>' : ''}${athlete.selected_avrupa_gencler ? '<span style="display:inline-block;margin-left:4px;background:#00695c;color:white;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:600;">AVR-G</span>' : ''}${athlete.candidate_relay_avrupa_gencler && !athlete.selected_avrupa_gencler ? '<span style="display:inline-block;margin-left:4px;background:transparent;color:#00695c;border:1px dashed #00695c;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;">AVR-G BAYRAK</span>' : ''}
```

Leg filtresine bağlama YOK — Gençler seçimi leg'e göre değişmiyor (Multi Gençler hep Antalya, Avrupa hep combined). Rozetler her leg görünümünde aynı.

## Test (TDD)

- `test_secim_events_exposed.py`: Multi/Comen/Central Yıldızlar + Multi Gençler için seçili sporcuda ilgili `*_events` dolu ve **yalnızca gerçekten yüzülen (stroke,distance)** içeriyor; seçili olmayanda `[]`. Comen/Central birleşik: Aralık'ta kazandığı + Nisan'da kazandığı event'lerin birleşimi.
- `_select_branch_winners_core` artık `_first_events` set ediyor: mevcut `test_yildizlar_ranker_core.py`'ye ekle.
- serve.py: `/api/ranking` yanıtında yeni 5 alan var, `[[str,int],...]` biçiminde (`panel/test_serve_upload.py`).
- Yıldızlar seçim sonuçları (kim seçildi) DEĞİŞMEDİ — mevcut suite regresyon kanıtı.
- Frontend: test yok; `python -m pytest -q` değişmez + statik grep + canlı smoke (`curl /api/ranking` alanları içeriyor).

## Kabuller

- Comen 4+ kuralıyla 2. olarak davet edilen sporcunun (`second_adds`) `comen_cup_events`'i boş kalır (branş birinciliği yok) — deferred minor, bu turda ele alınmıyor.
- Rozet renkleri: Multi Gençler `#ad1457` (koyu pembe, Multi Yıldızlar `#c2185b`'den ayrık), Avrupa Gençler `#00695c` (teal). Yıldızlar stiliyle aynı boyut/şekil.
