# Yapılacaklar — Federasyon Karması Sınır Durumu Farkları (2026-09-07 itibarıyla)

Bu oturumda Multinations, Comen Cup, Central European ve Federasyon Karması sistemleri gerçek TYF PDF/ekran görüntüleriyle karşılaştırıldı. Büyük çoğunluk doğrulandı (bkz. `federasyon-karmasi-resmi-kadro-2011-2012-2013.md` ve `comen-central-high-point-2026.md`). Kalan, henüz çözülmemiş noktalar:

## 1. Tam puan eşitliğinde 4.-5.-6. yarış tiebreak farkı

**Örnek:** 2012 Erkek — Kaan Balta (top3=23, 4. yarışı yok) vs Doruk Efe Donbaycı (top3=23, 4. yarışı 6 puan).
- MD kural 6: eşitlikte 4.-5.-6. yarış puanına bakılır → Doruk'un 4. yarışı olduğu için kural metnine göre O kazanmalı.
- Bizim sistem: kural metnini birebir doğru uyguluyor, Doruk'u TR'ye seçiyor.
- Resmi sonuç: Kaan Balta TR'de, Doruk Bölge'de — TERS karar.

**Soru:** Federasyonun gerçek tiebreak süreci yazılı kuraldan mı farklı, yoksa bizim skorlama/veri kaynağımız mı eksik? İncelenmemiş.

## 2. Kota sınırını aşan ama birbirine eşit sporcu grupları (sınırdaki kişiyle eşit DEĞİL)

**Örnek:** 2013 Erkek Bölge1 — resmi kadro 8 kişi (kota=6), ama 7. ve 8. kişi (Burak Kabaoğlu=21, Levent Yıldız=21) 6.kişiyle (Rüzgar Mertel=22) eşit değil, sadece kendi aralarında eşitler.
- Bizim `_select_with_tie()` sadece SINIRDAKİ kişiyle eşit olanları ekliyor — bu 2 kişi sınırla eşit olmadığı için dahil edilmiyor.
- Ama resmi kadroda bu 2 kişi de var.

**Aynı desen:** 2013K Bölge6 (4 kişi, kota 3), 2012E Bölge4 (3 kişi, kota 2), 2013E Bölge4 (5 kişi, kota 3), 2013E Bölge3 (Uras Güneş eksik/Eren Ayaz fazla), 2011E Bölge1/Bölge5, 2012F Bölge3 (Merve Mengüberti + Talya Tok eksik).

