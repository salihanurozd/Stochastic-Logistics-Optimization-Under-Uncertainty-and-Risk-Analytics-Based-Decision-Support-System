# Stokastik Lojistik Optimizasyonu ve Risk Duyarlı Karar Destek Sistemi

Bu repo, Yıldız Teknik Üniversitesi Matematik Mühendisliği Bölümü bitirme tezi kapsamında geliştirilen, kentsel lojistik ağlarındaki belirsizlikleri (trafik yoğunluğu, kaza olasılıkları, hava muhalefeti) sayısallaştıran ve optimize eden dinamik bir Karar Destek Sistemi (KDS) prototipidir. 

Proje; geleneksel deterministik navigasyon algoritmalarının (Dijkstra/Standart A*) aksine, finans matematiğinde kullanılan risk metriklerini (**VaR** ve **CVaR**) OpenStreetMap tabanlı gerçek yol ağlarına entegre ederek güvenli rota alternatifleri üretir, şirketin Hizmet Seviyesi Taahhüdü (SLA) ve Yeşil Lojistik (ESG) çıktılarını simüle eder.

## 🚀 Öne Çıkan Özellikler

* **Gerçek Dünya Topolojisi (OSMnx):** Seçilen bölgeye ait canlı yol ağı verilerini çekerek düğüm (kavşak) ve kenar (sokak) tabanlı graf yapısı oluşturur. Ağ yükleme sürelerini optimize etmek için haritayı yerel olarak önbelleğe alır.
* **Risk-Duyarlı A\* Modeli:** Çarpımsal kaza ve gecikme olasılıklarını negatif logaritma dönüşümüyle toplamsal "güvenilmezlik cezalarına" çevirir. Rota ayrıştırma mekanizması sayesinde Hız Odaklı (Mavi) ve Risk-Duyarlı (Kırmızı) iki bağımsız güzergah koridoru üretir.
* **Monte Carlo Simülasyon Motoru:** Bulunan rotaları sahaya sürmeden önce 1000 iterasyonluk bir stres testine sokar. Hava durumu ve zaman dilimi kısıtları altında seyahat sürelerinin frekans histogramını çıkarır.
* **İleri Risk Analitiği:** Klasik beklenen süre tahminlerinin ötesine geçerek, risk eşiğini (**%95 VaR**) ve ekstrem gecikme senaryolarının kuyruk şiddetini (**%95 CVaR / Tail Risk**) hesaplar.
* **Stratejik Karar Matrisi:** Rotaların zaman hedefini yakalama olasılıklarını (%), tahmini yakıt maliyetlerini (TL) ve Karbon Ayak İzini ($CO_2$ emisyonu) canlı olarak karşılaştırarak karar vericiye yönetsel öneriler sunar.
## 🗺️ Ölçeklenebilir ve Dinamik Şebeke Altyapısı

Proje kapsamında ampirik doğrulamalar ve simülasyon testleri için pilot bölge olarak İstanbul'un en heterojen ulaşım ağlarından biri olan **Kadıköy** seçilmiştir. Ancak sistem mimarisi tamamen **jenerik ve parametrik** olarak tasarlanmıştır. 

Geliştirilen Karar Destek Sistemi, `OSMnx` ve `OpenStreetMap` API entegrasyonu sayesinde, arayüz üzerinden girilen dünyanın herhangi bir kentsel lokasyonuna (Örn: Beşiktaş, Fatih vs.) ait graf topolojisini canlı olarak çekebilmekte, o bölgeye ait stokastik risk matrislerini ve Monte Carlo simülasyonlarını dinamik olarak sıfırdan inşa edebilmektedir.
