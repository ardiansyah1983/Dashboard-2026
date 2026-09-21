"""
app.py - Aplikasi Dashboard Visualisasi Hasil Pengukuran Kualitas Layanan Telekomunikasi (QoS).
"""

import os
import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium

import data_loader
import utils_viz
import utils_map

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Dashboard QoS Telekomunikasi",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Styling
st.markdown("""
<style>
    /* Global Styling */
    .main {
        background-color: #F8FAFC;
    }
    
    /* Header Card */
    .header-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #FFFFFF;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .header-title {
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    
    .header-desc {
        font-size: 14px;
        color: #94A3B8;
        margin-bottom: 0px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748B;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
    }
    
    .metric-unit {
        font-size: 13px;
        font-weight: 500;
        color: #64748B;
        margin-left: 4px;
    }
    
    .metric-footer {
        font-size: 11px;
        margin-top: 4px;
    }
    
    .status-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
    
    .badge-telkomsel { background-color: #FEE2E2; color: #DC2626; border: 1px solid #FECACA; }
    .badge-ioh { background-color: #FEF3C7; color: #D97706; border: 1px solid #FDE68A; }
    .badge-xlsmart { background-color: #DBEAFE; color: #2563EB; border: 1px solid #BFDBFE; }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #FFFFFF;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #EEF2F6 !important;
        color: #0F172A !important;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. SIDEBAR & DATA INGESTION
# ==========================================
st.sidebar.markdown("## ⚙️ Pengaturan & Filter")

# Deteksi file data yang ada
available_files = data_loader.find_qos_data_files()
file_options = {}

for f in available_files:
    fname = os.path.basename(f)
    dir_name = os.path.basename(os.path.dirname(f))
    label = f"📁 {fname} ({dir_name})"
    file_options[label] = f

data_source_mode = st.sidebar.radio(
    "Sumber Data:",
    ["Pilih File yang Tersedia", "Unggah File Baru (CSV/Excel)"],
    index=0
)

clean_df = pd.DataFrame()
raw_full_df = pd.DataFrame()
active_file_name = ""

if data_source_mode == "Pilih File yang Tersedia":
    if file_options:
        selected_file_label = st.sidebar.selectbox(
            "Pilih File Dataset:",
            list(file_options.keys())
        )
        selected_file_path = file_options[selected_file_label]
        active_file_name = os.path.basename(selected_file_path)
        try:
            clean_df, raw_full_df = data_loader.load_qos_summary(selected_file_path)
        except Exception as e:
            st.sidebar.error(f"Gagal membaca file: {e}")
    else:
        st.sidebar.warning("Tidak ditemukan file ringkasan QoS di folder.")
else:
    uploaded_file = st.sidebar.file_uploader(
        "Unggah File CSV / Excel QoS:",
        type=["csv", "xlsx", "xlsm"]
    )
    if uploaded_file is not None:
        active_file_name = uploaded_file.name
        try:
            clean_df, raw_full_df = data_loader.load_qos_summary(uploaded_file)
        except Exception as e:
            st.sidebar.error(f"Gagal membaca file unggahan: {e}")

if clean_df.empty:
    st.warning("⚠️ Belum ada data QoS yang berhasil dimuat. Silakan pilih atau unggah file ringkasan QoS di panel sebelah kiri.")
    st.stop()

# ==========================================
# 2. FILTER INTERAKTIF
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filter Analisis")

# Filter Event
all_events = sorted(clean_df['Event'].dropna().unique().tolist())
selected_events = st.sidebar.multiselect("Event:", all_events, default=all_events)

# Filter Kabupaten / Kota
all_kabupaten = sorted(clean_df['Kabupaten'].dropna().unique().tolist())
selected_kabupaten = st.sidebar.multiselect("Kabupaten / Kota:", all_kabupaten, default=all_kabupaten)

# Filter Operator
all_operators = sorted(clean_df['Operator_Clean'].dropna().unique().tolist())
selected_operators = st.sidebar.multiselect("Operator:", all_operators, default=all_operators)

# Filter Jenis Tes (DT / ST)
all_jenis_tes = sorted(clean_df['Jenis_Tes'].dropna().unique().tolist())
selected_jenis_tes = st.sidebar.multiselect("Jenis Pengukuran:", all_jenis_tes, default=all_jenis_tes)

# Terapkan Filter
filtered_df = clean_df[
    (clean_df['Event'].isin(selected_events)) &
    (clean_df['Kabupaten'].isin(selected_kabupaten)) &
    (clean_df['Operator_Clean'].isin(selected_operators)) &
    (clean_df['Jenis_Tes'].isin(selected_jenis_tes))
]

if filtered_df.empty:
    st.warning("⚠️ Tidak ada data yang sesuai dengan filter yang dipilih. Silakan sesuaikan kembali filter di sidebar.")
    st.stop()


# ==========================================
# 3. HEADER & KPI BANNER
# ==========================================
st.markdown(f"""
<div class="header-box">
    <div class="header-title">📊 Dashboard Visualisasi Kualitas Layanan Telekomunikasi (QoS)</div>
    <div class="header-desc">
        Monitoring & Evaluasi Kinerja Jaringan Seluler (Drive Test & Stationary Test) | Sumber Data: <b>{active_file_name}</b> | Filter Aktif: <b>{len(filtered_df)}</b> baris data
    </div>
</div>
""", unsafe_allow_html=True)

# KPI Metrics Header
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6, kpi7 = st.columns(7)

avg_dl = filtered_df['SpeedTest_DL_Avg_Mbps'].mean()
avg_ul = filtered_df['SpeedTest_UL_Avg_Mbps'].mean()
avg_lat = filtered_df['Ping_Avg_RTT_ms'].mean()
avg_wa_mos = filtered_df['WA_Call_Avg_MOS'].mean()
avg_rsrp = filtered_df['Signal_4G_RSRP'].mean()
avg_rsrq = filtered_df['Signal_4G_RSRQ'].mean()
total_loc = filtered_df['Lokasi_Pengukuran'].nunique()

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Kecepatan Unduh (DL)</div>
        <div class="metric-value">{avg_dl:.1f}<span class="metric-unit">Mbps</span></div>
        <div class="metric-footer" style="color: #10B981;">Rata-rata SpeedTest</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Kecepatan Unggah (UL)</div>
        <div class="metric-value">{avg_ul:.1f}<span class="metric-unit">Mbps</span></div>
        <div class="metric-footer" style="color: #3B82F6;">Rata-rata SpeedTest</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Latensi Ping (RTT)</div>
        <div class="metric-value">{avg_lat:.1f}<span class="metric-unit">ms</span></div>
        <div class="metric-footer" style="color: {'#10B981' if avg_lat < 100 else '#EF4444'};">{'Optimal (<100ms)' if avg_lat < 100 else 'Perlu Perhatian'}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Kualitas Suara (MOS)</div>
        <div class="metric-value">{avg_wa_mos:.2f}<span class="metric-unit">/ 5.0</span></div>
        <div class="metric-footer" style="color: #10B981;">WhatsApp Call MOS</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Kuat Sinyal (RSRP)</div>
        <div class="metric-value">{avg_rsrp:.1f}<span class="metric-unit">dBm</span></div>
        <div class="metric-footer" style="color: {'#10B981' if avg_rsrp > -95 else '#F59E0B'};">4G RSRP</div>
    </div>
    """, unsafe_allow_html=True)