**Soru:** Bölge kotası da "en az" mı yoksa federasyon burada da ek takdir mi kullanıyor? Yazılı kuralda bölge için ayrı bir "kadronun altında/üstünde olursa" maddesi yok (sadece TR/Multinations'ta var) — bu farkın nedeni netleştirilmemiş.

## Önerilen sonraki adımlar

1. Kaan Balta / Doruk Efe Donbaycı vakasını daha derinlemesine incele: Doruk'un 4. yarışının puanı/branşı gerçekten doğru mu (LXF verisinde çift kontrol), yoksa TYF'nin kullandığı "4.-5.-6. yarış" hesaplaması bizimkinden farklı bir formül mü (örn. sadece 4.'e bakıp 5-6'ya hiç bakmıyor olabilirler, ya da cumulative değil sadece 4.'ün kendisine bakıyor olabilirler).
2. Bölge kotası "eşitlik" davranışının TR'dekiyle aynı mı olması gerektiğini (sınırla eşit olma şartı) yoksa farklı bir mantık mı (örn. "kotanın X üstüne kadar" gibi bir tolerans) olduğunu **kullanıcıya sorarak** netleştir.
3. Tüm bu vakalar için kullanıcıdan onay alındıktan sonra `ranker.py::_select_with_tie()` üzerinde gerekiyorsa değişiklik yap, TDD ile test yaz, gerçek PDF verisiyle tekrar doğrula.

## Bu oturumda düzeltilen gerçek bug'lar (referans)

1. Antalya/Edirne dosya adı → race_leg tespiti kayboldu (Task 4 regresyonu) — düzeltildi.
2. İki ayrı SQLite dosyası (upload vs dashboard) — birleştirildi.
3. Upload/filtre performans sorunları (N+1 DB bağlantısı, O(n²) yıldızlar hesaplaması) — düzeltildi.
4. Federasyon Karması'nın iki çakışan algoritması (puan bazlı vs 1.'lik-sayısı bazlı) — puan bazlı olan kalıcı yapıldı.
5. Multinations/Central kotanın zorla doldurulması/kırpılması — kaldırıldı, kesin/aday ayrımı eklendi.
6. Multinations/Comen/Central'da bayrak-derinliği adayı sinyali eklendi (BAYRAK ADAYI rozeti).
7. Comen Cup'ın Aralık/Nisan'ı AYRI hesaplayıp OR'laması (olması gereken: BİRLEŞİK en iyi derece) — düzeltildi, 17→10 kesin, 0 hatalı fazlalık.
8. `region` filtresinin TR (ulusal) sıralamasını bölge-içi sıralamaya indirgemesi (birth_year pooling bug'ının ikizi) — düzeltildi.

Tüm düzeltmeler test edildi (104/104 pytest), gerçek TYF verisiyle çapraz kontrol edildi.

## 2026-09-07 (2. oturum) — Soru 2'nin büyük kısmı ÇÖZÜLDÜ: ferdi sporcu bug'ı

Yukarıdaki "Soru 2" (kota aşımı) vakalarının çoğu tie mantığı değil, **ferdi
(kulüpsüz) sporcuların bölgesiz kalmasıydı**. LXF'te `<CLUB name="Ferdi" ...>`
düğümü Excel kulüp haritasında olmadığı için parser `region=0`/`city=Unknown`
bırakıyordu; bu sporcular hiçbir bölge sıralamasına girmiyor, yerlerine
kotadan taşan başkaları seçiliyordu. CLUB düğümü ili plaka kodu olarak taşıyor
(`region="07"` = Antalya) — artık `modules/plate_region.py` ile plaka→bölge/il
fallback'i var (81/81 il, Excel il→bölge verisinden üretildi). Commit e1651fa.

Gerçek TYF verisiyle doğrulandı — resmi kadroyla eşleşti:
- **2013F Bölge3**: Aliye Pazar (ferdi Antalya) B3-2 girdi; kota 3'e döndü (önceden 4 kişi seçiliyordu, Ada Güngör + Derin Alya Kalak fazlalıktı).
- **2013E Bölge3**: Uras Güneş (ferdi Antalya) girdi, Eren Ayaz çıktı — bu notun tam dediği.
- **2012F Bölge3**: Merve Mengüberti (ferdi İzmir) B3-1 girdi.
- (Talya Tok bu veride puanlanabilir yarışa sahip değil → seçilmedi, ayrı durum.)

Testler: 109/109 pytest.

## 2026-09-07 (2. oturum) — SORU 1 ÇÖZÜLDÜ: 50m kısıtının kapsamı

`best_scores_sequence` "en fazla 1 adet 50m" kısıtını **tüm sıralama
dizisine** uyguluyordu → sporcunun ikinci 50m yarışı eşitlik-bozma
(4./5./6. yarış) sırasında da yok sayılıyordu. PDF kuralı kısıtı yalnızca
"puan aldıkları **3 yarış**" için koyuyor. Commit d398b70.

Düzeltme: top3 hâlâ max 1x50m; 4. yarıştan itibaren kalan tüm yarışlar
(ek 50m dahil) puana göre. top3 üçü dolduramazsa 0 padlenir.

Vaka — **2012 Erkek TR-10**: Kaan Balta (Kelebek50=7 + Serbest50=7 +
Serbest100=9 + Serbest200=7 → top3=23, top4=30) vs Doruk Efe Donbaycı
(top3=23, top4=29). Artık Kaan, Doruk'un önünde → **TR-10 = Kaan Balta**,
resmi kadroyla **2012E TR 10/10 tam eşleşme**. 2013 K/E TR hâlâ 20/20
(regresyon yok). Testler: 114/114.

Bunun yan etkisi: 2012E Bölge4'te Doruk artık Bölge'ye düşüyor
(Doruk+Tan seçili, kota 2). Resmi kadroda 3. isim Umut Ata Sarıkaya(20)
var — o da kota sınırının altında → "Soru 2" (federasyon takdiri)
sınıfına giriyor, ayrı bir hata değil.

## Kalan açık noktalar

- **Soru 2 (federasyon takdiri)**: 3 grupta resmi kadro kotayı aşıyor,
  fazladan çağrılanlar kota sınırının ALTINDA ve sınırla eşit değil:
  - 2013E B1: Burak Kabaoğlu(21), Levent Yıldız(21) — sınır 22
  - 2013E B4: Ahmet Tuna Atcı(21), Barış Atakan Güvenç(21) — sınır 22 (Ankara, kullanıcı onayladı: kod değişmeyecek)
  - 2013K B6: Ömür Güvel(20) — sınır 21
  - 2012E B4: Umut Ata Sarıkaya(20) — sınır 23
  Yazılı PDF kuralında karşılığı yok; wildcard/takdir görünüyor. Kod değişmeyecek.
- ~~**2012K B3 veri sorunu**: Talya Tok top3=0~~ **ÇÖZÜLDÜ (commit 27a6068).**
  Gerçek neden: Talya, 50m Kelebek'te 2011-2013K havuzunda en hızlı (28.36)
  olduğu için branş birincisi = kesin Multinations sayılıp Fed Karması'ndan
  dışlanıyordu. 2011-2013K'da 11 branş birincisi var, kota 10. PDF madde 5:
  kota aşımında (1.lik,2.lik,3.lük) sayısına göre kotaya indirilir. Talya'nın
  hiç 2./3.lüğü yok → en zayıf → ADAY'a düştü, Fed Karması'na girdi → 2012K
  B3-2 (resmi kadroyla eşleşti). Multinations F artık 10/10 resmi.

## Multinations/Central madde-5 kırpması (27a6068)

`_split_winners_by_quota()` — branş birincisi sayısı kotadan fazlaysa
(Multi 10, Central 12) `(1.lik, 2.lik, 3.lük)` azalan sıralanıp kotaya
indirilir; altta kalan birinciler ADAY (`candidate_yildiz_*`), otomatik
seçilmez ve Federasyon Karması'ndan dışlanmaz. `< kota` (madde 4 dolgusu)
ve `== kota` davranışı değişmedi. Comen'de kota yok, dokunulmadı.

Not: Eşitlikte sınırdaki kişi(ler) — şu an tam kotaya kesiliyor (kararlı
sıralama, giriş sırası korunur). Federasyonun eşitlik davranışı belirsiz;
kullanıcı bir sorun bildirirse "tied-keep" eklenebilir.

## 2026-09-09 — Bölge kotasında "1. sıra beraberliği" incelemesi: KURAL DEĞİL, TAKDİR

Kullanıcı 3 grupta federasyonun kotayı aştığını fark etti; olası kural:
"bölgenin 1. sırasındaki eşit-puanlı grup tek kontenjan sayılır, sonrası
normal". Bu hipotez 3 vakaya tam uyuyor:

| Grup | Kota | 1. sıra | Federasyon | Bizim kod |
|------|------|---------|-----------|-----------|
| 2012E B4 | 2 | {Doruk 23, Tan 23} | 3 (Umut 20 eklendi) | 2 |
| 2013K B6 | 3 | {Yağmur 23, Hatice 23} | 4 (Elif Durum 21 + Ömür Güvel 20) | 3 |
| 2013E B1 | 6 | {Ayaz, Ö.Cengiz, M.Uludağ = 25} | 8 (M.M.Kıraç 24 + Efe Ertürk 23 + Rüzgar 22 + Burak K. 21 + Levent Y. 21) | 6 |

**AMA kural DEĞİL** — kullanıcı karşı örnek buldu, aynı yapı zıt karar:

| Grup | Kota | 1. sıra | Federasyon | Bizim kod |
|------|------|---------|-----------|-----------|
| 2012E B6 | 2 | {Doruk Kervancıoğlu 19, Aydın Ege Özsoy 19} (birebir aynı key) | 2 (3.'yü almadı) | 2 ✓ |
| 2012E B5 | 2 | {Eymen Bera Ayas 11, Aras Ipek 11} | 2 (3.'yü almadı) | 2 ✓ |

B6/B5'te kurala sıkı uymuş, B4/B6-2013K/B1'de kotayı aşıp fazladan almış.
Kodlanabilir örüntü yok → **federasyon takdiri**. `_select_with_tie`
DEĞİŞMEYECEK; mevcut hali kural açısından doğru. Bu 5 vaka "Soru 2"
(federasyon kota-üstü takdiri) sınıfına ait — Ankara 2013E B4 gibi.
