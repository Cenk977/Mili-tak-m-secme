# Gençler Milli Takım Seçimleri — Tasarım

**Tarih:** 2026-09-07
**Kaynak kural belgesi:** `2026-GENCLER-MILLI-TAKIM-SECILME-KRITERLERI.pdf` (TYF)
**Kapsam:** Multinations Gençler + Avrupa Gençler. (Gençler Alternatif ve Dakar bu turda YOK.)

## Amaç

Mevcut Yıldızlar (2011-2013) seçim sistemine, Gençler yaş grubu için iki yeni
milli takım seçimi eklemek. **Tamamen additive**: mevcut Federasyon Karması ve
Yıldızlar (Multi/Comen/Central) çıktıları değişmez, çapraz dışlama yok.

## Kurallar (PDF özeti)

### Multinations Gençler
- **Yaş:** 2008-2009-2010 K-E
- **Seçme yarışı:** 20-22 Aralık 2025 (= elimizdeki `antalya` LXF)
- **Seçim:** "her branş ve mesafede en iyi dereceye sahip sporcular" = branş
  birincileri. Kota **10 K + 10 E**.
  - Madde 4: branş birincisi < kota → 2./3.lük sahiplerinden takımı olumlu
    etkileyecekler **davet edilebilir** (aday, otomatik seçilmez).
  - Madde 5: branş birincisi > kota → 2./3.lüklere bakarak federasyon **10'a
    indirir**.
  - Madde 3: ara dereceler sayılmaz.
- **→ Multinations Yıldızlar ile algoritma birebir aynı.** Fark: yaş penceresi
  + antrenör baraj tablosu.
- Antrenör barajı: PDF s.3 (tek sütun, K/E). `coach_called` bayrağı için.

### Avrupa Gençler
- **Yaş:** 2008-2009-2010-2011-2012 K-E
- **Seçme yarışı:** 1 Ekim 2025 – 23 Mayıs 2026 (çok sayıda ulusal/uluslararası
  müsabaka). **Elimizde yalnızca Aralık + Nisan TYF müsabakaları var → kısmi
  hesap.**
- **Seçim:** "kendi branş ve mesafesindeki **SPORCU BARAJI**'nı geçen sporcular
  yarışma kotasına göre kadroya davet edilir."
  - **Kota yok sayılır** (kullanıcı kararı): SPORCU BARAJI'nı geçen HER sporcu
    `kesin`. Federasyon kotayla kendi kırpar, tahmin edilmez.
  - **Baraj eşitliği geçer:** yüzülen süre baraj süresine **eşit veya daha
    hızlı** ise baraj geçilmiş sayılır (`<=`).
  - Madde 3: ara dereceler sayılmaz (pipeline zaten event başına en iyi
    dereceyi tutuyor).
- Antrenör barajı: PDF s.5, ayrı ve daha sıkı sütun. `coach_called` için.
- Bayrak: PDF "gerekli durumlarda TYF davet eder" — deterministik değil;
  mevcut `_relay_candidate_ids` sezgiseli yumuşak ipucu olarak uygulanır.

## Mimari

### Yeni dosyalar

**`federasyon/gencler_barajlari.py`**
- `MULTI_GENCLER_ANTRENOR` : `{(stroke_tr, dist): {"M": "MM:SS.ss"|None, "F": ...}}`
- `AVRUPA_GENCLER_SPORCU`   : aynı biçim (sporcu barajı)
- `AVRUPA_GENCLER_ANTRENOR` : aynı biçim (antrenör barajı)
- `check_baraj(table, stroke_tr, dist, gender, time_str) -> bool`
  - `parse_time()` ile saniyeye çevirip `<=` karşılaştırır (string compare DEĞİL).
  - Tablo/gender'da baraj yoksa `False`.
- **Türkçe branş adları** kullanılır (`"Serbest"`, `"Sırtüstü"`, `"Kurbağalama"`,
  `"Kelebek"`, `"Karışık"`) — parse edilen veriyle (`combined_events` anahtarları)
  eşleşsin diye. (Mevcut `yildizlar_*_barajlari.py` İngilizce anahtar kullandığı
  için `coach_called` fiilen hep False dönüyor — o ayrı bir latent bug, bu turda
  düzeltilmiyor ama yeni modül bu hataya düşmez.)

**`federasyon/gencler_ranker.py`**
- `from federasyon.yildizlar_ranker import (_compute_group_stats,
  _split_winners_by_quota, _relay_candidate_ids, _select_branch_winners_core,
  parse_time, YILDIZLAR_FEMALE_PROGRAM, YILDIZLAR_MALE_PROGRAM,
  RELAY_LEG_EVENTS)`
- `MULTI_GENCLER_QUOTA = 10`
- `select_multinations_gencler(athletes) -> athletes`
- `select_avrupa_gencler(athletes) -> athletes`
- `select_all_gencler(athletes) -> athletes` (ikisini sırayla çağırır)

### `federasyon/yildizlar_ranker.py` — küçük refactor

`select_yildizlar_multinations` içindeki "branş birincisi → kesin/aday/relay"
çekirdeği, saf bir yardımcıya çıkarılır:

