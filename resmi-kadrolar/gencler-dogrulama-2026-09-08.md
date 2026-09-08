# Gençler Milli Takım Seçimi — Gerçek Veri Akıl-Sağlığı Doğrulaması

**Tarih:** 2026-09-08 (Avrupa Gençler sayıları 2026-09-08 akşamı düzeltildi — bkz. "Düzeltme notu")
**Veri kaynağı:** `data/bolge_karmalari.db` — 2025 TYF yarışları (Antalya = Aralık, Edirne = Nisan), doğum yılları 2008-2012.
**Çalıştırılan:** `database.db.get_athlete_rankings` → `federasyon.gencler_ranker.select_all_gencler`

> **Düzeltme notu (2026-09-08 akşamı):** Bu dosyanın ilk sürümü Avrupa Gençler'i
> **3K + 3E** gösteriyordu. Bu yanlıştı — ilk doğrulama betiği baraj karşılaştırmasını
> hatalı yapmış (0.1–0.7 sn barajı AŞAN dereceleri "geçti" saymış). Kod doğru
> çalışıyor; `check_baraj` süreleri saniyeye çevirip `<=` karşılaştırıyor. Elle
> doğrulandı: ör. Can Acar 50m Sırtüstü = **26.22**, sporcu barajı **26.10** →
> 0.12 sn yavaş, geçmiyor. Doğru sayı: **1K + 1E**.

> **Kapsam uyarısı:** Elimizde resmi Gençler kadro ilanı YOK. Doğrulama yalnızca kural
> mantığı ve sınır koşulları düzeyinde. Multi Gençler çekirdeği Multi Yıldızlar ile
> aynı kod yolu (`_select_branch_winners_core`), o taraf resmi kadroyla doğrulanmış.

> **Avrupa Gençler — kısmi veri:** Barajlar yalnızca DB'deki iki TYF yarışıyla (Aralık /
> Nisan) değerlendirildi. Sezonun diğer akredite müsabakaları veri setinde yok →
> KESİN sayıları gerçek sezonun **alt sınırı**. Avrupa Gençler barajları sıkı; iki
> yarışla çok az sporcunun geçmesi beklenen bir durum.

---

## Kadın (F)

### Multi Gençler — KESİN 10, ADAY 0

| # | Doğum | Sporcu |
|---|---|---|
| 1 | 2009 | Gökçe Unur |
| 2 | 2009 | Neva Naz Güvenç |
| 3 | 2009 | Beren Başaran |
| 4 | 2009 | Alisa Enercan |
| 5 | 2009 | Zeynep Demirören |
| 6 | 2010 | Su Yüksel |
| 7 | 2010 | Ela Işcan |
| 8 | 2010 | Asya Melek Alp |
| 9 | 2010 | Su Inal |
| 10 | 2010 | Seher Kaya |

### Avrupa Gençler — KESİN 1

| Doğum | Sporcu | Sporcu barajı geçilen branş |
|---|---|---|
| 2009 | Alisa Enercan | Kelebek 200 |

Antrenör barajı geçen: 0.

---

## Erkek (M)

### Multi Gençler — KESİN 10, ADAY 1

| # | Doğum | Sporcu |
|---|---|---|
| 1 | 2009 | Can Acar |
| 2 | 2009 | Mustafa Özgür Yalçın |
| 3 | 2009 | Kırhan Yılmaz |
| 4 | 2009 | Berkin Avcı |
| 5 | 2009 | Utku Ulucan |
| 6 | 2009 | Taylan Uygur |
| 7 | 2010 | Arel Gültekin |
| 8 | 2010 | Eymen Batu Ibolar |
| 9 | 2010 | Serhat Kasal |
| 10 | 2010 | Cemil Cankat Er |

**ADAY (1):** 2009 — Kaan Ivan Sağıroğlu

> **Sınır beraberliği notu:** Kaan Ivan Sağıroğlu ile Serhat Kasal, `(1.lik, 2.lik,
> 3.lük)` sayılarında **eşit** (madde-5 kota sınırındalar). Hangisinin KESİN, hangisinin
> ADAY olduğu `get_athlete_rankings`'in satır sırasına (id ASC) bağlı — veri yeniden
> yüklenirse yer değiştirebilir. İkisi de "10. sıra ± 1" konumunda; federasyon bu tür
> beraberlikte kendi takdirini kullanır.

### Avrupa Gençler — KESİN 1

| Doğum | Sporcu | Sporcu barajı geçilen branş |
|---|---|---|
| 2010 | Arel Gültekin | Kelebek 200 |

Antrenör barajı geçen: 1 (Arel Gültekin — Kelebek 200'de antrenör barajını da geçiyor).

---

## Kontrol Listesi Sonuçları

| Kontrol | Sonuç | Kanıt |
|---|---|---|
| Multi Gençler yaşları ⊆ {2008, 2009, 2010} | GEÇTİ | Listede yalnız 2009/2010 (2008 sporcusu bu veride Multi'ye girmedi). |
| Multi Gençler KESİN ≤ 10K + 10E | GEÇTİ | K = 10, E = 10. Madde-5 kırpması E'de devrede (11 birinci → 1 aday). |
| Avrupa Gençler yaşları ⊆ {2008..2012} | GEÇTİ | KESİN sporcular 2009/2010. |
| `avrupa_gencler_events` yalnız gerçekten yüzülen branşlar | GEÇTİ | Her giriş sporcunun `combined_events` kümesinde. |
| Baraj karşılaştırması `parse_time` + `<=` (string compare değil) | GEÇTİ | `check_baraj` düzeltildi; elle doğrulandı (Can Acar 26.22 > 26.10 → geçmiyor). |
| Yıldızlar / Federasyon Karması çıktıları değişmedi | GEÇTİ | Regresyon testleri unchanged. |

## Sonuç

Kural mantığı doğrulandı: yaş sınırları, kota kırpması, `avrupa_gencler_events`
tutarlılığı ve baraj karşılaştırması beklendiği gibi. Avrupa Gençler'de iki yarışla
yalnızca 1K + 1E sporcunun sporcu barajını geçmesi, barajların sıkılığı göz önüne
alındığında makul. Resmi kadro ilanıyla karşılaştırma yapılamadı.
