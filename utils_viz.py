"""
utils_viz.py - Modul pembuat visualisasi grafik interaktif Plotly untuk Dashboard QoS.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from data_loader import get_operator_color, get_operator_palette


# Standar palet warna
OP_COLORS = {
    'TELKOMSEL': '#E60000',
    'IOH': '#F5A623',
    'XLSMART': '#0070F3',
    'TSEL': '#E60000',
    'XLS': '#0070F3'
}

QUALITY_COLORS = {
    'Baik Sekali': '#10B981',
    'Baik': '#3B82F6',
    'Cukup': '#F59E0B',
    'Kurang': '#EF4444',
    'Buruk': '#7F1D1D',
    'No Data': '#9CA3AF'
}


def apply_custom_layout(fig, title="", height=400):
    """Menerapkan styling modern yang konsisten ke grafik Plotly."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=15, color='#1E293B'),
            x=0.01,
            y=0.96
        ),
        margin=dict(l=20, r=20, t=50 if title else 20, b=20),
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248,250,252,0.6)',
        hovermode='x unified',
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=12, color='#475569'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(226,232,240,0.8)',
            borderwidth=1
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(226,232,240,0.8)',
            linecolor='#CBD5E1'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(226,232,240,0.8)',
            linecolor='#CBD5E1'
        )
    )
    return fig


def plot_operator_bar(df, metric_col, title, y_title, unit="", higher_is_better=True, height=360):
    """Membuat grafik bar perbandingan rata-rata metrik antar operator."""
    sub_df = df.dropna(subset=[metric_col])
    if sub_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Data Tidak Tersedia", showarrow=False, font=dict(size=14, color="#94A3B8"))
        return apply_custom_layout(fig, title, height)

    agg = sub_df.groupby('Operator_Clean')[metric_col].agg(['mean', 'median', 'count']).reset_index()
    agg = agg.sort_values('mean', ascending=not higher_is_better)

    fig = go.Figure()
    for _, row in agg.iterrows():
        op = row['Operator_Clean']
        val = row['mean']
        med = row['median']
        cnt = row['count']
        color = OP_COLORS.get(op, '#64748B')
        
        fig.add_trace(go.Bar(
            x=[op],
            y=[val],
            name=op,
            marker_color=color,
            text=f"<b>{val:.2f} {unit}</b><br>(Med: {med:.2f})",
            textposition='outside',
            hovertemplate=f"<b>{op}</b><br>Rata-rata: {val:.2f} {unit}<br>Median: {med:.2f} {unit}<br>Sampel: {cnt}<extra></extra>"
        ))

    fig.update_layout(
        yaxis_title=f"{y_title} ({unit})" if unit else y_title,
        showlegend=False
    )
    return apply_custom_layout(fig, title, height)


def plot_grouped_by_kabupaten(df, metric_col, title, y_title, unit="", height=420):
    """Membuat grouped bar chart membandingkan operator di tiap Kabupaten/Kota."""
    sub_df = df.dropna(subset=[metric_col])
    if sub_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Data Tidak Tersedia", showarrow=False, font=dict(size=14, color="#94A3B8"))
        return apply_custom_layout(fig, title, height)

    agg = sub_df.groupby(['Kabupaten', 'Operator_Clean'])[metric_col].mean().reset_index()

    fig = px.bar(
        agg,
        x='Kabupaten',
        y=metric_col,
        color='Operator_Clean',
        barmode='group',
        color_discrete_map=OP_COLORS,
        text_auto='.2f',
        labels={'Kabupaten': 'Kabupaten / Kota', metric_col: f'{y_title} ({unit})' if unit else y_title, 'Operator_Clean': 'Operator'}
    )
    fig.update_traces(textposition='outside', textfont_size=10)
    fig.update_layout(xaxis_tickangle=-30)
    return apply_custom_layout(fig, title, height)


