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

Testler: 109/109 pytest. Kalan gerçek tie vakaları (2013E B1 vb.) ve "Soru 1"
(tam puan eşitliğinde 4.-5.-6. yarış tiebreak) hâlâ açık.
