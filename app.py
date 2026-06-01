import streamlit as st
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import math
import random
import numpy as np
import os
import re
from geopy.geocoders import Nominatim

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Stokastik Lojistik Analitiği", layout="wide", page_icon="📊")

# --- MODERN DESIGN SYSTEM (CUSTOM CSS) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: #FAFAFA;
        }
        
        .main-title {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.05em;
            margin-bottom: 0.5rem;
        }
        
        .wpf-card-blue {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border-top: 4px solid #2563EB;
            margin-bottom: 1rem;
        }
        
        .wpf-card-red {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border-top: 4px solid #DC2626;
            margin-bottom: 1rem;
        }
        
        .badge-blue {
            background-color: #EFF6FF;
            color: #1E40AF;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
            margin-top: 0.5rem;
            border: 1px solid #BFDBFE;
        }
        .badge-red {
            background-color: #FEF2F2;
            color: #991B1B;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
            margin-top: 0.5rem;
            border: 1px solid #FCA5A5;
        }
        
        .status-pill-green {
            background-color: #DCFCE7;
            color: #166534;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #BBF7D0;
            display: inline-block;
            margin-left: 10px;
            vertical-align: middle;
        }
        .status-pill-red {
            background-color: #FEE2E2;
            color: #991B1B;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #FCA5A5;
            display: inline-block;
            margin-left: 10px;
            vertical-align: middle;
        }
        .status-pill-orange {
            background-color: #FEF3C7;
            color: #92400E;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid #FDE68A;
            display: inline-block;
            margin-left: 10px;
            vertical-align: middle;
        }
        
        .premium-panel {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.5rem;
            border-left: 6px solid #475569;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .address-bar {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 0.75rem 1.2rem;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
            color: #334155;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>Stokastik Rota Planlama ve Risk Analiz Platformu</div>", unsafe_allow_html=True)
st.markdown("<div style='color: #64748B; font-size: 1.05rem; margin-bottom: 2rem; font-weight: 400;'>Veri Odaklı Stratejik Karar Destek Sistemi (SPO & SAA Metodolojisi)</div>", unsafe_allow_html=True)

if 'hesaplama_yapildi' not in st.session_state:
    st.session_state['hesaplama_yapildi'] = False

st.sidebar.title("Kontrol Paneli")

with st.sidebar.expander("1. Coğrafi Konum Ayarları", expanded=True):
    bolge_adi = st.text_input("Çalışma Bölgesi:", value="Kadikoy, Istanbul")
    baslangic_adresi = st.text_input("Başlangıç Noktası:", value="Kadıköy Belediyesi, İstanbul")
    bitis_adresi = st.text_input("Varış Noktası:", value="Moda Sahil, İstanbul")

with st.sidebar.expander("2. Algoritmik Yapılandırma", expanded=False):
    sim_sayisi = st.slider("Monte Carlo Senaryo Sayısı (SAA):", 100, 1000, 600, step=100)
    lambda_guvenli = st.slider("Risk Hassasiyeti (Lambda):", 5000, 50000, 25000, step=5000)

with st.sidebar.expander("3. Çevresel Faktörler", expanded=True):
    hava_durumu = st.selectbox("Atmosfer Koşulları:", ["Güneşli", "Yağmurlu", "Kar Yağışlı"])
    gunun_saati = st.selectbox("Zaman Dilimi (Trafik Etkisi):", ["Gece (Sakin)", "Mesai Giriş/Çıkış (Yoğun)", "Gün İçi"])

@st.cache_resource
def haritayi_yukle_ve_isle(bolge, hava, saat):
    h_risk = {"Güneşli": 1.0, "Yağmurlu": 1.5, "Kar Yağışlı": 2.5}
    h_hiz = {"Güneşli": 1.0, "Yağmurlu": 0.8, "Kar Yağışlı": 0.5}
    s_trafik = {"Gece (Sakin)": 0.7, "Mesai Giriş/Çıkış (Yoğun)": 2.5, "Gün İçi": 1.3}

    temiz_ad = re.sub(r'[^a-zA-Z0-9]', '_', bolge.lower()).strip('_')
    klasor = "haritalar_cache"
    os.makedirs(klasor, exist_ok=True)
    graph_file = f"{klasor}/{temiz_ad}_final_v6.graphml"

    if not os.path.exists(graph_file):
        G = ox.graph_from_place(bolge, network_type='drive')
        ox.save_graphml(G, graph_file)
    else:
        G = ox.load_graphml(graph_file)

    for u, v, k, data in G.edges(data=True, keys=True):
        hw = data.get('highway', 'residential')
        if type(hw) == list: hw = hw[0]
        dist = data.get('length', 10.0)
        if type(dist) == list: dist = dist[0]

        speed = 65.0 if hw in ['motorway', 'primary'] else 30.0
        risk_val = random.uniform(0.35, 0.65) if hw in ['motorway'] else random.uniform(0.01, 0.06)

        etkin_hiz = (speed / 3.6) * h_hiz[hava]
        data['base_risk'] = min(0.99, risk_val * h_risk[hava])
        data['travel_time'] = (dist / etkin_hiz) * (random.uniform(1.0, 1.3) * s_trafik[saat])
        
    return G

if st.sidebar.button("Analiz Yap ve Rotaları Hesapla", use_container_width=True):
    with st.spinner("Stokastik optimizasyon motoru çalışıyor..."):
        geolocator = Nominatim(user_agent="lojistik_final_descriptive")
        start_loc = geolocator.geocode(baslangic_adresi)
        end_loc = geolocator.geocode(bitis_adresi)
        
        if not start_loc or not end_loc:
            st.error("Giriş yapılan adres tanınamadı. Lütfen lokasyon bilgisini kontrol edin.")
            st.stop()

        G = haritayi_yukle_ve_isle(bolge_adi, hava_durumu, gunun_saati)
        n_start = ox.nearest_nodes(G, X=start_loc.longitude, Y=start_loc.latitude)
        n_end = ox.nearest_nodes(G, X=end_loc.longitude, Y=end_loc.latitude)

        def weight_func(lamda):
            return lambda u, v, d: d.get('travel_time', 10) + (lamda * -math.log(1 - d.get('base_risk', 0.01) + 1e-6))

        best_fast = nx.astar_path(G, n_start, n_end, weight=weight_func(0))
        best_safe = nx.astar_path(G, n_start, n_end, weight=weight_func(lambda_guvenli))

        ortak = set(best_fast) & set(best_safe)
        farklilik = 1.0 - (len(ortak) / max(len(best_fast), len(best_safe)))
        
        if farklilik < 0.35:
            f_edges = set(zip(best_fast[:-1], best_fast[1:]))
            def forced_weight(u, v, d):
                base_w = d.get('travel_time', 10) + (lambda_guvenli * -math.log(1 - d.get('base_risk', 0.01) + 1e-6))
                return base_w * 200.0 if ((u, v) in f_edges or (v, u) in f_edges) else base_w
            try:
                best_safe = nx.astar_path(G, n_start, n_end, weight=forced_weight)
                farklilik = 1.0 - (len(set(best_fast) & set(best_safe)) / max(len(best_fast), len(best_safe)))
            except: pass

        def simulate_route(route):
            res = []
            edges = list(zip(route[:-1], route[1:]))
            for _ in range(sim_sayisi):
                t = 0
                for u, v in edges:
                    d = G.get_edge_data(u, v)[0]
                    t += d.get('travel_time', 10) * max(0.8, np.random.normal(1.1, 0.25)) * (5.0 if random.random() < d.get('base_risk', 0.01) else 1.0)
                res.append(t / 60)
            return res

        fast_res = simulate_route(best_fast)
        safe_res = simulate_route(best_safe)

        df = sum(G.get_edge_data(u, v)[0].get('length', 0) for u,v in zip(best_fast[:-1], best_fast[1:])) / 1000
        ds = sum(G.get_edge_data(u, v)[0].get('length', 0) for u,v in zip(best_safe[:-1], best_safe[1:])) / 1000

        st.session_state.update({
            'hesaplama_yapildi': True, 
            'G': G, 
            'best_fast': best_fast, 
            'best_safe': best_safe,
            'fast_res': fast_res, 
            'safe_res': safe_res, 
            'farklilik': farklilik, 
            'mesafeler': (df, ds), 
            'adlar': (start_loc.address, end_loc.address),
            'hava': hava_durumu, 
            'saat': gunun_saati
        })

if st.session_state['hesaplama_yapildi']:
    G = st.session_state['G']
    fast_res = st.session_state['fast_res']
    safe_res = st.session_state['safe_res']
    best_fast = st.session_state['best_fast']
    best_safe = st.session_state['best_safe']
    df, ds = st.session_state['mesafeler']

    st.markdown(f"""
    <div class='address-bar'>
        <strong>📍 Başlangıç:</strong> {st.session_state['adlar'][0]} &nbsp;|&nbsp; 
        <strong>🏁 Varış:</strong> {st.session_state['adlar'][1]}
    </div>
    """, unsafe_allow_html=True)

    fast_var95 = np.percentile(fast_res, 95)
    fast_cvar95 = np.mean([t for t in fast_res if t >= fast_var95])

    safe_var95 = np.percentile(safe_res, 95)
    safe_cvar95 = np.mean([t for t in safe_res if t >= safe_var95])

    # KONTROL METRİKLERİ VE GRAFİKLER
    col_left_card, col_right_card = st.columns(2)
    
    with col_left_card:
        st.markdown(f"""
        <div class='wpf-card-blue'>
            <div style='color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Hız Odaklı Güzergah</div>
            <div style='color: #1E293B; font-size: 2.25rem; font-weight: 700; margin-top: 0.25rem;'>
                {np.mean(fast_res):.1f} <span style='font-size: 1.25rem; font-weight: 500;'>dk</span>
                <div class='status-pill-green'>↑ En Hızlı</div>
            </div>
            <div style='margin-top: 1rem;'>
                <div class='badge-blue'>Risk Eşiği (VaR): {fast_var95:.1f} dk</div>
                <div class='badge-blue' style='background-color: #DBEAFE;'>Kuyruk Şiddeti (CVaR): {fast_cvar95:.1f} dk</div>
                <div class='status-pill-red' style='margin-left:0px; margin-top:5px; display:block; width:fit-content;'>↑ Gecikme İhtimali</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right_card:
        st.markdown(f"""
        <div class='wpf-card-red'>
            <div style='color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Risk-Duyarlı Güzergah</div>
            <div style='color: #1E293B; font-size: 2.25rem; font-weight: 700; margin-top: 0.25rem;'>
                {np.mean(safe_res):.1f} <span style='font-size: 1.25rem; font-weight: 500;'>dk</span>
                <div class='status-pill-orange'>↑ Daha Yavaş</div>
            </div>
            <div style='margin-top: 1rem;'>
                <div class='badge-red'>Risk Eşiği (VaR): {safe_var95:.1f} dk</div>
                <div class='badge-red' style='background-color: #FEE2E2;'>Kuyruk Şiddeti (CVaR): {safe_cvar95:.1f} dk</div>
                <div class='status-pill-green' style='margin-left:0px; margin-top:5px; display:block; width:fit-content;'>↑ Güvenli Teslimat</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("Şebeke Topolojisi ve Rota Gösterimi")
        fig, ax = ox.plot_graph_routes(G, [best_fast, best_safe], route_colors=['#2563EB', '#DC2626'], route_linewidths=[4, 4], node_size=0, bgcolor='#FAFAFA', edge_color='#E2E8F0')
        st.pyplot(fig)
        
    with c_right:
        st.subheader("Monte Carlo Simülasyonu Kuyruk Dağılımı")
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.hist(fast_res, bins=40, alpha=0.6, color='#2563EB', label='Mavi Güzergah (Hız)')
        ax2.hist(safe_res, bins=40, alpha=0.6, color='#DC2626', label='Kırmızı Güzergah (Risk-Duyarlı)')
        ax2.set_xlabel("Varış Süresi (Dakika)")
        ax2.set_ylabel("Senaryo Frekansı")
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.grid(axis='y', linestyle='--', alpha=0.3)
        ax2.legend(frameon=False)
        st.pyplot(fig2)

    st.markdown("---")
    st.subheader("Stratejik Karar Destek Sistemi")
    
    target = st.slider("Hizmet Seviyesi Taahhüdü (SLA) Zaman Hedefi (Dakika):", min_value=5, max_value=40, value=15)
    
    p_f = sum(1 for t in fast_res if t <= target) / len(fast_res) * 100
    p_s = sum(1 for t in safe_res if t <= target) / len(safe_res) * 100

    col_sla_a, col_sla_b = st.columns(2)
    with col_sla_a:
        st.metric(f"Mavi Rota SLA Başarı Oranı ({target} dk)", f"%{p_f:.1f}")
    with col_sla_b:
        st.metric(f"Kırmızı Rota SLA Başarı Oranı ({target} dk)", f"%{p_s:.1f}")

    st.markdown(f"""
    <div class='premium-panel'>
        <div style='font-weight: 600; color: #1E293B; margin-bottom: 0.75rem;'>Operasyonel Verimlilik ve Sürdürülebilirlik Matrisi</div>
        <div style='display: flex; justify-content: space-between; font-size: 0.9rem; color: #475569;'>
            <div><strong>Toplam Mesafe:</strong><br>• Mavi: {df:.2f} km<br>• Kırmızı: {ds:.2f} km</div>
            <div><strong>Tahmini Yakıt:</strong><br>• Mavi: {(df/100)*8*45:.1f} TL<br>• Kırmızı: {(ds/100)*8*45:.1f} TL</div>
            <div><strong>Karbon Salınımı:</strong><br>• Mavi: {df*0.15:.2f} kg CO₂<br>• Kırmızı: {ds*0.15:.2f} kg CO₂</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    analiz_hava = st.session_state['hava']
    analiz_saat = st.session_state['saat']
    
    if p_s > p_f + 15:
        tavsiye = f"**Risk-Duyarlı Dağıtım Politikası Önerilir:** {analiz_hava} hava koşulları ve {analiz_saat} zaman diliminde şebeke oynaklığı yüksektir. Kırmızı rota seyahat süresini uzatsa da, %{p_s:.1f} SLA başarı oranı ve optimize edilmiş kuyruk riski (CVaR) ile operasyonel güvence sağlamaktadır."
    else:
        tavsiye = f"**Maliyet Odaklı Dağıtım Politikası Önerilir:** {analiz_hava} hava koşullarında ve {analiz_saat} zaman diliminde şebeke riskleri kabul edilebilir sınırlar içerisindedir. Mavi rota tercih edilerek operasyonel maliyetler ve karbon ayak izi minimize edilebilir."
    
    st.info(tavsiye)