with kpi6:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Kualitas Sinyal (RSRQ)</div>
        <div class="metric-value">{avg_rsrq:.1f}<span class="metric-unit">dB</span></div>
        <div class="metric-footer" style="color: {'#10B981' if avg_rsrq >= -12 else ('#3B82F6' if avg_rsrq >= -15 else '#F59E0B')};">4G RSRQ</div>
    </div>
    """, unsafe_allow_html=True)

with kpi7:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Titik Ukur</div>
        <div class="metric-value">{total_loc}<span class="metric-unit">Lokasi</span></div>
        <div class="metric-footer" style="color: #64748B;">{filtered_df['Kabupaten'].nunique()} Kab/Kota</div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 4. TABS ANALISIS
# ==========================================
tabs = st.tabs([
    "📊 Ringkasan & Scorecard",
    "🚀 Throughput & Kecepatan",
    "🌐 Latensi & Aplikasi OTT",
    "📞 Kualitas Suara & SMS",
    "📶 Kualitas & Cakupan Sinyal",
    "🗺️ Peta Spasial",
    "⚖️ Benchmarking Operator",
    "📋 Data Explorer & Export"
])


# -------------------------------------------------------------
# TAB 1: RINGKASAN & SCORECARD
# -------------------------------------------------------------
with tabs[0]:
    st.markdown("### 🏆 Leaderboard & Ringkasan Kinerja Operator")
    
    col_lead1, col_lead2 = st.columns([1.25, 0.75])
    
    with col_lead1:
        # Ringkasan Matriks Per Operator
        op_summary = filtered_df.groupby('Operator_Clean').agg(
            Avg_DL_Speed=('SpeedTest_DL_Avg_Mbps', 'mean'),
            Avg_UL_Speed=('SpeedTest_UL_Avg_Mbps', 'mean'),
            Avg_Ping_RTT=('Ping_Avg_RTT_ms', 'mean'),
            Avg_WA_MOS=('WA_Call_Avg_MOS', 'mean'),
            Avg_4G_RSRP=('Signal_4G_RSRP', 'mean'),
            Avg_4G_RSRQ=('Signal_4G_RSRQ', 'mean'),
            YouTube_Success=('YouTube_Success_Rate', 'mean'),
            Voice_Success=('Voice_Success_Rate', 'mean'),
            Sample_Count=('No', 'count')
        ).reset_index()

        # Format tampilan tabel
        display_summary = op_summary.copy()
        display_summary.columns = ['Operator', 'Rata-rata DL (Mbps)', 'Rata-rata UL (Mbps)', 'Ping RTT (ms)', 'WA MOS', '4G RSRP (dBm)', '4G RSRQ (dB)', 'YouTube Success (%)', 'Voice Success (%)', 'Total Sampel']
        
        st.dataframe(
            display_summary.style.format({
                'Rata-rata DL (Mbps)': '{:.2f}',
                'Rata-rata UL (Mbps)': '{:.2f}',
                'Ping RTT (ms)': '{:.1f}',
                'WA MOS': '{:.2f}',
                '4G RSRP (dBm)': '{:.1f}',
                '4G RSRQ (dB)': '{:.1f}',
                'YouTube Success (%)': '{:.1f}%',
                'Voice Success (%)': '{:.1f}%',
                'Total Sampel': '{:d}'
            }).highlight_max(subset=['Rata-rata DL (Mbps)', 'Rata-rata UL (Mbps)', 'WA MOS', '4G RSRP (dBm)', '4G RSRQ (dB)', 'YouTube Success (%)', 'Voice Success (%)'], color='#DCFCE7')
              .highlight_min(subset=['Ping RTT (ms)'], color='#DCFCE7'),
            use_container_width=True
        )

        st.markdown("#### 🎯 Kepatuhan Standar QoS (Komdigi & Regulasi)")
        c_kpi1, c_kpi2, c_kpi3, c_kpi4, c_kpi5 = st.columns(5)
        with c_kpi1:
            dl_compliance = (filtered_df['SpeedTest_DL_Avg_Mbps'] >= 20.0).mean() * 100
            st.metric("DL Speed ≥ 20 Mbps", f"{dl_compliance:.1f}%", delta="Standar Komdigi" if dl_compliance >= 80 else "- Perlu Optimasi")
        with c_kpi2:
            ping_compliance = (filtered_df['Ping_Avg_RTT_ms'] <= 150.0).mean() * 100
            st.metric("Latency Ping ≤ 150ms", f"{ping_compliance:.1f}%", delta="Bagus" if ping_compliance >= 90 else "- Tinggi")
        with c_kpi3:
            mos_compliance = (filtered_df['WA_Call_Avg_MOS'] >= 3.0).mean() * 100
            st.metric("MOS Suara ≥ 3.0", f"{mos_compliance:.1f}%", delta="Jernih" if mos_compliance >= 80 else "- Cukup")
        with c_kpi4:
            rsrp_compliance = (filtered_df['Signal_4G_RSRP'] >= -100.0).mean() * 100
            st.metric("4G RSRP ≥ -100 dBm", f"{rsrp_compliance:.1f}%", delta="Cakupan Baik" if rsrp_compliance >= 80 else "- Lemah")
        with c_kpi5:
            rsrq_compliance = (filtered_df['Signal_4G_RSRQ'] >= -15.0).mean() * 100
            st.metric("4G RSRQ ≥ -15 dB", f"{rsrq_compliance:.1f}%", delta="Kualitas Baik" if rsrq_compliance >= 80 else "- Cukup")

    with col_lead2:
        st.markdown("#### 🕸️ Radar Benchmark Multi-Dimensi")
        fig_radar = utils_viz.plot_radar_benchmark(filtered_df, height=380)
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📍 Top 5 dan Bottom 5 Lokasi Pengukuran (Berdasarkan Kecepatan Unduh)")
    c_top, c_bot = st.columns(2)
    
    loc_agg = filtered_df.groupby(['Kabupaten', 'Lokasi_Pengukuran', 'Operator_Clean'])['SpeedTest_DL_Avg_Mbps'].mean().reset_index().dropna()
    top5 = loc_agg.sort_values('SpeedTest_DL_Avg_Mbps', ascending=False).head(5)
    bot5 = loc_agg.sort_values('SpeedTest_DL_Avg_Mbps', ascending=True).head(5)

    with c_top:
        st.markdown("##### 🟢 5 Lokasi Pengukuran Tercepat")
        top_fig = px.bar(
            top5,
            x='SpeedTest_DL_Avg_Mbps',
            y='Lokasi_Pengukuran',
            color='Operator_Clean',
            orientation='h',
            color_discrete_map=utils_viz.OP_COLORS,
            labels={'SpeedTest_DL_Avg_Mbps': 'Download Speed (Mbps)', 'Lokasi_Pengukuran': 'Lokasi'},
            text_auto='.1f'
        )
        top_fig.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(l=10, r=10, t=10, b=10), height=260)
        st.plotly_chart(top_fig, use_container_width=True)

    with c_bot:
        st.markdown("##### 🔴 5 Lokasi Pengukuran Paling Lambat")
        bot_fig = px.bar(
            bot5,
            x='SpeedTest_DL_Avg_Mbps',
            y='Lokasi_Pengukuran',
            color='Operator_Clean',
            orientation='h',
            color_discrete_map=utils_viz.OP_COLORS,
            labels={'SpeedTest_DL_Avg_Mbps': 'Download Speed (Mbps)', 'Lokasi_Pengukuran': 'Lokasi'},
            text_auto='.1f'
        )
        bot_fig.update_layout(yaxis={'categoryorder': 'total descending'}, margin=dict(l=10, r=10, t=10, b=10), height=260)
        st.plotly_chart(bot_fig, use_container_width=True)


# -------------------------------------------------------------
# TAB 2: THROUGHPUT & KECEPATAN
# -------------------------------------------------------------
with tabs[1]:
    st.markdown("### 🚀 Analisis Throughput & Kecepatan Pengunduhan / Pengunggahan")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        fig_dl = utils_viz.plot_operator_bar(
            filtered_df,
            'SpeedTest_DL_Avg_Mbps',
            'Kecepatan Unduh SpeedTest (Rata-rata & Median)',
            'Download Speed',
            'Mbps',
            higher_is_better=True
        )
        st.plotly_chart(fig_dl, use_container_width=True)

    with col_t2:
        fig_ul = utils_viz.plot_operator_bar(
            filtered_df,
            'SpeedTest_UL_Avg_Mbps',
            'Kecepatan Unggah SpeedTest (Rata-rata & Median)',
            'Upload Speed',
            'Mbps',
            higher_is_better=True
        )
        st.plotly_chart(fig_ul, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🏢 Perbandingan Kecepatan Unduh SpeedTest per Kabupaten / Kota")
    fig_kab_dl = utils_viz.plot_grouped_by_kabupaten(
        filtered_df,
        'SpeedTest_DL_Avg_Mbps',
        'Rata-rata SpeedTest DL (Mbps) per Wilayah',
        'Download Speed',
        'Mbps',
        height=420
    )
    st.plotly_chart(fig_kab_dl, use_container_width=True)

    st.markdown("---")
    col_box1, col_box2 = st.columns(2)
    with col_box1:
        st.markdown("#### 📦 Distribusi Kecepatan Unduh (Box Plot)")
        fig_box_dl = utils_viz.plot_speed_distribution_box(
            filtered_df,
            'SpeedTest_DL_Avg_Mbps',
            'Distribusi Throughput DL (Mbps)',
            'Throughput DL',
            'Mbps'
        )
        st.plotly_chart(fig_box_dl, use_container_width=True)

    with col_box2:
        st.markdown("#### 📦 Distribusi Kecepatan Unggah (Box Plot)")
        fig_box_ul = utils_viz.plot_speed_distribution_box(
            filtered_df,
            'SpeedTest_UL_Avg_Mbps',
            'Distribusi Throughput UL (Mbps)',
            'Throughput UL',
            'Mbps'
        )
        st.plotly_chart(fig_box_ul, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔄 Perbandingan Protokol Pengukuran (SpeedTest vs FTP vs Capacity vs HTTP)")
    proto_summary = filtered_df.groupby('Operator_Clean').agg(
        SpeedTest_DL=('SpeedTest_DL_Avg_Mbps', 'mean'),
        FTP_DL=('FTP_DL_Avg_Mbps', 'mean'),
        Capacity_DL=('Capacity_DL_Avg_Mbps', 'mean'),
        HTTP_DL=('HTTP_DL_Avg_Mbps', 'mean'),
        SpeedTest_UL=('SpeedTest_UL_Avg_Mbps', 'mean'),
        FTP_UL=('FTP_UL_Avg_Mbps', 'mean'),
        Capacity_UL=('Capacity_UL_Avg_Mbps', 'mean'),
        HTTP_UL=('HTTP_UL_Avg_Mbps', 'mean')
    ).reset_index()

    proto_melted = pd.melt(
        proto_summary,
        id_vars=['Operator_Clean'],
        value_vars=['SpeedTest_DL', 'FTP_DL', 'Capacity_DL', 'HTTP_DL'],
        var_name='Metode Pengujian',
        value_name='Kecepatan Rata-rata (Mbps)'
    )

    fig_proto = px.bar(
        proto_melted,
        x='Metode Pengujian',
        y='Kecepatan Rata-rata (Mbps)',
        color='Operator_Clean',
        barmode='group',
        color_discrete_map=utils_viz.OP_COLORS,
        text_auto='.2f'
    )
    fig_proto = utils_viz.apply_custom_layout(fig_proto, "Perbandingan Kecepatan Pengunduhan Berdasarkan Protokol", height=380)
    st.plotly_chart(fig_proto, use_container_width=True)


# -------------------------------------------------------------
# TAB 3: LATENSI & PENGALAMAN APLIKASI OTT
# -------------------------------------------------------------
with tabs[2]:
    st.markdown("### 🌐 Latensi Jaringan, Web Browsing, dan Pengalaman Aplikasi OTT")
    
    col_lat1, col_lat2 = st.columns(2)
    with col_lat1:
        fig_ping = utils_viz.plot_operator_bar(
            filtered_df,
            'Ping_Avg_RTT_ms',
            'Rata-rata Latensi Ping RTT (ms) - Makin Kecil Makin Bagus',
            'Ping Latency',
            'ms',
            higher_is_better=False
        )
        st.plotly_chart(fig_ping, use_container_width=True)

    with col_lat2:
        fig_browsing = utils_viz.plot_operator_bar(
            filtered_df,
            'Browsing_Avg_Speed_Mbps',
            'Rata-rata Kecepatan Web Browsing (Mbps)',
            'Browsing Speed',
            'Mbps',
            higher_is_better=True
        )
        st.plotly_chart(fig_browsing, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📺 Kinerja Streaming Video YouTube")
    col_yt1, col_yt2 = st.columns([1.1, 0.9])
    
    with col_yt1:
        fig_yt_res = utils_viz.plot_youtube_resolutions(filtered_df, height=360)
        st.plotly_chart(fig_yt_res, use_container_width=True)

    with col_yt2:
        yt_metrics = filtered_df.groupby('Operator_Clean').agg(
            Success_Rate=('YouTube_Success_Rate', 'mean'),
            Avg_TTFP_Sec=('YouTube_Avg_TTFP_s', 'mean'),
            Freezing_Ratio=('YouTube_Freezing_Ratio', 'mean'),
            Visual_Quality=('YouTube_Visual_Quality', 'mean')
        ).reset_index()

        st.markdown("##### 📊 Metrik Kualitas Pemutaran YouTube")
        st.dataframe(
            yt_metrics.style.format({
                'Success_Rate': '{:.1f}%',
                'Avg_TTFP_Sec': '{:.2f} s',
                'Freezing_Ratio': '{:.2f}%',
                'Visual_Quality': '{:.2f}'
            }),
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("#### 📱 Kinerja Media Sosial & Pesan Instan (Instagram & WhatsApp)")
    col_soc1, col_soc2 = st.columns(2)
    
    with col_soc1:
        ig_summary = filtered_df.groupby('Operator_Clean').agg(
            Pic_Speed=('IG_Pic_Avg_Speed_Mbps', 'mean'),
            Pic_Duration=('IG_Pic_Avg_Duration_s', 'mean'),
            Video_Speed=('IG_Video_Avg_Speed_Mbps', 'mean'),
            Video_Duration=('IG_Video_Avg_Duration_s', 'mean')
        ).reset_index()

        fig_ig = px.bar(
            ig_summary,
            x='Operator_Clean',
            y=['Pic_Speed', 'Video_Speed'],
            barmode='group',
            labels={'Operator_Clean': 'Operator', 'value': 'Kecepatan Unggah IG (Mbps)', 'variable': 'Konten IG'},
            title="<b>Kecepatan Unggah Post Instagram (Foto vs Video)</b>"
        )
        fig_ig = utils_viz.apply_custom_layout(fig_ig, "Kecepatan Unggah Post Instagram (Foto vs Video)", height=340)
        st.plotly_chart(fig_ig, use_container_width=True)

    with col_soc2:
        wa_summary = filtered_df.groupby('Operator_Clean').agg(
            WA_MOS=('WA_Call_Avg_MOS', 'mean'),
            WA_CST_Sec=('WA_Call_Avg_CST_s', 'mean'),
            WA_Success_Rate=('WA_Call_Success_Rate', 'mean'),
            WA_Msg_Duration=('WA_Msg_Avg_Duration_s', 'mean')
        ).reset_index()

        fig_wa = px.bar(
            wa_summary,
            x='Operator_Clean',
            y='WA_MOS',
            color='Operator_Clean',
            color_discrete_map=utils_viz.OP_COLORS,
            text_auto='.2f',
            labels={'Operator_Clean': 'Operator', 'WA_MOS': 'Mean Opinion Score (MOS)'}
        )
        fig_wa = utils_viz.apply_custom_layout(fig_wa, "Kualitas Suara WhatsApp Call (MOS)", height=340)
        st.plotly_chart(fig_wa, use_container_width=True)


# -------------------------------------------------------------
# TAB 4: KUALITAS SUARA & SMS
# -------------------------------------------------------------
with tabs[3]:
    st.markdown("### 📞 Kinerja Kualitas Layanan Suara (Voice Call) & SMS")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        fig_voice_mos = utils_viz.plot_operator_bar(
            filtered_df,
            'Voice_Avg_MOS',
            'Rata-rata Skor Suara Voice Call (MOS)',
            'Voice MOS',
            '',
            higher_is_better=True
        )
        st.plotly_chart(fig_voice_mos, use_container_width=True)

    with col_v2:
        fig_voice_cst = utils_viz.plot_operator_bar(
            filtered_df,
            'Voice_Avg_CST_s',
            'Rata-rata Waktu Pembentukan Panggilan (CST) - Detik',
            'Call Setup Time',
            'detik',
            higher_is_better=False
        )
        st.plotly_chart(fig_voice_cst, use_container_width=True)

    st.markdown("---")
    st.markdown("#### ⚖️ Perbandingan Panggilan Suara Onnet vs Offnet")
    col_net1, col_net2 = st.columns(2)
    
    with col_net1:
        voice_net_summary = filtered_df.groupby('Operator_Clean').agg(
            Onnet_Success=('Voice_Onnet_Success_Rate', 'mean'),
            Offnet_Success=('Voice_Offnet_Success_Rate', 'mean'),
            Onnet_Blocked=('Voice_Onnet_Blocked_Rate', 'mean'),
            Offnet_Blocked=('Voice_Offnet_Blocked_Rate', 'mean'),
            Onnet_Dropped=('Voice_Onnet_Dropped_Rate', 'mean'),
            Offnet_Dropped=('Voice_Offnet_Dropped_Rate', 'mean')
        ).reset_index()

        st.markdown("##### 📋 Tingkat Keberhasilan Panggilan Suara (CSSR)")
        st.dataframe(
            voice_net_summary.style.format({
                'Onnet_Success': '{:.2f}%',
                'Offnet_Success': '{:.2f}%',
                'Onnet_Blocked': '{:.2f}%',
                'Offnet_Blocked': '{:.2f}%',
                'Onnet_Dropped': '{:.2f}%',
                'Offnet_Dropped': '{:.2f}%'
            }),
            use_container_width=True
        )

    with col_net2:
        sms_summary = filtered_df.groupby('Operator_Clean').agg(
            SMS_Onnet_Success=('SMS_Onnet_Success_LE_1min_Rate', 'mean'),
            SMS_Offnet_Success=('SMS_Offnet_Success_LE_1min_Rate', 'mean')
        ).reset_index()

        st.markdown("##### 📩 Pengiriman SMS < 1 Menit (%)")
        st.dataframe(
            sms_summary.style.format({
                'SMS_Onnet_Success': '{:.2f}%',
                'SMS_Offnet_Success': '{:.2f}%'
            }),
            use_container_width=True
        )


# -------------------------------------------------------------
# TAB 5: KUALITAS & CAKUPAN SINYAL (RF)
# -------------------------------------------------------------
with tabs[4]:
    st.markdown("### 📶 Analisis Kualitas & Cakupan Sinyal Radio Frekuensi (RF 4G / 5G / 2G)")
    
    col_rf1, col_rf2, col_rf3 = st.columns(3)
    with col_rf1:
        fig_rsrp = utils_viz.plot_operator_bar(
            filtered_df,
            'Signal_4G_RSRP',
            '4G RSRP (Kuat Sinyal - dBm)',
            '4G RSRP',
            'dBm',
            higher_is_better=True,
            height=340
        )
        st.plotly_chart(fig_rsrp, use_container_width=True)

    with col_rf2:
        fig_rsrq = utils_viz.plot_operator_bar(
            filtered_df,
            'Signal_4G_RSRQ',
            '4G RSRQ (Kualitas Sinyal - dB)',
            '4G RSRQ',
            'dB',
            higher_is_better=True,
            height=340
        )
        st.plotly_chart(fig_rsrq, use_container_width=True)

    with col_rf3:
        fig_sinr = utils_viz.plot_operator_bar(
            filtered_df,
            'Signal_4G_SINR',
            '4G SINR (Interferensi - dB)',
            '4G SINR',
            'dB',
            higher_is_better=True,
            height=340
        )
        st.plotly_chart(fig_sinr, use_container_width=True)

    st.markdown("---")
    col_cat1, col_cat2, col_cat3 = st.columns(3)
    with col_cat1:
        st.markdown("#### 🎯 Kategori Kuat Sinyal 4G RSRP")
        fig_cat_rsrp = utils_viz.plot_signal_category_distribution(
            filtered_df,
            signal_col='Signal_4G_RSRP_Cat',
            title="Kategori Kuat Sinyal (RSRP)",
            height=340
        )
        st.plotly_chart(fig_cat_rsrp, use_container_width=True)

    with col_cat2:
        st.markdown("#### 🎯 Kategori Kualitas Sinyal 4G RSRQ")
        fig_cat_rsrq = utils_viz.plot_signal_category_distribution(
            filtered_df,
            signal_col='Signal_4G_RSRQ_Cat',
            title="Kategori Kualitas Sinyal (RSRQ)",
            height=340
        )
        st.plotly_chart(fig_cat_rsrq, use_container_width=True)

    with col_cat3:
        st.markdown("#### 🎯 Kategori Sinyal 4G SINR")
        fig_cat_sinr = utils_viz.plot_signal_category_distribution(
            filtered_df,
            signal_col='Signal_4G_SINR_Cat',
            title="Kategori SINR (Interferensi)",
            height=340
        )
        st.plotly_chart(fig_cat_sinr, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔍 Matriks Korelasi Sinyal RF (Kuat vs Kualitas)")
    col_scat1, col_scat2 = st.columns(2)
    with col_scat1:
        fig_scat_rsrq = utils_viz.plot_rsrp_rsrq_scatter(filtered_df, height=380)
        st.plotly_chart(fig_scat_rsrq, use_container_width=True)

    with col_scat2:
        fig_scat_sinr = utils_viz.plot_rsrp_sinr_scatter(filtered_df, height=380)
        st.plotly_chart(fig_scat_sinr, use_container_width=True)

    st.markdown("---")
    st.markdown("#### ⚠️ Persentase Sampel Sinyal Buruk (Bad Coverage & Bad Quality Samples)")
    bad_summary = filtered_df.groupby('Operator_Clean').agg(
        Bad_RSRP_Rate=('Signal_4G_Bad_RSRP_Rate', 'mean'),
        Bad_RSRQ_Rate=('Signal_4G_Bad_RSRQ_Rate', 'mean'),
        Bad_SINR_Rate=('Signal_4G_Bad_SINR_Rate', 'mean'),
        Total_Samples=('Signal_4G_Total_RSRP_Sample', 'sum')
    ).reset_index()

    st.dataframe(
        bad_summary.style.format({
            'Bad_RSRP_Rate': '{:.2f}%',
            'Bad_RSRQ_Rate': '{:.2f}%',
            'Bad_SINR_Rate': '{:.2f}%',
            'Total_Samples': '{:,.0f}'
        }).highlight_min(subset=['Bad_RSRP_Rate', 'Bad_RSRQ_Rate', 'Bad_SINR_Rate'], color='#DCFCE7')
          .highlight_max(subset=['Bad_RSRP_Rate', 'Bad_RSRQ_Rate', 'Bad_SINR_Rate'], color='#FEE2E2'),
        use_container_width=True
    )


# -------------------------------------------------------------
# TAB 6: PETA SPASIAL
# -------------------------------------------------------------
with tabs[5]:
    st.markdown("### 🗺️ Peta Spasial Distribusi Titik Pengukuran & Drive Test QoS")
    
    col_map_opt1, col_map_opt2 = st.columns([1, 3])
    with col_map_opt1:
        map_color_mode = st.radio(
            "Skema Warna Marker:",
            [
                "Berdasarkan Operator",
                "Berdasarkan Kecepatan Unduh (DL Speed)",
                "Berdasarkan Kuat Sinyal (4G RSRP)",
                "Berdasarkan Kualitas Sinyal (4G RSRQ)"
            ],
            index=0
        )
        color_key = 'operator'
        if 'Kecepatan' in map_color_mode:
            color_key = 'speed'
        elif 'Kuat Sinyal' in map_color_mode:
            color_key = 'rsrp'
        elif 'Kualitas Sinyal' in map_color_mode:
            color_key = 'rsrq'

        st.info("""
        **Keterangan Marker:**
        - **Merah**: TELKOMSEL / Sinyal Lemah (< -105 dBm) / RSRQ Buruk (< -19.5 dB) / Speed < 20 Mbps
        - **Kuning/Orange**: IOH / Sinyal Cukup / RSRQ Cukup (-19.5 s/d -15 dB) / Speed 20-50 Mbps
        - **Biru**: XLSMART / Sinyal Baik / RSRQ Baik (-15 s/d -10 dB) / Speed 50-100 Mbps
        - **Hijau**: Sinyal Sangat Baik / RSRQ Sangat Baik (≥ -10 dB) / Speed ≥ 100 Mbps
        - **Ikon Mobil**: Drive Test (DT)
        - **Ikon Pin**: Stationary Test (ST)
        """)

    with col_map_opt2:
        qos_map = utils_map.create_qos_map(filtered_df, color_by=color_key)
        st_folium(qos_map, width="100%", height=560, returned_objects=[])


# -------------------------------------------------------------
# TAB 7: BENCHMARKING OPERATOR
# -------------------------------------------------------------
with tabs[6]:
    st.markdown("### ⚖️ Perbandingan Head-to-Head & Peringkat Operator per Wilayah")
    
    selected_kab_bench = st.selectbox(
        "Pilih Wilayah Kabupaten / Kota untuk Analisis Spesifik:",
        ["Semua Wilayah"] + all_kabupaten
    )

    bench_df = filtered_df if selected_kab_bench == "Semua Wilayah" else filtered_df[filtered_df['Kabupaten'] == selected_kab_bench]

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown(f"#### 📊 Throughput DL & UL di {selected_kab_bench}")
        fig_b_dl = px.bar(
            bench_df.groupby('Operator_Clean')[['SpeedTest_DL_Avg_Mbps', 'SpeedTest_UL_Avg_Mbps']].mean().reset_index(),
            x='Operator_Clean',
            y=['SpeedTest_DL_Avg_Mbps', 'SpeedTest_UL_Avg_Mbps'],
            barmode='group',
            labels={'Operator_Clean': 'Operator', 'value': 'Kecepatan (Mbps)', 'variable': 'Metrik'},
            text_auto='.1f'
        )
        fig_b_dl = utils_viz.apply_custom_layout(fig_b_dl, f"Perbandingan Kecepatan DL & UL ({selected_kab_bench})", height=350)
        st.plotly_chart(fig_b_dl, use_container_width=True)

    with col_b2:
        st.markdown(f"#### 📶 Kuat (RSRP) & Kualitas Sinyal (RSRQ) di {selected_kab_bench}")
        bench_rf = bench_df.groupby('Operator_Clean')[['Signal_4G_RSRP', 'Signal_4G_RSRQ']].mean().reset_index()

        fig_b_rf = px.bar(
            bench_rf,
            x='Operator_Clean',
            y=['Signal_4G_RSRP', 'Signal_4G_RSRQ'],
            barmode='group',
            labels={'Operator_Clean': 'Operator', 'value': 'Nilai RF (dBm / dB)', 'variable': 'Parameter RF'},
            text_auto='.1f'
        )
        fig_b_rf = utils_viz.apply_custom_layout(fig_b_rf, f"Parameter Sinyal 4G RSRP & RSRQ ({selected_kab_bench})", height=350)
        st.plotly_chart(fig_b_rf, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📋 Matriks Komparasi Lengkap per Kabupaten / Kota")
    full_kab_matrix = filtered_df.groupby(['Kabupaten', 'Operator_Clean']).agg(
        Speed_DL=('SpeedTest_DL_Avg_Mbps', 'mean'),
        Speed_UL=('SpeedTest_UL_Avg_Mbps', 'mean'),
        Ping_RTT=('Ping_Avg_RTT_ms', 'mean'),
        WA_MOS=('WA_Call_Avg_MOS', 'mean'),
        RSRP_4G=('Signal_4G_RSRP', 'mean'),
        RSRQ_4G=('Signal_4G_RSRQ', 'mean'),
        YouTube_SR=('YouTube_Success_Rate', 'mean')
    ).reset_index()

    st.dataframe(
        full_kab_matrix.style.format({
            'Speed_DL': '{:.2f} Mbps',
            'Speed_UL': '{:.2f} Mbps',
            'Ping_RTT': '{:.1f} ms',
            'WA_MOS': '{:.2f}',
            'RSRP_4G': '{:.1f} dBm',
            'RSRQ_4G': '{:.1f} dB',
            'YouTube_SR': '{:.1f}%'
        }),
        use_container_width=True
    )


# -------------------------------------------------------------
# TAB 8: DATA EXPLORER & EXPORT
# -------------------------------------------------------------
with tabs[7]:
    st.markdown("### 📋 Eksplorasi Data Mentah & Unduh Laporan")
    
    # Opsi Kolom yang Ingin Ditampilkan
    all_clean_cols = filtered_df.columns.tolist()
    default_show_cols = [
        'No', 'Provinsi', 'Kabupaten', 'Jenis_Tes', 'Lokasi_Pengukuran', 'Tanggal_Pengukuran', 'Operator_Clean',
        'SpeedTest_DL_Avg_Mbps', 'SpeedTest_UL_Avg_Mbps', 'Ping_Avg_RTT_ms', 'YouTube_Success_Rate',
        'WA_Call_Avg_MOS', 'Signal_4G_RSRP', 'Signal_4G_RSRQ', 'Signal_4G_RSRQ_Cat', 'Signal_4G_SINR', 'Lat', 'Long', 'Distance_Km'
    ]
    default_show_cols = [c for c in default_show_cols if c in all_clean_cols]

    selected_cols = st.multiselect("Pilih Kolom Tampilan:", all_clean_cols, default=default_show_cols)

    search_query = st.text_input("🔍 Cari Lokasi / Kata Kunci:", "")
    view_df = filtered_df[selected_cols]
    
    if search_query:
        mask = filtered_df.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
        view_df = filtered_df[mask][selected_cols]

    st.dataframe(view_df, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 💾 Unduh Data Terfilter")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Unduh Data sebagai CSV",
            data=csv_data,
            file_name=f"QoS_Filtered_Data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )

    with col_exp2:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='QoS_Clean_Data')
            # Tambahkan sheet raw jika ada
            if not raw_full_df.empty:
                raw_full_df.to_excel(writer, index=False, sheet_name='QoS_Raw_MultiHeader')
        
        st.download_button(
            label="📥 Unduh Data sebagai Excel (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name=f"QoS_Filtered_Report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
