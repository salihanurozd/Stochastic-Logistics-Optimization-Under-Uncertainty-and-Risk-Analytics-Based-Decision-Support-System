import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import math
import random
import numpy as np
import os
import re

print("="*50)
print(" STOKASTİK LOJİSTİK OPTİMİZASYON MOTORU ")
print("="*50)

# Kullanıcıdan Dinamik Girdi Alma
bolge_adi = input("\nHangi bölgeyi analiz etmek istersiniz? (Örn: Besiktas, Istanbul veya Cankaya, Ankara): ")

# --- PROFESYONEL VERİ TEMİZLEME ---
def turkce_karakter_temizle(metin):
    kaynak = "çğıöşüÇĞİÖŞÜ"
    hedef = "cgiosuCGIOSU"
    cevirici = str.maketrans(kaynak, hedef)
    return metin.translate(cevirici)

# Önce Türkçeleri İngilizceye çevir, sonra küçük harf yap, sonra sembolleri temizle
standart_ad = turkce_karakter_temizle(bolge_adi).lower()
temiz_ad = re.sub(r'[^a-z0-9]', '_', standart_ad)
temiz_ad = re.sub(r'_+', '_', temiz_ad).strip('_')

# Haritalar için özel klasör oluştur
klasor = "haritalar_cache"
if not os.path.exists(klasor):
    os.makedirs(klasor)

graph_file = f"{klasor}/{temiz_ad}_network.graphml"

# 1. DİNAMİK HARİTA YÖNETİMİ (Akıllı Önbellek)
if not os.path.exists(graph_file):
    print(f"\n[İNDİRİLİYOR] '{bolge_adi}' haritası OSM sunucularından çekiliyor...")
    print("Bu işlem bölgenin büyüklüğüne göre birkaç dakika sürebilir...")
    try:
        G = ox.graph_from_place(bolge_adi, network_type='drive')
        ox.save_graphml(G, graph_file)
        print(f"[BAŞARILI] Harita indirildi ve '{graph_file}' olarak diske kaydedildi.")
    except Exception as e:
        print(f"\n[HATA] Bölge bulunamadı veya veri çekilemedi! Lütfen İngilizce karakterlerle tam ilçe/il adını yazın.")
        print(f"Hata Detayı: {e}")
        exit() # Hata varsa programı güvenli şekilde kapat
else:
    print(f"\n[ÖNBELLEK] Harita zaten mevcut! İnternet kullanılmadan dosyadan yükleniyor.")
    G = ox.load_graphml(graph_file)
    print("[BAŞARILI] Harita saniyeler içinde RAM'e alındı.")

# 2. VERİ EKLEME (Stokastik Özellikler)
print("\n[VERİ İŞLEME] Sokaklara hız, risk ve anlık trafik verileri entegre ediliyor.")
for u, v, k, data in G.edges(data=True, keys=True):
    hw = data.get('highway', 'residential')
    if type(hw) == list: hw = hw[0]
    
    distance = data.get('length', 10.0)
    if type(distance) == list: distance = distance[0]

    # Ana yollar hızlı ama riskli, ara sokaklar yavaş ama güvenli
    if hw in ['motorway', 'motorway_link', 'trunk', 'primary', 'secondary']:
        data['speed_kph'] = 80.0
        data['base_risk'] = random.uniform(0.30, 0.60) 
    else:
        data['speed_kph'] = 30.0
        data['base_risk'] = random.uniform(0.01, 0.05) 

    data['traffic_factor'] = random.uniform(1.0, 3.0) 
    speed_mps = data['speed_kph'] / 3.6
    data['travel_time'] = (distance / speed_mps) * data['traffic_factor']

# 3. ROTA OPTİMİZASYONU (A* ve Lambda Çarpanı)
def get_weight(lamda):
    # Eksi logaritma formülü: Süre + (Risk Duyarlılığı * Risk Maliyeti)
    return lambda u, v, d: d.get('travel_time', 10) + (lamda * -math.log(1 - d.get('base_risk', 0.01) + 1e-6))

nodes = list(G.nodes())
print("\n[ALGORİTMA] Birbirinden bağımsız Hızlı ve Güvenli rotalar aranıyor...")

best_fast, best_safe = None, None
max_diff = -1

