"""
data_loader.py - Modul pembaca, pembersih, dan ekstraksi data pengukuran QoS Telekomunikasi.
"""

import os
import glob
import re
import pandas as pd
import numpy as np


def clean_numeric_val(val):
    """Membersihkan nilai numerik dari string seperti 'No Data', '%', '-', dll."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace('%', '').replace(',', '.')
    if s in ['No Data', '-', '', 'null', 'None', 'nan', 'ND', '#N/A']:
        return np.nan
    try:
        return float(s)
    except (ValueError, TypeError):
        return np.nan


def clean_text_val(val, default=''):
    """Membersihkan string nilai teks."""
    if pd.isna(val):
        return default
    s = str(val).strip()
    if s in ['-', 'No Data', 'null', 'None', 'nan']:
        return default
    return s


def find_qos_data_files(base_dir=None):
    """Mencari semua file summary QoS yang ada di direktori dan subdirektori."""
    if base_dir is None:
        base_dir = os.path.abspath(os.path.dirname(__file__))
    
    found_files = []
    
    # 1. Cek direktori aktif
    for ext in ("*.csv", "*.xlsx", "*.xlsm"):
        for f in glob.glob(os.path.join(base_dir, ext)):
            if not os.path.basename(f).startswith('~$'):
                found_files.append(os.path.abspath(f))

    # 2. Cek parent directory
    parent_dir = os.path.dirname(base_dir)
    if os.path.exists(parent_dir):
        for root, _, files in os.walk(parent_dir):
            for file in files:
                if file.lower().endswith(('.csv', '.xlsx', '.xlsm')) and ('summary' in file.lower() or 'qos' in file.lower()):
                    full_p = os.path.abspath(os.path.join(root, file))
                    if full_p not in found_files and not file.startswith('~$'):
                        found_files.append(full_p)
                        
    return found_files


def load_qos_summary(file_path_or_buffer):
    """
    Membaca dataset summary QoS (CSV atau Excel), meratakan header multi-level,
    dan memetakan kolom-kolom standar untuk visualisasi.
    """
    if isinstance(file_path_or_buffer, str):
        if file_path_or_buffer.lower().endswith('.csv'):
            raw_df = pd.read_csv(file_path_or_buffer, header=[0, 1])
        else:
            raw_df = pd.read_excel(file_path_or_buffer, header=[0, 1])
    else:
        # Streamlit UploadedFile
        name = getattr(file_path_or_buffer, 'name', '').lower()
        if name.endswith('.csv') or not name.endswith(('.xlsx', '.xlsm')):
            try:
                raw_df = pd.read_csv(file_path_or_buffer, header=[0, 1])
            except Exception:
                file_path_or_buffer.seek(0)
                raw_df = pd.read_excel(file_path_or_buffer, header=[0, 1])
        else:
            raw_df = pd.read_excel(file_path_or_buffer, header=[0, 1])

    # Bangun nama kolom gabungan
    flat_cols = []
    for col in raw_df.columns:
        c0 = '' if 'Unnamed:' in str(col[0]) else str(col[0]).strip()
        c1 = '' if 'Unnamed:' in str(col[1]) else str(col[1]).strip()
        if c0 and c1:
            name = f"{c0} - {c1}"
        else:
            name = c0 or c1 or f"Col_{len(flat_cols)}"
        flat_cols.append(name.strip())

    df = raw_df.copy()
    df.columns = flat_cols

    # Normalisasi nama Operator
    def norm_op(op):
        s = str(op).strip().upper()
        if 'TSEL' in s or 'TELKOMSEL' in s:
            return 'TELKOMSEL'
        elif 'IOH' in s or 'INDOSAT' in s or 'ISAT' in s:
            return 'IOH'
        elif 'XL' in s or 'SMART' in s or 'XLS' in s:
            return 'XLSMART'
        return s

    # Siapkan dictionary data untuk membuat DataFrame baru tanpa fragmentasi
    data_dict = {
        # Identitas & Metadata
        'No': df.iloc[:, 0].apply(clean_numeric_val),
        'Kode_Provinsi': df.iloc[:, 1].astype(str).str.strip(),
        'Provinsi': df.iloc[:, 2].astype(str).str.strip(),
        'Kode_Kabupaten': df.iloc[:, 3].astype(str).str.strip(),
        'Kabupaten': df.iloc[:, 4].astype(str).str.strip(),
        'Jenis_Tes': df.iloc[:, 5].astype(str).str.strip().str.upper(),
        'Collection': df.iloc[:, 6].astype(str).str.strip(),
        'Kecamatan': df.iloc[:, 7].apply(lambda x: clean_text_val(x, '-')),
        'Desa': df.iloc[:, 8].apply(lambda x: clean_text_val(x, '-')),
        'Lokasi_Pengukuran': df.iloc[:, 9].astype(str).str.strip(),
        'Event': df.iloc[:, 10].astype(str).str.strip(),
        'PMT_UPT': df.iloc[:, 11].astype(str).str.strip(),
        'Tanggal_Pengukuran': df.iloc[:, 12].astype(str).str.strip(),
        'Operator': df.iloc[:, 13].astype(str).str.strip().str.upper(),
        'Operator_Clean': df.iloc[:, 13].apply(norm_op),

        # FTP Downlink & Uplink
        'FTP_DL_Attempts': df.iloc[:, 14].apply(clean_numeric_val),
        'FTP_DL_Success_Attempts': df.iloc[:, 15].apply(clean_numeric_val),
        'FTP_DL_Success_Rate': df.iloc[:, 16].apply(clean_numeric_val),
        'FTP_DL_Avg_Mbps': df.iloc[:, 17].apply(clean_numeric_val),
        'FTP_DL_Median_Mbps': df.iloc[:, 18].apply(clean_numeric_val),
        'FTP_DL_Max_Mbps': df.iloc[:, 19].apply(clean_numeric_val),
        'FTP_DL_Min_Mbps': df.iloc[:, 20].apply(clean_numeric_val),
        'FTP_UL_Attempts': df.iloc[:, 23].apply(clean_numeric_val),
        'FTP_UL_Success_Attempts': df.iloc[:, 24].apply(clean_numeric_val),
        'FTP_UL_Success_Rate': df.iloc[:, 25].apply(clean_numeric_val),
        'FTP_UL_Avg_Mbps': df.iloc[:, 26].apply(clean_numeric_val),
        'FTP_UL_Median_Mbps': df.iloc[:, 27].apply(clean_numeric_val),
        'FTP_UL_Max_Mbps': df.iloc[:, 28].apply(clean_numeric_val),
        'FTP_UL_Min_Mbps': df.iloc[:, 29].apply(clean_numeric_val),

        # Capacity Test
        'Capacity_DL_Success_Rate': df.iloc[:, 34].apply(clean_numeric_val),
        'Capacity_DL_Avg_Mbps': df.iloc[:, 35].apply(clean_numeric_val),
        'Capacity_DL_Median_Mbps': df.iloc[:, 36].apply(clean_numeric_val),
        'Capacity_UL_Success_Rate': df.iloc[:, 43].apply(clean_numeric_val),
        'Capacity_UL_Avg_Mbps': df.iloc[:, 44].apply(clean_numeric_val),
        'Capacity_UL_Median_Mbps': df.iloc[:, 45].apply(clean_numeric_val),

        # SpeedTest DL & UL
        'SpeedTest_Attempts': df.iloc[:, 50].apply(clean_numeric_val),
        'SpeedTest_Success_Attempts': df.iloc[:, 51].apply(clean_numeric_val),
        'SpeedTest_DL_Success_Rate': df.iloc[:, 52].apply(clean_numeric_val),
        'SpeedTest_DL_Avg_Mbps': df.iloc[:, 53].apply(clean_numeric_val),
        'SpeedTest_DL_Median_Mbps': df.iloc[:, 54].apply(clean_numeric_val),
        'SpeedTest_DL_Max_Mbps': df.iloc[:, 55].apply(clean_numeric_val),
        'SpeedTest_DL_Min_Mbps': df.iloc[:, 56].apply(clean_numeric_val),
        'SpeedTest_DL_RTT_ms': df.iloc[:, 57].apply(clean_numeric_val),
        'SpeedTest_UL_Success_Rate': df.iloc[:, 58].apply(clean_numeric_val),
        'SpeedTest_UL_Avg_Mbps': df.iloc[:, 59].apply(clean_numeric_val),
        'SpeedTest_UL_Median_Mbps': df.iloc[:, 60].apply(clean_numeric_val),
        'SpeedTest_UL_Max_Mbps': df.iloc[:, 61].apply(clean_numeric_val),
        'SpeedTest_UL_Min_Mbps': df.iloc[:, 62].apply(clean_numeric_val),
        'SpeedTest_UL_RTT_ms': df.iloc[:, 63].apply(clean_numeric_val),

        # HTTP Transfer
        'HTTP_DL_Success_Rate': df.iloc[:, 70].apply(clean_numeric_val),
        'HTTP_DL_Avg_Mbps': df.iloc[:, 71].apply(clean_numeric_val),
        'HTTP_DL_Median_Mbps': df.iloc[:, 72].apply(clean_numeric_val),
        'HTTP_UL_Success_Rate': df.iloc[:, 77].apply(clean_numeric_val),
        'HTTP_UL_Avg_Mbps': df.iloc[:, 78].apply(clean_numeric_val),
        'HTTP_UL_Median_Mbps': df.iloc[:, 79].apply(clean_numeric_val),

        # Browsing
        'Browsing_Attempts': df.iloc[:, 82].apply(clean_numeric_val),
        'Browsing_Success_Attempts': df.iloc[:, 83].apply(clean_numeric_val),
        'Browsing_Success_Rate': df.iloc[:, 84].apply(clean_numeric_val),
        'Browsing_Avg_Speed_Mbps': df.iloc[:, 85].apply(clean_numeric_val),
        'Browsing_Max_Speed_Mbps': df.iloc[:, 86].apply(clean_numeric_val),
        'Browsing_Min_Speed_Mbps': df.iloc[:, 87].apply(clean_numeric_val),
        'Browsing_Duration_Sec': df.iloc[:, 88].apply(clean_numeric_val),
        'Browsing_RTT_ms': df.iloc[:, 89].apply(clean_numeric_val),

        # Ping Test
        'Ping_Attempts': df.iloc[:, 91].apply(clean_numeric_val),
        'Ping_Success_Attempts': df.iloc[:, 92].apply(clean_numeric_val),
        'Ping_Success_Rate': df.iloc[:, 93].apply(clean_numeric_val),
        'Ping_Packet_Loss_Rate': df.iloc[:, 94].apply(clean_numeric_val),
        'Ping_Avg_RTT_ms': df.iloc[:, 95].apply(clean_numeric_val),
        'Ping_RTT_LE_250ms_Rate': df.iloc[:, 96].apply(clean_numeric_val),

        # YouTube Video
        'YouTube_Attempts': df.iloc[:, 97].apply(clean_numeric_val),
        'YouTube_Success_Attempts': df.iloc[:, 98].apply(clean_numeric_val),
        'YouTube_Success_Rate': df.iloc[:, 99].apply(clean_numeric_val),
        'YouTube_Avg_TTFP_s': df.iloc[:, 100].apply(clean_numeric_val),
        'YouTube_TTFP_GT_10s_Rate': df.iloc[:, 101].apply(clean_numeric_val),
        'YouTube_Visual_Quality': df.iloc[:, 102].apply(clean_numeric_val),
        'YouTube_Freezing_Ratio': df.iloc[:, 103].apply(clean_numeric_val),
        'YouTube_Jerkiness': df.iloc[:, 104].apply(clean_numeric_val),
        'YouTube_144p_Rate': df.iloc[:, 105].apply(clean_numeric_val),
        'YouTube_240p_Rate': df.iloc[:, 106].apply(clean_numeric_val),
        'YouTube_360p_Rate': df.iloc[:, 107].apply(clean_numeric_val),
        'YouTube_480p_Rate': df.iloc[:, 108].apply(clean_numeric_val),
        'YouTube_720p_Rate': df.iloc[:, 109].apply(clean_numeric_val),
        'YouTube_1080p_HD_Rate': df.iloc[:, 110].apply(clean_numeric_val),
        'YouTube_1440p_2K_Rate': df.iloc[:, 111].apply(clean_numeric_val),

        # Instagram Post
        'IG_Pic_Attempts': df.iloc[:, 112].apply(clean_numeric_val),
        'IG_Pic_Success_Rate': df.iloc[:, 114].apply(clean_numeric_val),
        'IG_Pic_Avg_Speed_Mbps': df.iloc[:, 115].apply(clean_numeric_val),
        'IG_Pic_Avg_Duration_s': df.iloc[:, 116].apply(clean_numeric_val),
        'IG_Video_Attempts': df.iloc[:, 118].apply(clean_numeric_val),
        'IG_Video_Success_Rate': df.iloc[:, 120].apply(clean_numeric_val),
        'IG_Video_Avg_Speed_Mbps': df.iloc[:, 121].apply(clean_numeric_val),
        'IG_Video_Avg_Duration_s': df.iloc[:, 122].apply(clean_numeric_val),

        # WhatsApp
        'WA_Call_Attempts': df.iloc[:, 124].apply(clean_numeric_val),
        'WA_Call_Blocked': df.iloc[:, 125].apply(clean_numeric_val),
        'WA_Call_Dropped': df.iloc[:, 126].apply(clean_numeric_val),
        'WA_Call_Success_Rate': df.iloc[:, 127].apply(clean_numeric_val),
        'WA_Call_Blocked_Rate': df.iloc[:, 128].apply(clean_numeric_val),
        'WA_Call_Dropped_Rate': df.iloc[:, 129].apply(clean_numeric_val),
        'WA_Call_Avg_MOS': df.iloc[:, 130].apply(clean_numeric_val),
        'WA_Call_MOS_GE_16_Rate': df.iloc[:, 131].apply(clean_numeric_val),
        'WA_Call_Avg_CST_s': df.iloc[:, 133].apply(clean_numeric_val),
        'WA_Msg_Attempts': df.iloc[:, 135].apply(clean_numeric_val),
        'WA_Msg_Success_Rate': df.iloc[:, 137].apply(clean_numeric_val),
        'WA_Msg_Avg_Duration_s': df.iloc[:, 138].apply(clean_numeric_val),

        # SMS
        'SMS_Onnet_Attempts': df.iloc[:, 139].apply(clean_numeric_val),
        'SMS_Onnet_Success_LE_1min_Rate': df.iloc[:, 141].apply(clean_numeric_val),
        'SMS_Offnet_Attempts': df.iloc[:, 142].apply(clean_numeric_val),
        'SMS_Offnet_Success_LE_1min_Rate': df.iloc[:, 144].apply(clean_numeric_val),

        # Voice Call Onnet
        'Voice_Onnet_Attempts': df.iloc[:, 145].apply(clean_numeric_val),
        'Voice_Onnet_Success_Rate': df.iloc[:, 148].apply(clean_numeric_val),
        'Voice_Onnet_Blocked_Rate': df.iloc[:, 149].apply(clean_numeric_val),
        'Voice_Onnet_Dropped_Rate': df.iloc[:, 150].apply(clean_numeric_val),
        'Voice_Onnet_Avg_MOS': df.iloc[:, 153].apply(clean_numeric_val),
        'Voice_Onnet_Avg_CST_s': df.iloc[:, 158].apply(clean_numeric_val),

        # Voice Call Offnet
        'Voice_Offnet_Attempts': df.iloc[:, 160].apply(clean_numeric_val),
        'Voice_Offnet_Success_Rate': df.iloc[:, 163].apply(clean_numeric_val),
        'Voice_Offnet_Blocked_Rate': df.iloc[:, 164].apply(clean_numeric_val),
        'Voice_Offnet_Dropped_Rate': df.iloc[:, 165].apply(clean_numeric_val),
        'Voice_Offnet_Avg_MOS': df.iloc[:, 168].apply(clean_numeric_val),
        'Voice_Offnet_Avg_CST_s': df.iloc[:, 173].apply(clean_numeric_val),

        # Voice Call Average
        'Voice_Attempts': df.iloc[:, 175].apply(clean_numeric_val),
        'Voice_Success_Rate': df.iloc[:, 178].apply(clean_numeric_val),
        'Voice_Blocked_Rate': df.iloc[:, 179].apply(clean_numeric_val),
        'Voice_Dropped_Rate': df.iloc[:, 180].apply(clean_numeric_val),
        'Voice_Avg_MOS': df.iloc[:, 183].apply(clean_numeric_val),
        'Voice_Avg_CST_s': df.iloc[:, 188].apply(clean_numeric_val),

        # RF Signal 5G
        'Signal_5G_SS_RSRP': df.iloc[:, 190].apply(clean_numeric_val),
        'Signal_5G_SS_RSRP_Cat': df.iloc[:, 191].apply(lambda x: clean_text_val(x, 'No Data')),
        'Signal_5G_SS_RSRQ': df.iloc[:, 192].apply(clean_numeric_val),
        'Signal_5G_SS_SINR': df.iloc[:, 194].apply(clean_numeric_val),

        # RF Signal 4G
        'Signal_4G_RSRP': df.iloc[:, 196].apply(clean_numeric_val),
        'Signal_4G_RSRP_Cat': df.iloc[:, 197].apply(lambda x: clean_text_val(x, 'No Data')),
        'Signal_4G_RSRQ': df.iloc[:, 198].apply(clean_numeric_val),
        'Signal_4G_RSRQ_Cat': df.iloc[:, 199].apply(lambda x: clean_text_val(x, 'No Data')),
        'Signal_4G_SINR': df.iloc[:, 200].apply(clean_numeric_val),
        'Signal_4G_SINR_Cat': df.iloc[:, 201].apply(lambda x: clean_text_val(x, 'No Data')),

        # RF Signal 2G
        'Signal_2G_RxLev': df.iloc[:, 202].apply(clean_numeric_val),
        'Signal_2G_RxLev_Cat': df.iloc[:, 203].apply(lambda x: clean_text_val(x, 'No Data')),
        'Signal_2G_RxQual': df.iloc[:, 204].apply(clean_numeric_val),
        'Signal_2G_RxQual_Cat': df.iloc[:, 205].apply(lambda x: clean_text_val(x, 'No Data')),

        # Bad Signal Sample Rates
        'Signal_5G_Bad_RSRP_Rate': df.iloc[:, 208].apply(clean_numeric_val),
        'Signal_5G_Bad_RSRQ_Rate': df.iloc[:, 211].apply(clean_numeric_val),
        'Signal_5G_Bad_SINR_Rate': df.iloc[:, 214].apply(clean_numeric_val),
        'Signal_4G_Total_RSRP_Sample': df.iloc[:, 215].apply(clean_numeric_val),
        'Signal_4G_Bad_RSRP_Sample': df.iloc[:, 216].apply(clean_numeric_val),
        'Signal_4G_Bad_RSRP_Rate': df.iloc[:, 217].apply(clean_numeric_val),
        'Signal_4G_Total_RSRQ_Sample': df.iloc[:, 218].apply(clean_numeric_val),
        'Signal_4G_Bad_RSRQ_Sample': df.iloc[:, 219].apply(clean_numeric_val),
        'Signal_4G_Bad_RSRQ_Rate': df.iloc[:, 220].apply(clean_numeric_val),
        'Signal_4G_Total_SINR_Sample': df.iloc[:, 221].apply(clean_numeric_val),
        'Signal_4G_Bad_SINR_Sample': df.iloc[:, 222].apply(clean_numeric_val),
        'Signal_4G_Bad_SINR_Rate': df.iloc[:, 223].apply(clean_numeric_val),
        'Signal_2G_Bad_RxLev_Rate': df.iloc[:, 226].apply(clean_numeric_val),
        'Signal_2G_Bad_RxQual_Rate': df.iloc[:, 229].apply(clean_numeric_val),

        # Coordinates & Distance
        'Lat': df.iloc[:, 264].apply(clean_numeric_val),
        'Long': df.iloc[:, 265].apply(clean_numeric_val),
        'Distance_Km': df.iloc[:, 266].apply(clean_numeric_val),
    }

    clean_df = pd.DataFrame(data_dict)

    # Kolom agregasi utama
    clean_df['Overall_DL_Speed_Mbps'] = clean_df['SpeedTest_DL_Avg_Mbps'].fillna(clean_df['FTP_DL_Avg_Mbps'])
    clean_df['Overall_UL_Speed_Mbps'] = clean_df['SpeedTest_UL_Avg_Mbps'].fillna(clean_df['FTP_UL_Avg_Mbps'])

    return clean_df, df


def filter_dataset(df, kabupaten_list=None, operator_list=None, jenis_tes_list=None, event_list=None):
    """Menerapkan filter terhadap dataset clean_df."""
    filtered = df.copy()

    if kabupaten_list and 'Semua' not in kabupaten_list:
        filtered = filtered[filtered['Kabupaten'].isin(kabupaten_list)]

    if operator_list and 'Semua' not in operator_list:
        filtered = filtered[filtered['Operator_Clean'].isin(operator_list) | filtered['Operator'].isin(operator_list)]

    if jenis_tes_list and 'Semua' not in jenis_tes_list:
        filtered = filtered[filtered['Jenis_Tes'].isin(jenis_tes_list)]

    if event_list and 'Semua' not in event_list:
        filtered = filtered[filtered['Event'].isin(event_list)]

    return filtered


def get_operator_color(op_name):
    """Mengembalikan kode warna standar per operator telekomunikasi."""
    op = str(op_name).upper()
    if 'TSEL' in op or 'TELKOMSEL' in op:
        return '#E60000'  # Merah Telkomsel
    elif 'IOH' in op or 'INDOSAT' in op or 'ISAT' in op:
        return '#F5A623'  # Kuning Emas Indosat Ooredoo Hutchison
    elif 'XL' in op or 'SMART' in op or 'XLS' in op:
        return '#0070F3'  # Biru XL Axiata / Smartfren
    return '#6C757D'     # Abu-abu default


def get_operator_palette():
    """Mengembalikan dictionary palet warna operator."""
    return {
        'TELKOMSEL': '#E60000',
        'TSEL': '#E60000',
        'IOH': '#F5A623',
        'INDOSAT': '#F5A623',
        'XLSMART': '#0070F3',
        'XLS': '#0070F3',
        'SMARTFREN': '#E91E63'
    }
