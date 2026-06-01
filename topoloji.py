import osmnx as ox
import pandas as pd
import re
import os

print(" Kadıköy Yol Ağı Topoloji İstatistikleri Hesaplanıyor...")

# Orijinal önbellek adlandırmasıyla haritayı yükle
bolge_adi = "Kadikoy, Istanbul"
temiz_ad = re.sub(r'[^a-zA-Z0-9]', '_', bolge_adi.lower()).strip('_')
graph_file = f"haritalar_cache/{temiz_ad}_final_v6.graphml"

if os.path.exists(graph_file):
    G = ox.load_graphml(graph_file)
    print(" Mevcut harita önbellekten başarıyla yüklendi.")
else:
    G = ox.graph_from_place(bolge_adi, network_type='drive')
    print(" Harita OpenStreetMap üzerinden canlı çekildi.")

# 1. Temel Şebeke Metrikleri
nodes_count = len(G.nodes)
edges_count = len(G.edges)
avg_degree = sum(dict(G.degree()).values()) / nodes_count

print(f"\n--- Tablo 3.1 ŞEBEKE TOPOLOJİSİ TEMEL METRİKLERİ ---")
print(f"Toplam Düğüm (Kavşak) Sayısı: {nodes_count}")
print(f"Toplam Kenar (Sokak/Yol Segmenti) Sayısı: {edges_count}")
print(f"Ortalama Bağlantısallık Derecesi (Node Degree): {avg_degree:.2f}")

# 2. Yol Tiplerinin Dağılımı 
hw_list = []
for u, v, k, data in G.edges(data=True, keys=True):
    hw = data.get('highway', 'residential')
    if isinstance(hw, list): hw = hw[0]
    hw_list.append(hw)

df_hw = pd.Series(hw_list).value_counts()
df_hw_yuzde = pd.Series(hw_list).value_counts(normalize=True) * 100

print(f"\n --- Tablo 3.2: YOL SINIFLARININ DAĞILIMI ---")
for index, (val, pct) in enumerate(zip(df_hw, df_hw_yuzde)):
    print(f"{df_hw.index[index]}: {val} adet (%{pct:.1f})")