def plot_speed_distribution_box(df, metric_col, title, y_title, unit="Mbps", height=380):
    """Membuat box plot distribusi nilai metrik per operator."""
    sub_df = df.dropna(subset=[metric_col])
    if sub_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Data Tidak Tersedia", showarrow=False, font=dict(size=14, color="#94A3B8"))
        return apply_custom_layout(fig, title, height)

    fig = px.box(
        sub_df,
        x='Operator_Clean',
        y=metric_col,
        color='Operator_Clean',
        color_discrete_map=OP_COLORS,
        points="all",
        hover_data=['Kabupaten', 'Jenis_Tes', 'Lokasi_Pengukuran'],
        labels={'Operator_Clean': 'Operator', metric_col: f'{y_title} ({unit})' if unit else y_title}
    )
    fig.update_layout(showlegend=False)
    return apply_custom_layout(fig, title, height)


def plot_radar_benchmark(df, height=450):
    """Membuat Radar Chart komparasi multi-dimensi komprehensif antar operator."""
    operators = df['Operator_Clean'].unique().tolist()
    if not operators:
        fig = go.Figure()
        fig.add_annotation(text="Data Tidak Tersedia", showarrow=False)
        return fig

    # Dimensi yang dinilai & dinormalisasi (0 - 100)
    dimensions = [
        'SpeedTest DL Speed',
        'SpeedTest UL Speed',
        'Latency (Ping RTT)',
        'YouTube Success Rate',
        'WhatsApp MOS',
        '4G RSRP (Kuat Sinyal)',
        '4G RSRQ (Kualitas Sinyal)',
        'Voice Success Rate'
    ]

    fig = go.Figure()

    # Cari max/min global untuk normalisasi
    max_dl = max(df['SpeedTest_DL_Avg_Mbps'].quantile(0.95), 100)
    max_ul = max(df['SpeedTest_UL_Avg_Mbps'].quantile(0.95), 40)
    min_lat = 20
    max_lat = max(df['Ping_Avg_RTT_ms'].quantile(0.95), 150)

    for op in operators:
        op_df = df[df['Operator_Clean'] == op]
        if op_df.empty:
            continue

        dl_val = op_df['SpeedTest_DL_Avg_Mbps'].mean()
        ul_val = op_df['SpeedTest_UL_Avg_Mbps'].mean()
        lat_val = op_df['Ping_Avg_RTT_ms'].mean()
        yt_val = op_df['YouTube_Success_Rate'].mean()
        wa_val = op_df['WA_Call_Avg_MOS'].mean()
        rsrp_val = op_df['Signal_4G_RSRP'].mean()
        rsrq_val = op_df['Signal_4G_RSRQ'].mean()
        voice_val = op_df['Voice_Success_Rate'].mean()

        # Skor normalisasi (0 - 100)
        s_dl = min(100, (dl_val / max_dl) * 100) if pd.notna(dl_val) else 50
        s_ul = min(100, (ul_val / max_ul) * 100) if pd.notna(ul_val) else 50
        # Latensi: makin kecil makin bagus
        s_lat = max(0, 100 - ((lat_val - min_lat) / (max_lat - min_lat)) * 100) if pd.notna(lat_val) else 50
        s_yt = yt_val if pd.notna(yt_val) else 80
        # MOS: skala 1 - 5 ke skala 0 - 100
        s_wa = min(100, max(0, ((wa_val - 1) / 4) * 100)) if pd.notna(wa_val) else 70
        # RSRP: -120 s/d -70 dBm
        s_rsrp = min(100, max(0, ((rsrp_val - (-120)) / 50) * 100)) if pd.notna(rsrp_val) else 60
        # RSRQ: -20 s/d -5 dB
        s_rsrq = min(100, max(0, ((rsrq_val - (-20)) / 15) * 100)) if pd.notna(rsrq_val) else 60
        s_voice = voice_val if pd.notna(voice_val) else 90

        scores = [s_dl, s_ul, s_lat, s_yt, s_wa, s_rsrp, s_rsrq, s_voice]
        scores_closed = scores + [scores[0]]
        dims_closed = dimensions + [dimensions[0]]

        color = OP_COLORS.get(op, '#64748B')

        fig.add_trace(go.Scatterpolar(
            r=scores_closed,
            theta=dims_closed,
            fill='toself',
            name=op,
            line=dict(color=color, width=2),
            opacity=0.6,
            hovertemplate=f"<b>{op}</b><br>%{{theta}}: %{{r:.1f}} / 100<extra></extra>"
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='#E2E8F0'),
            angularaxis=dict(gridcolor='#E2E8F0', linecolor='#CBD5E1')
        ),
        margin=dict(l=40, r=40, t=50, b=40),
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=11, color='#334155'),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    return fig


