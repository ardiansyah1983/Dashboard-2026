"""
utils_map.py - Modul pembuat peta spasial interaktif berbasis Folium untuk visualisasi QoS.
"""

import folium
from folium.plugins import MarkerCluster, Fullscreen, MeasureControl
import pandas as pd
import numpy as np


def get_marker_color_by_operator(operator):
    """Mendapatkan warna marker berdasarkan operator."""
    op = str(operator).upper()
    if 'TSEL' in op or 'TELKOMSEL' in op:
        return 'red'
    elif 'IOH' in op or 'INDOSAT' in op:
        return 'orange'
    elif 'XL' in op or 'SMART' in op or 'XLS' in op:
        return 'blue'
    return 'gray'


def get_marker_color_by_speed(speed):
    """Mendapatkan warna marker berdasarkan kecepatan unduh (Mbps)."""
    if pd.isna(speed):
        return 'gray'
    if speed >= 100:
        return 'green'
    elif speed >= 50:
        return 'blue'
    elif speed >= 20:
        return 'orange'
    else:
        return 'red'


def get_marker_color_by_rsrp(rsrp):
    """Mendapatkan warna marker berdasarkan kuat sinyal 4G RSRP (dBm)."""
    if pd.isna(rsrp):
        return 'gray'
    if rsrp >= -85:
        return 'green'
    elif rsrp >= -95:
        return 'blue'
    elif rsrp >= -105:
        return 'orange'
    else:
        return 'red'


def get_marker_color_by_rsrq(rsrq):
    """Mendapatkan warna marker berdasarkan kualitas sinyal 4G RSRQ (dB)."""
    if pd.isna(rsrq):
        return 'gray'
    if rsrq >= -10:
        return 'green'      # Baik Sekali
    elif rsrq >= -15:
        return 'blue'       # Baik
    elif rsrq >= -19.5:
        return 'orange'     # Cukup
    else:
        return 'red'        # Kurang / Buruk


