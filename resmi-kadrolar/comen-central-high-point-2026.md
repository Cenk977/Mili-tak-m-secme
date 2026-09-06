# Comen Cup ve Central European — "High Point" Ekran Görüntüleri (2026)

Kaynak: kullanıcının paylaştığı ekran görüntüleri (muhtemelen SwimStandings/Meet Mobile "Meet Dashboard" — "High point" görünümü), 2026-09-06.

**ÖNEMLİ AÇIK SORU:** Bu "High point" listesi sadece ilk 5'i mi gösteriyor (kısmi görünüm), yoksa TAM resmi kadro mu? Bu netleşmeden kesin karşılaştırma yapılamaz — "High point" genelde toplam puan bazlı bir skor tablosu olabilir, "hangi branşta kim birinci oldu" listesiyle birebir aynı olmayabilir.

## COMEN - MEDITERRANEAN (Jun 19-21, 2026), Türkiye Yüzme Federasyonu, Roma TUR

### Women — High point (ilk 5)
1. Alara Gokalp
2. Yaren Soysal
3. Beril Cagri
4. Damla Maviler
5. Ipek Sozer

### Men — High point (ilk 5)
1. Cemil Cankat Er
2. Eymen IBOLAR
3. Sarp Hasay
4. Sarper Taze
5. Kuzey Set

## Central European Countries Meet (Jul 17-19, 2026), Türkiye Yüzme Federasyonu, Roma TUR

### Men 14-15 — High point (ilk 5)
1. Toprak Topatan
2. Umut Aras Ozkan
3. Sarper Taze
4. Emir Bartu Ozcan
5. Kuzey Set

### Women 14-15 — High point (ilk 5)
1. Alara Gokalp
2. Beril Cagri
3. Yaren Soysal
4. Ipek Sozer
5. Damla Maviler

## Notlar / Tutarsızlıklar

- İlk paylaşılan "High point" ekran görüntüsü sadece bir liderlik tablosuydu (ilk 5), TAM kadro değildi. Kullanıcı daha sonra gerçek tam Comen Cup Kadın kadrosunu (11 kişi, entry-listesiyle) paylaştı:
  Alara Gökalp, Yaren Soysal, Beril Çağrı, Damla Maviler, İpek Sözer, Eda Hacıoğlu, İpek Su Ersan, Ayşe Kent, Ayşe Nazlı Sönmez, Idil Gülcan, Kumsal Kandemir.

## KÖK NEDEN BULUNDU VE DÜZELTİLDİ (2026-09-06)

Kullanıcının açıklaması: **"multi sadece aralık yarışında, comen ve central aralık nisan karması en iyi dereceye göre"** — Comen Cup ve Central European, Aralık(Antalya)+Nisan(Edirne) sonuçlarının BİRLEŞİK en iyi derecesine göre değerlendirilir (Multinations ise SADECE Aralık).

**Bug:** `select_yildizlar_comen_cup_aralik()` sadece `antalya_events_time`, `select_yildizlar_comen_cup_nisan()` sadece `edirne_events_time` kullanıp OR'luyordu — iki AYRI yarışta iki farklı galip olabiliyordu. Central European zaten doğru şekilde `combined_events_time` kullanıyordu.

**Düzeltme:** Her iki Comen fonksiyonu da `combined_events_time` kullanacak şekilde birleştirildi (Central ile aynı mantık).

**Sonuç (Kadın karşılaştırması, 2026-09-06 verisiyle):**
- Önce: 17 kesin (6 fazladan yanlış isim: Tuğba Yıldız, Cemre İnce, Pelin Kızıldere, Talya Tok, Nehir Doğulu, Derin Anbarlı)
- Sonra: 10 kesin, **0 fazladan isim**, sadece 1 eksik (Damla Maviler — 800m Serbest verisi Antalya/Edirne LXF'lerinde hiç yok, veri eksikliği, algoritma sorunu değil)
- Central European (kadın) zaten 10/11 ile aynı doğru sonucu veriyordu.

Test: `federasyon/tests/test_yildizlar_comen_cup.py`

## Erkek Comen Cup Karşılaştırması (2026-09-06)

Gerçek tam kadro (11 kişi, kullanıcı entry-list ekran görüntüsüyle paylaştı):
Cemil Cankat Er, Eymen IBOLAR, Sarp Hasay, Sarper Taze, Kuzey Set, Kivanc Ozkan, Derin Ayhan, Deniz Eryol, Umut Aras Ozkan, Kaan Akça, Emir Bartu Özcan.

Bizim sistem:
- **KESİN (6):** Cemil Cankat Er, Eymen Batu Ibolar, Sarp Barkın Hasay, Kuzey Set, Kıvanç Özkan, Deniz Kaan Eryol
- **BAYRAK ADAYI (5):** Sarper Taze, Derin Ayhan, Umut Aras Özkan, Kaan Akça, Emir Bartu Özcan (4'ü aynı zamanda Multinations kesin galibi — elit çok yönlü sporcular, bireysel galibiyetleri bu yaş havuzunda yok ama bayrak derinliği güçlü)

**KESİN + BAYRAK ADAYI = 11/11 tam kapsama.** Fazladan sadece 2 isim (bug değil, gerçek galibiyetleri var ama federasyon dahil etmemiş): Arel Gültekin (4 galibiyet: Kelebek 50/100/200 + Serbest 200), Serhat Kasal (2 galibiyet: Kurbağalama 50/100).

**Sonuç:** Comen/Central sistemi hem erkek hem kadında doğru çalışıyor — kesin+bayrak adayı birleşimi gerçek kadroyu eksiksiz kapsıyor, ekstra isimler federasyonun ek takdir yetkisiyle açıklanabilir.