```
_select_branch_winners_core(group, quota, event_times_key, program,
                            relay_events) -> (sel_ids, cand_ids, relay_ids)
```

- `group`: tek cinsiyetlik, yaş-filtreli sporcu listesi.
- İçinde: `_compute_group_stats` → `_first/_second/_third`, `_split_winners_by_quota`
  (madde 4/5), `_relay_candidate_ids`.
- `select_yildizlar_multinations` bunu çağıracak şekilde sadeleşir —
  **davranışı DEĞİŞMEZ**, mevcut testler (`test_yildizlar_multinations.py`,
  `test_yildizlar_quota_trim.py`) aynen geçmeli (regresyon kanıtı).
- `select_multinations_gencler` aynı çekirdeği 2008-2010 yaş + Gençler baraj +
  `_gencler` alan öneki ile çağırır.

### Alanlar (athlete dict)

Multinations Gençler:
- `selected_multinations_gencler` (bool)
- `candidate_multinations_gencler` (bool — madde 4/5 kota altı/üstü adayı)
- `candidate_relay_multinations_gencler` (bool)
- `coach_called_multinations_gencler` (bool)

Avrupa Gençler:
- `selected_avrupa_gencler` (bool — sporcu barajı geçildi)
- `avrupa_gencler_events` (list[(stroke,dist)] — barajı geçilen branşlar)
- `coach_called_avrupa_gencler` (bool — antrenör barajı geçildi)
- `candidate_relay_avrupa_gencler` (bool)

### Entegrasyon

- **`panel/serve.py`**: `/api/ranking` handler'ında `select_all_yildizlar(athletes)`
  çağrısından hemen sonra `select_all_gencler(athletes)`. `apply_selection_status_with_points`
  ÇAĞRISI ÖNCESİNDE ya da sonrasında olması fark etmez (dışlama yok) — mevcut
  yıldız çağrısıyla aynı noktaya konur. Yanıt sözlüğüne yukarıdaki alanlar eklenir
  (`athlete.get(...)` ile, mevcut `selected_yildiz_*` satırlarının yanına).
- **`panel/index.html`**: mevcut yıldız rozet/sütun desenine iki yeni öğe:
  "Multi Gençler" (kesin/aday/bayrak) ve "Avrupa Gençler" (kesin + geçtiği branş
  sayısı). Minimal; mevcut CSS sınıfları yeniden kullanılır.
- **Veri:** yeni `get_athlete_rankings` alanı GEREKMEZ — `antalya_events_time`,
  `combined_events_time`, `combined_events` zaten mevcut. Yaş filtresi Gençler
  fonksiyonlarının içinde.

## Baraj Tabloları (PDF'ten transcribe — `MM:SS.ss`)

Branş adları Türkçe. `,` ve `;` → `.` normalize edildi. `None` = o cinsiyette
yarış yok.

### Multi Gençler — Antrenör Barajı (PDF s.3)

| Branş | E | K |
|---|---|---|
| Serbest 50 | 22.84 | 25.69 |
| Serbest 100 | 50.32 | 55.75 |
| Serbest 200 | 1:50.51 | 2:01.95 |
| Serbest 400 | 3:55.85 | 4:17.82 |
| Serbest 800 | None | 8:46.98 |
| Serbest 1500 | 15:37.03 | None |
| Sırtüstü 50 | 26.05 | 29.37 |
| Sırtüstü 100 | 55.89 | 1:02.39 |
| Sırtüstü 200 | 2:02.20 | 2:15.61 |
| Kurbağalama 50 | 28.37 | 32.18 |
| Kurbağalama 100 | 1:01.87 | 1:09.63 |
| Kurbağalama 200 | 2:14.87 | 2:30.03 |
| Kelebek 50 | 24.39 | 27.31 |
| Kelebek 100 | 53.74 | 1:00.24 |
| Kelebek 200 | 2:00.41 | 2:13.57 |
| Karışık 200 | 2:02.66 | 2:16.73 |
| Karışık 400 | 4:22.60 | 4:49.67 |

### Avrupa Gençler — Sporcu Barajı / Antrenör Barajı (PDF s.5)

Biçim: `E-sporcu / E-antrenör | K-sporcu / K-antrenör`