def plot_youtube_resolutions(df, height=360):
    """Membuat stacked horizontal bar perbandingan kualitas resolusi YouTube per Operator."""
    res_cols = {
        'YouTube_1080p_HD_Rate': '1080p HD',
        'YouTube_720p_Rate': '720p',
        'YouTube_480p_Rate': '480p',
        'YouTube_360p_Rate': '360p',
        'YouTube_240p_Rate': '240p',
        'YouTube_144p_Rate': '144p'
    }
    
    palette_res = {
        '1080p HD': '#10B981',
        '720p': '#3B82F6',
        '480p': '#6366F1',
        '360p': '#F59E0B',
        '240p': '#F97316',
        '144p': '#EF4444'
    }

    operators = df['Operator_Clean'].unique().tolist()
    if not operators:
        fig = go.Figure()
        return fig

    rows = []
    for op in operators:
        op_df = df[df['Operator_Clean'] == op]
        for col, label in res_cols.items():
            val = op_df[col].mean()
            if pd.notna(val):
                rows.append({'Operator': op, 'Resolusi': label, 'Persentase': val})

    if not rows:
        fig = go.Figure()
        fig.add_annotation(text="Data Resolusi YouTube Tidak Tersedia", showarrow=False)
        return apply_custom_layout(fig, "Distribusi Resolusi YouTube", height)

    plot_df = pd.DataFrame(rows)
    fig = px.bar(
        plot_df,
        x='Persentase',
        y='Operator',
        color='Resolusi',
        orientation='h',
        color_discrete_map=palette_res,
        labels={'Persentase': 'Proporsi (%)', 'Operator': 'Operator'},
        text_auto='.1f'
    )
    fig.update_layout(barmode='stack', xaxis=dict(range=[0, 100]))
    return apply_custom_layout(fig, "Distribusi Resolusi Video YouTube (%)", height)


def plot_signal_category_distribution(df, signal_col='Signal_4G_RSRP_Cat', title="Kategori Sinyal 4G RSRP", height=350):
    """Membuat bar chart distribusi kategori kualitas sinyal (Baik Sekali, Baik, Cukup, Kurang)."""
    sub_df = df.dropna(subset=[signal_col])
    if sub_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Data Kategori Sinyal Tidak Tersedia", showarrow=False)
        return apply_custom_layout(fig, title, height)

    counts = sub_df.groupby(['Operator_Clean', signal_col]).size().reset_index(name='Jumlah')
    totals = sub_df.groupby('Operator_Clean').size().reset_index(name='Total')
    counts = counts.merge(totals, on='Operator_Clean')
    counts['Persentase'] = (counts['Jumlah'] / counts['Total']) * 100

    fig = px.bar(
        counts,
        x='Operator_Clean',
        y='Persentase',
        color=signal_col,
        barmode='stack',
        color_discrete_map=QUALITY_COLORS,
        labels={'Operator_Clean': 'Operator', 'Persentase': 'Persentase (%)', signal_col: 'Kategori Sinyal'},
        text_auto='.1f'
    )
    fig.update_layout(yaxis=dict(range=[0, 100]))
    return apply_custom_layout(fig, title, height)