def create_qos_map(df, color_by='operator'):
    """
    Membuat peta interaktif Folium dari data pengukuran QoS.
    color_by: 'operator', 'speed', atau 'rsrp'
    """
    valid_coords = df.dropna(subset=['Lat', 'Long']).copy()
    
    # Filter out invalid lat/long values
    valid_coords = valid_coords[(valid_coords['Lat'] >= -12) & (valid_coords['Lat'] <= 6) & 
                                (valid_coords['Long'] >= 95) & (valid_coords['Long'] <= 142)]

    if valid_coords.empty:
        # Default center Sulawesi Tenggara (Kendari)
        m = folium.Map(location=[-3.9734, 122.5114], zoom_start=8, tiles='CartoDB positron')
        return m

    center_lat = valid_coords['Lat'].mean()
    center_long = valid_coords['Long'].mean()

    m = folium.Map(
        location=[center_lat, center_long],
        zoom_start=8,
        tiles='CartoDB positron',
        control_scale=True
    )

    # Tambahkan layer pilihan peta
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Dark Matter').add_to(m)

    # Plugin tambahan
    Fullscreen(position='topright').add_to(m)
    MeasureControl(position='bottomleft').add_to(m)

    # Grup marker per operator agar bisa di-toggle
    operators = valid_coords['Operator_Clean'].unique().tolist()
    op_groups = {}
    for op in operators:
        op_groups[op] = folium.FeatureGroup(name=f"Operator: {op}").add_to(m)

    for _, row in valid_coords.iterrows():
        lat = row['Lat']
        lon = row['Long']
        op = row['Operator_Clean']
        kab = row['Kabupaten']
        lok = row['Lokasi_Pengukuran']
        jenis = row['Jenis_Tes']
        tgl = row['Tanggal_Pengukuran']

        dl_spd = row['SpeedTest_DL_Avg_Mbps']
        ul_spd = row['SpeedTest_UL_Avg_Mbps']
        lat_rtt = row['Ping_Avg_RTT_ms']
        wa_mos = row['WA_Call_Avg_MOS']
        rsrp_val = row['Signal_4G_RSRP']
        rsrp_cat = row['Signal_4G_RSRP_Cat']
        rsrq_val = row['Signal_4G_RSRQ']
        rsrq_cat = row['Signal_4G_RSRQ_Cat']
        sinr_val = row['Signal_4G_SINR']
        dist_km = row['Distance_Km']

        # Tentukan warna
        if color_by == 'speed':
            marker_col = get_marker_color_by_speed(dl_spd)
        elif color_by == 'rsrp':
            marker_col = get_marker_color_by_rsrp(rsrp_val)
        elif color_by == 'rsrq':
            marker_col = get_marker_color_by_rsrq(rsrq_val)
        else:
            marker_col = get_marker_color_by_operator(op)

        # Icon tipe tes
        icon_name = 'car' if jenis == 'DT' else 'map-marker'

        # Konten HTML Popup yang rapi
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 240px; font-size: 12px; color: #1E293B;">
            <div style="background-color: #1E293B; color: white; padding: 6px 10px; border-radius: 4px 4px 0 0; font-weight: bold; font-size: 13px;">
                {lok}
            </div>
            <div style="padding: 8px; border: 1px solid #E2E8F0; border-top: none; border-radius: 0 0 4px 4px; background: #FFFFFF;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>Operator:</b></td>
                        <td style="padding: 3px 0; text-align: right;"><span style="background: {'#FFE4E6' if op=='TELKOMSEL' else ('#FEF3C7' if op=='IOH' else '#DBEAFE')}; padding: 2px 6px; border-radius: 3px; font-weight: bold;">{op}</span></td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>Wilayah:</b></td>
                        <td style="padding: 3px 0; text-align: right;">{kab}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>Tipe Tes:</b></td>
                        <td style="padding: 3px 0; text-align: right;"><b>{jenis}</b> ({'Drive Test' if jenis=='DT' else 'Stationary'})</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>Tanggal:</b></td>
                        <td style="padding: 3px 0; text-align: right;">{tgl}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>SpeedTest DL:</b></td>
                        <td style="padding: 3px 0; text-align: right; color: #059669; font-weight: bold;">{f'{dl_spd:.2f} Mbps' if pd.notna(dl_spd) else '-'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>SpeedTest UL:</b></td>
                        <td style="padding: 3px 0; text-align: right; font-weight: bold;">{f'{ul_spd:.2f} Mbps' if pd.notna(ul_spd) else '-'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>Ping Latency:</b></td>
                        <td style="padding: 3px 0; text-align: right;">{f'{lat_rtt:.1f} ms' if pd.notna(lat_rtt) else '-'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>4G RSRP (Kuat):</b></td>
                        <td style="padding: 3px 0; text-align: right;">{f'{rsrp_val:.1f} dBm ({rsrp_cat})' if pd.notna(rsrp_val) else '-'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>4G RSRQ (Kualitas):</b></td>
                        <td style="padding: 3px 0; text-align: right;">{f'{rsrq_val:.1f} dB ({rsrq_cat})' if pd.notna(rsrq_val) else '-'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F1F5F9;">
                        <td style="padding: 3px 0; color: #64748B;"><b>4G SINR:</b></td>
                        <td style="padding: 3px 0; text-align: right;">{f'{sinr_val:.1f} dB' if pd.notna(sinr_val) else '-'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px 0; color: #64748B;"><b>WhatsApp MOS:</b></td>
                        <td style="padding: 3px 0; text-align: right;">{f'{wa_mos:.2f}' if pd.notna(wa_mos) else '-'}</td>
                    </tr>
                </table>
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"<b>{lok}</b> ({op}) - DL: {dl_spd:.1f} Mbps",
            icon=folium.Icon(color=marker_col, icon=icon_name, prefix='fa')
        ).add_to(op_groups[op])

    folium.LayerControl(collapsed=False).add_to(m)
    return m