| Branş | E sporcu | E antrenör | K sporcu | K antrenör |
|---|---|---|---|---|
| Serbest 50 | 22.84 | 22.62 | 25.81 | 25.56 |
| Serbest 100 | 50.27 | 49.83 | 56.02 | 55.49 |
| Serbest 200 | 1:50.51 | 1:49.45 | 2:01.95 | 2:01.36 |
| Serbest 400 | 3:54.15 | 3:51.88 | 4:17.20 | 4:14.72 |
| Serbest 800 | 8:07.21 | 8:02.50 | 8:45.96 | 8:40.90 |
| Serbest 1500 | 15:28.02 | 15:19.01 | 16:43.01 | 16:33.32 |
| Sırtüstü 50 | 26.10 | 25.54 | 29.31 | 29.13 |
| Sırtüstü 100 | 55.89 | 55.35 | 1:02.69 | 1:02.09 |
| Sırtüstü 200 | 2:02.20 | 2:01.03 | 2:16.26 | 2:14.95 |
| Kurbağalama 50 | 28.38 | 28.00 | 32.18 | 32.08 |
| Kurbağalama 100 | 1:02.32 | 1:01.72 | 1:10.13 | 1:09.46 |
| Kurbağalama 200 | 2:15.84 | 2:14.54 | 2:31.11 | 2:29.67 |
| Kelebek 50 | 24.25 | 24.10 | 27.29 | 27.12 |
| Kelebek 100 | 53.74 | 53.22 | 1:00.53 | 59.95 |
| Kelebek 200 | 2:00.41 | 1:59.25 | 2:14.21 | 2:12.93 |
| Karışık 200 | 2:02.66 | 2:01.48 | 2:17.39 | 2:16.07 |
| Karışık 400 | 4:22.60 | 4:20.08 | 4:51.06 | 4:48.28 |

> Not: Avrupa Gençler baraj tablosunda K için hem 800 hem 1500, E için de hem
> 800 hem 1500 var (Yıldızlar programı bunları cinsiyete göre ayırıyordu).
> Avrupa Gençler'de sporcunun yüzdüğü HER branş için baraj kontrolü yapılır;
> program filtresi kullanılmaz (baraj tablosu zaten geçerli branşları tanımlar).

## Test Planı (TDD)

### `federasyon/tests/test_gencler_barajlari.py`
- Her tabloda 17 branş, K/E sütunları parse ediliyor.
- `check_baraj`: baraj süresine **eşit** → `True`; 0.01 hızlı → `True`; 0.01
  yavaş → `False`; tanımsız branş/gender → `False`.
- `parse_time` ile `MM:SS.ss` ve `M:SS.ss` ve `MM:MM:SS.ss` doğru saniyeye
  çevriliyor.

### `federasyon/tests/test_gencler_multinations.py`
- Yaş filtresi: 2007 ve 2011 doğumlular Multi Gençler hesabına GİRMEZ; 2008-2010
  girer.
- Madde 5 kırpması: 11 branş birincisi (E) + kota 10 → en zayıf derinlikli
  ADAY olur, 10 kesin. (quota_trim testinin Gençler eşleniği.)
- Madde 4 dolgusu: 3 branş birincisi → yalnız 3 kesin, 2./3.lük adayları
  `candidate_multinations_gencler=True`.
- Alan önekleri doğru (`_multinations_gencler`, `selected_yildiz_multinations`
  DEĞİL).
- **Regresyon:** `select_yildizlar_multinations` çıktısı Gençler fonksiyonundan
  etkilenmiyor (ayrı çağrı, ayrı alanlar).

### `federasyon/tests/test_gencler_avrupa.py`
- Sporcu barajını geçen (eşit dahil) → `selected_avrupa_gencler=True`,
  `avrupa_gencler_events` o branşı içerir.
- Barajı 0.01 kaçıran → `selected_avrupa_gencler=False`.
- Yalnız antrenör barajını (daha sıkı) geçen → hem `selected` hem
  `coach_called` True (antrenör barajı sporcu barajından hızlıdır).
- Yaş 2013 ve 2007 → hesaba girmez; 2008-2012 girer.
- Kota yok: barajı geçen 15 sporcu varsa 15'i de kesin (kırpma yok).

### `federasyon/tests/test_yildizlar_ranker_refactor.py` (veya mevcut dosyaya ekle)
- `_select_branch_winners_core` saf fonksiyon: verilen grup + kota için
  beklenen (sel_ids, cand_ids) döner.

### Gerçek veriyle akıl-sağlığı (test değil, doğrulama scripti)
- Multi Gençler K/E kaç kesin? Yaş dağılımı 2008-2010 mantıklı mı?
- Avrupa Gençler kaç kesin, hangi branşlarda? (Kısmi veri notu.)

## Kabuller / Bilinen sınırlamalar

1. **Avrupa Gençler kısmi**: seçme penceresi 8 aylık ve çok müsabakalı; biz
   yalnız Aralık(Antalya)+Nisan(Edirne) TYF verisinden hesaplıyoruz. UI'da
   "kısmi — yalnızca TYF Aralık/Nisan müsabakaları" notu gösterilir.
2. **Multi Gençler resmi 2026 kadrosu elde yok** → doğrulama sınırlı; algoritma
   Yıldızlar Multi ile aynı olduğundan (o resmi kadroyla 8/8 + 10/10
   doğrulanmış) güven yüksek.
3. **Çapraz dışlama yok**: 2011-2012 bir sporcu hem Yıldızlar Comen/Central hem
   Avrupa Gençler kesin olabilir; Federasyon Karması / Yıldızlar kotalarına
   dokunulmaz.
4. **Antrenör kotası** (aynı kulüpten kaç antrenör) bu turda hesaplanmıyor —
   yalnız `coach_called` bireysel bayrağı.
5. Mevcut `yildizlar_*_barajlari.py` İngilizce-anahtar bug'ı bu turda
   düzeltilmiyor (ayrı iş).