def plot_rsrp_sinr_scatter(df, height=380):
    """Scatter plot hubungan antara RSRP (Kuat Sinyal) vs SINR (Kualitas Interferensi)."""
    sub_df = df.dropna(subset=['Signal_4G_RSRP', 'Signal_4G_SINR'])
    if sub_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Data RF RSRP & SINR Tidak Tersedia", showarrow=False)
        return apply_custom_layout(fig, "RSRP vs SINR Correlation", height)

    fig = px.scatter(
        sub_df,
        x='Signal_4G_RSRP',
        y='Signal_4G_SINR',
        color='Operator_Clean',
        color_discrete_map=OP_COLORS,
        hover_data=['Kabupaten', 'Lokasi_Pengukuran', 'Jenis_Tes', 'SpeedTest_DL_Avg_Mbps'],
        labels={'Signal_4G_RSRP': '4G RSRP (dBm) - Kuat Sinyal', 'Signal_4G_SINR': '4G SINR (dB) - Kualitas/Interferensi', 'Operator_Clean': 'Operator'}
    )
    # Garis ambang batas standar Komdigi / 3GPP
    fig.add_vline(x=-95, line_width=1.5, line_dash="dash", line_color="#F59E0B", annotation_text="Batas Cukup (-95 dBm)", annotation_position="top right")
    fig.add_vline(x=-110, line_width=1.5, line_dash="dot", line_color="#EF4444", annotation_text="Batas Buruk (-110 dBm)", annotation_position="top left")
    fig.add_hline(y=0, line_width=1.5, line_dash="dash", line_color="#EF4444", annotation_text="SINR < 0 dB", annotation_position="bottom right")

    return apply_custom_layout(fig, "Matriks Kuat Sinyal (RSRP) vs Kualitas (SINR)", height)


def plot_rsrp_rsrq_scatter(df, height=380):
    """Scatter plot hubungan antara RSRP (Kuat Sinyal) vs RSRQ (Kualitas Sinyal)."""
    sub_df = df.dropna(subset=['Signal_4G_RSRP', 'Signal_4G_RSRQ'])
    if sub_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Data RF RSRP & RSRQ Tidak Tersedia", showarrow=False)
        return apply_custom_layout(fig, "RSRP vs RSRQ Correlation", height)

    fig = px.scatter(
        sub_df,
        x='Signal_4G_RSRP',
        y='Signal_4G_RSRQ',
        color='Operator_Clean',
        color_discrete_map=OP_COLORS,
        hover_data=['Kabupaten', 'Lokasi_Pengukuran', 'Jenis_Tes', 'SpeedTest_DL_Avg_Mbps'],
        labels={'Signal_4G_RSRP': '4G RSRP (dBm) - Kuat Sinyal', 'Signal_4G_RSRQ': '4G RSRQ (dB) - Kualitas Sinyal', 'Operator_Clean': 'Operator'}
    )
    # Garis ambang batas standar Komdigi / 3GPP
    fig.add_vline(x=-95, line_width=1.5, line_dash="dash", line_color="#F59E0B", annotation_text="Batas Cukup (-95 dBm)", annotation_position="top right")
    fig.add_vline(x=-110, line_width=1.5, line_dash="dot", line_color="#EF4444", annotation_text="Batas Buruk (-110 dBm)", annotation_position="top left")
    fig.add_hline(y=-15, line_width=1.5, line_dash="dash", line_color="#F59E0B", annotation_text="Batas Cukup (-15 dB)", annotation_position="bottom right")
    fig.add_hline(y=-19.5, line_width=1.5, line_dash="dot", line_color="#EF4444", annotation_text="Batas Buruk (-19.5 dB)", annotation_position="bottom left")

    return apply_custom_layout(fig, "Matriks Kuat Sinyal (RSRP) vs Kualitas Sinyal (RSRQ)", height)

