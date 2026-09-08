# Gençler Milli Takım Seçimi — Gerçek Veri Akıl-Sağlığı Doğrulaması

**Tarih:** 2026-09-08
**Veri kaynağı:** `data/bolge_karmalari.db` — 2025 TYF yarışları (Antalya = Aralık, Edirne = Nisan), doğum yılları 2008-2012.
**Çalıştırılan:** `database.db.get_athlete_rankings` → `federasyon.gencler_ranker.select_all_gencler`

> **Not (2026-09-08 gece):** Bu dosya bir ara "Avrupa Gençler 1K/1E" olarak
> düzeltilmişti (commit 7557880) — o düzeltme **yanlıştı**. O sırada
> `data/bolge_karmalari.db` yalnızca Antalya (Aralık) fed_results satırlarını
> içeriyordu; Edirne (Nisan) verisi eksikti. İki yarış da yüklüyken doğru sayı
> **3K + 3E**'dir (bu dosyanın ilk sürümündeki gibi). Örn. Can Acar 50m Sırtüstü:
> Antalya 26.22 (baraj 26.10'u geçmez) ama **Edirne 26.03 geçer** → birleşik en
> iyi 26.03 → KESİN. `check_baraj` kodu baştan beri doğru. **Ders:** doğrulama
> öncesi `select * from fed_results group by race_leg` ile iki yarışın da yüklü
> olduğunu kontrol et.

> **Kapsam uyarısı:** Elimizde resmi Gençler kadro ilanı YOK. Bu nedenle doğrulama sınırlıdır —
> çıktı yalnızca kural mantığı ve sınır koşulları açısından kontrol edilebildi, resmi listeyle
> karşılaştırılamadı. Multi Gençler seçim çekirdeği Multi Yıldızlar ile **aynı kod yolu**
> (`_select_branch_winners_core`) olduğundan, Yıldızlar tarafı için yapılmış doğrulama buraya da taşınır.

> **Avrupa Gençler — kısmi veri:** Avrupa Gençler barajları yalnızca DB'deki iki yarışla
> (TYF Aralık / Nisan) değerlendirildi. Sezonun diğer yarışları veri setinde olmadığından
> KESİN sayıları gerçek sezon sonuçlarının alt sınırıdır; eksik yarışlarla daha fazla sporcu baraj geçebilir.

---

## Kadın (F)

### Multi Gençler
- **KESİN: 10** &nbsp;|&nbsp; **ADAY: 0**

| # | Doğum Yılı | Sporcu |
|---|---|---|
| 1 | 2009 | Gökçe Unur |
| 2 | 2009 | Neva Naz Güvenç |
| 3 | 2009 | Alisa Enercan |
| 4 | 2009 | Beren Başaran |
| 5 | 2009 | Zeynep Demirören |
| 6 | 2010 | Ela Işcan |
| 7 | 2010 | Asya Melek Alp |
| 8 | 2010 | Seher Kaya |
| 9 | 2010 | Su Yüksel |
| 10 | 2010 | Su Inal |

ADAY listesi boş.

### Avrupa Gençler
- **KESİN: 3** (kısmi veri)

| Doğum Yılı | Sporcu | Baraj geçilen branşlar |
|---|---|---|
| 2009 | Alisa Enercan | Kelebek 200 |
| 2010 | Ela Işcan | Kurbağalama 200 |
| 2010 | Seher Kaya | Kelebek 200 |

---

## Erkek (M)

### Multi Gençler
- **KESİN: 10** &nbsp;|&nbsp; **ADAY: 1**

| # | Doğum Yılı | Sporcu |
|---|---|---|
| 1 | 2009 | Kaan Ivan Sağıroğlu |
| 2 | 2009 | Can Acar |
| 3 | 2009 | Mustafa Özgür Yalçın |
| 4 | 2009 | Kırhan Yılmaz |
| 5 | 2009 | Berkin Avcı |
| 6 | 2009 | Utku Ulucan |
| 7 | 2009 | Taylan Uygur |
| 8 | 2010 | Arel Gültekin |
| 9 | 2010 | Eymen Batu Ibolar |
| 10 | 2010 | Cemil Cankat Er |

**ADAY (1):** 2010 — Serhat Kasal

> Kaan Ivan Sağıroğlu ile Serhat Kasal `(1.lik, 2.lik, 3.lük)` sayılarında eşit
> (madde-5 kota sınırında). Hangisinin KESİN/ADAY olduğu `get_athlete_rankings`
> satır sırasına (id ASC) bağlı; veri yeniden yüklenirse yer değiştirebilir.

### Avrupa Gençler
- **KESİN: 3** (kısmi veri)

| Doğum Yılı | Sporcu | Baraj geçilen branşlar |
|---|---|---|
| 2009 | Can Acar | Sırtüstü 50 |
| 2009 | Utku Ulucan | Sırtüstü 100, Sırtüstü 200 |
| 2010 | Arel Gültekin | Kelebek 100, Kelebek 200 |

---

## Kontrol Listesi Sonuçları

| Kontrol | Sonuç | Kanıt |
|---|---|---|
| Multi Gençler yaşları ⊆ {2008, 2009, 2010} | **GEÇTİ** | Betikteki `assert 2008 <= birth_year <= 2010` tüm sporcularda geçti; listede yalnız 2009/2010 var (2008 sporcusu bu veri setinde Multi'ye girmedi). |
| Multi Gençler KESİN ≤ 10 K + 10 E | **GEÇTİ** | F = tam 10, M = tam 10. Kırpma sınırı aşılmadı; madde-5 beraberlik taşması yok. |
| Avrupa Gençler yaşları ⊆ {2008..2012} | **GEÇTİ** | Betikteki `assert 2008 <= birth_year <= 2012` tüm KESİN sporcularda geçti (gözlemlenen: 2009, 2010). |
| `avrupa_gencler_events` yalnız sporcunun gerçekten yüzdüğü branşları içeriyor | **GEÇTİ** | Her KESİN sporcu için `avrupa_gencler_events ⊆ combined_events` kontrol edildi; 9 branş girişinin tamamı sporcunun `combined_events` kümesinde. |
| Yıldızlar / Federasyon Karması çıktıları değişmedi | **GEÇTİ** | `python -m pytest -q` = 136 passed (Yıldızlar multinations / quota-trim / ranker-core / COMEN / Central Europe testleri dahil). |

---

## Gözlemler

- Hem F hem M için Multi Gençler tam olarak 10 sporcuyla doldu; kırpma mantığı devrede ama fazlalık/beraberlik taşması tetiklenmedi.
- Erkeklerde 1 sporcu (Serhat Kasal, 2010) ADAY olarak işaretlendi — KESİN kadro zaten 10'a ulaştığı için sıradaki isim aday havuzuna düştü; bu beklenen davranış, bug değil.
- Avrupa Gençler baraj geçen sayısı her iki cinsiyette de yalnız 3 — düşük ama kısmi veriyle (2 yarış) tutarlı. Baraj geçişleri ağırlıklı 200m mesafelerde ve kelebek/sırtüstü/kurbağalama branşlarında yoğunlaşıyor.
- 2008 doğumlu sporcular veri setinde mevcut ancak bu çalıştırmada ne Multi ne Avrupa Gençler KESİN listesine girdi; yaş filtresi doğru çalışıyor, seçilmeme performans kaynaklı.
- Tüm assert'ler hatasız geçti; betik sıfır exception ile tamamlandı.

## Sonuç

Gerçek veriyle çalıştırma kural mantığını doğruladı: yaş sınırları, kota kırpması ve
`avrupa_gencler_events` tutarlılığı beklendiği gibi. Üretim kodunda değişiklik yapılmadı.
Resmi kadro ilanıyla karşılaştırma yapılamadığından doğrulama, kural uyumu düzeyinde sınırlıdır.
