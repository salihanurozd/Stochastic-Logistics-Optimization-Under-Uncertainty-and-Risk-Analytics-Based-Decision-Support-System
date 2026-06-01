import osmnx as ox
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import math
import random
import re

print(" Dinamik Lambda Parametrik Duyarlılık Analizi")

bolge_adi = "Kadikoy, Istanbul"
temiz_ad = re.sub(r'[^a-zA-Z0-9]', '_', bolge_adi.lower()).strip('_')
graph_file = f"haritalar_cache/{temiz_ad}_final_v6.graphml"

G = ox.load_graphml(graph_file)

# Kadıköy Belediyesi - Moda Sahil Koordinatları Sabitlendi
n_start = ox.nearest_nodes(G, X=29.0369, Y=40.9912)
n_end = ox.nearest_nodes(G, X=29.0232, Y=40.9785)

# Şebeke Temel Risk Değerlerini ve Gün İçi Trafik Ağırlıklarını Yükle
for u, v, k, data in G.edges(data=True, keys=True):
    hw = data.get('highway', 'residential')
    if isinstance(hw, list): hw = hw[0]
    dist = data.get('length', 10.0)
    if isinstance(dist, list): dist = dist[0]
    speed = 65.0 if hw in ['motorway', 'primary'] else 30.0
    data['base_risk'] = min(0.99, random.uniform(0.35, 0.65) if hw in ['motorway'] else random.uniform(0.01, 0.06))
    data['travel_time'] = (dist / (speed / 3.6)) * 1.3 # Gün içi çarpanı

# Duyarlılık Test Parametreleri
lambdas = [0, 5000, 10000, 20000, 30000, 40000, 50000]
ortalama_sureler = []
karbon_salinimlari = []

for lamda in lambdas:
    def weight_func(u, v, d):
        return d.get('travel_time', 10) + (lamda * -math.log(1 - d.get('base_risk', 0.01) + 1e-6))
    
    # A* ile rotayı bul
    path = nx.astar_path(G, n_start, n_end, weight=weight_func)
    
    # Mesafe bazlı Karbon salınımı hesapla
    dist_km = sum(G.get_edge_data(u, v)[0].get('length', 0) for u, v in zip(path[:-1], path[1:])) / 1000
    karbon_salinimlari.append(dist_km * 0.15)
    
    # Monte Carlo Simülasyonu ile ortalama süreyi bul
    sureler = []
    edges = list(zip(path[:-1], path[1:]))
    for _ in range(100):
        t = 0
        for u, v in edges:
            d = G.get_edge_data(u, v)[0]
            t += d.get('travel_time', 10) * max(0.8, np.random.normal(1.1, 0.25)) * (5.0 if random.random() < d.get('base_risk', 0.01) else 1.0)
        sureler.append(t / 60)
    ortalama_sureler.append(np.mean(sureler))

# --- ÇİFT EKSENLİ PARAFREKANS GRAFİĞİ ---
fig, ax1 = plt.subplots(figsize=(10, 6), dpi=150)

# Sol Eksen: Seyahat Süresi (Kırmızı)
color = '#DC2626'
ax1.set_xlabel('Risk Hassasiyet Katsayısı (Lambda - $\lambda$)', fontsize=11, fontweight='bold', labelpad=10)
ax1.set_ylabel('Ortalama Seyahat Süresi (Dakika)', color=color, fontsize=11, fontweight='bold')
line1 = ax1.plot(lambdas, ortalama_sureler, marker='o', color=color, linewidth=2.5, label='Ortalama Seyahat Süresi (Sol Aks)')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, linestyle=':', alpha=0.5)

# Sağ Eksen: Karbon Salınımı (Yeşil)
ax2 = ax1.twinx()  
color = '#10B981'
ax2.set_ylabel('Sürdürülebilirlik Metriği: Karbon Ayak İzi (kg $CO_2$)', color=color, fontsize=11, fontweight='bold')
line2 = ax2.plot(lambdas, karbon_salinimlari, marker='s', linestyle='--', color=color, linewidth=2.5, label='Karbon Salınımı (Sağ Aks)')
ax2.tick_params(axis='y', labelcolor=color)

# Lejant Birleştirme
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0')

plt.title('Parametrik Duyarlılık Analizi: Risk Kaçınma Düzeyinin ($\lambda$) Süre ve Çevre (ESG) Üzerindeki Etkisi', fontsize=12, fontweight='bold', pad=15)
fig.tight_layout()

# Grafiği Kaydet ve Göster
plt.savefig("bolum4_lambda_duyarlilik.png", bbox_inches='tight')
plt.show()
print("python Grafik 'bolum4_lambda_duyarlilik.png' adıyla başarıyla kaydedildi!")