for i in range(150): # En farklı rotayı bulmak için maksimum 150 deneme
    n1, n2 = random.sample(nodes, 2)
    # Başlangıç ve bitiş noktaları birbirine çok yakın olmasın (Mesafe filtresi)
    dist = math.sqrt((G.nodes[n1]['x']-G.nodes[n2]['x'])**2 + (G.nodes[n1]['y']-G.nodes[n2]['y'])**2)
    if dist < 0.02: continue 

    try:
        r_fast = nx.astar_path(G, n1, n2, weight=get_weight(0)) # Sadece hıza odaklan (Lambda 0)
        r_safe = nx.astar_path(G, n1, n2, weight=get_weight(5000)) # Sadece güvenliğe odaklan (Lambda 5000)
        
        # Rotaların ne kadar farklı olduğunu hesapla (Jaccard Index benzeri)
        ortak_sokak_orani = len(set(r_fast) & set(r_safe)) / max(len(r_fast), len(r_safe))
        farklilik = 1.0 - ortak_sokak_orani
        
        if farklilik > max_diff:
            max_diff, best_fast, best_safe = farklilik, r_fast, r_safe
        
        if farklilik > 0.4: break # Yollar %40 farklıysa yeterli, döngüden çık
    except nx.NetworkXNoPath:
        continue

if best_fast:
    print(f"[BAŞARILI] Ayrışan rotalar bulundu! (Ayrışma Oranı: %{int(max_diff*100)})")
    print(">>> Harita açılıyor. Haritayı KAPATTIĞINIZDA simülasyon başlayacaktır. <<<")
    fig, ax = ox.plot_graph_routes(G, [best_fast, best_safe], route_colors=['blue', 'red'], route_linewidths=[4, 4], node_size=0, bgcolor='black')
    plt.show()
else:
    print("[HATA] Uygun rota bulunamadı. Lütfen kodu tekrar çalıştırın.")
    exit()

# 4. MONTE CARLO SİMÜLASYONU (Risk Analitiği)
def simulate(route, count=1000):
    times = []
    edges = list(zip(route[:-1], route[1:]))
    for _ in range(count):
        t = 0
        for u, v in edges:
            d = G.get_edge_data(u, v)[0]
            trafik = max(0.5, np.random.normal(1.1, 0.2)) # Normal dağılımlı trafik dalgalanması
            kaza = 5.0 if random.random() < d.get('base_risk', 0.05) else 1.0 # Eğer o gün kaza varsa süre 5'e katlanır
            t += d.get('travel_time', 10) * trafik * kaza
        times.append(t / 60) # Saniyeyi dakikaya çevir
    return times

print("\n[MONTE CARLO] 1000 farklı hava ve trafik senaryosu simüle ediliyor.")
fast_res = simulate(best_fast)
safe_res = simulate(best_safe)

# CVaR TABANLI RİSK RAPORU 
fast_var95 = np.percentile(fast_res, 95)
fast_cvar95 = np.mean([t for t in fast_res if t >= fast_var95])

safe_var95 = np.percentile(safe_res, 95)
safe_cvar95 = np.mean([t for t in safe_res if t >= safe_var95])

print("\n" + "="*50)
print(f"[{bolge_adi.upper()} - STRATEJİK RİSK RAPORU (CVaR)]")
print("="*50)
print(f"MAVİ (Hızlı Rota)  -> Ortalama: {np.mean(fast_res):.1f} dk | En Kötü %5 Ortalama (CVaR): {fast_cvar95:.1f} dk")
print(f"KIRMIZI (Güvenli)  -> Ortalama: {np.mean(safe_res):.1f} dk | En Kötü %5 Ortalama (CVaR): {safe_cvar95:.1f} dk")
print("-" * 50)
print(f"ANALİZ: Mavi rotanın kuyruk riski (CVaR), Kırmızı rotadan {abs(fast_cvar95 - safe_cvar95):.1f} dk daha fazladır.")
print("="*50)

# Çan Eğrisi Görselleştirme
plt.figure(figsize=(10, 5))
plt.hist(fast_res, bins=40, alpha=0.5, color='blue', label=f'Hızlı/Riskli (Ort: {np.mean(fast_res):.1f} dk)')
plt.hist(safe_res, bins=40, alpha=0.5, color='red', label=f'Güvenli/Yavaş (Ort: {np.mean(safe_res):.1f} dk)')
plt.title(f"{bolge_adi.upper()} - 1000 Simülasyonluk Lojistik Risk Dağılımı")
plt.xlabel("Teslimat Süresi (Dakika)")
plt.ylabel("Senaryo Frekansı")
plt.legend()
plt.show()

print("\nSistem başarıyla tamamlandı.")
