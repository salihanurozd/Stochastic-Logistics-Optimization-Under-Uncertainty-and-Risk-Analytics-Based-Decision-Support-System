import matplotlib.pyplot as plt

# Senaryo Verileri (Ortalama Süre ve CVaR değerleri)
# Sıralama: S1 (İdeal), S4 (Stratejik), S2 (Yağmurlu), S3 (Kaos)
senaryolar = ['S1: İdeal', 'S4: Stratejik', 'S2: Yağmurlu', 'S3: Kaos']
x_ortalama = [4.6, 8.2, 10.8, 38.2] # Maliyet (Dakika)
y_cvar = [6.2, 11.0, 14.8, 54.0]    # Risk (CVaR - Dakika)

# Grafiği Oluşturma
plt.figure(figsize=(10, 6))
plt.plot(x_ortalama, y_cvar, linestyle='--', color='#4169E1', alpha=0.6) 
plt.scatter(x_ortalama, y_cvar, color='#DC143C', s=120, zorder=5) 

# Etiketleri yerleştirme
for i, txt in enumerate(senaryolar):
    if txt == 'S3: Kaos':
        plt.annotate(txt, (x_ortalama[i], y_cvar[i]), xytext=(-55, -15), textcoords='offset points', fontsize=10, fontweight='bold', color='#333333')
    else:
        plt.annotate(txt, (x_ortalama[i], y_cvar[i]), xytext=(10, -5), textcoords='offset points', fontsize=10, fontweight='bold', color='#333333')

# Eksen ve Başlık Ayarları
plt.title('Lojistik Karar Verme Süreçlerinde Pareto Sınırı (Time vs. Tail Risk)', fontsize=12, fontweight='bold', pad=15)
plt.xlabel('Ortalama Varış Süresi (Dakika) - [Operasyonel Maliyet]', fontsize=11)
plt.ylabel('95% Kuyruk Riski (CVaR) - [Operasyonel Güvenlik]', fontsize=11)
plt.grid(True, linestyle=':', alpha=0.7)

plt.tight_layout()
plt.show()