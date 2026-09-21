# 📶 Dashboard Visualisasi Kualitas Layanan Telekomunikasi (QoS)

Aplikasi dashboard interaktif modern berbasis **Streamlit**, **Plotly**, dan **Folium** untuk memonitor, memvisualisasikan, menganalisis, dan membandingkan hasil pengukuran kualitas jaringan & layanan telekomunikasi (Drive Test [DT] dan Stationary Test [ST]) dari Balai Monitor / UPT Komdigi.

---

## 🌟 Fitur Utama

1. **Multi-Source Data Ingestion**:
   - Otomatis memuat dan mendeteksi file ringkasan QoS di folder kerja (`Summary Hasil Pengolahan QOS Reguler 2026.csv`, file `.xlsx`, `.xlsm`).
   - Fitur unggah berkas (Upload CSV / Excel) mandiri langsung dari Web UI.
   - Parsing otomatis multi-level header dan normalisasi lebih dari 260 kolom metrik.

2. **Filter Interaktif Terpadu (Sidebar)**:
   - Filter Wilayah (Kabupaten / Kota, Kecamatan, Lokasi).
   - Filter Operator Seluler (TELKOMSEL, IOH, XLSMART).
   - Filter Tipe Pengujian (Drive Test `DT`, Stationary Test `ST`).
   - Filter Event & Tanggal.

3. **Modul & Tab Visualisasi Lengkap**:
   - 📊 **Ringkasan & Scorecard**: Kartu metrik KPI utama, kepatuhan ambang batas Komdigi (Throughput, Latensi, MOS, RSRP), leaderboard operator, Top/Bottom lokasi pengukuran, dan Radar Chart komparasi multi-dimensi.
   - 🚀 **Throughput & Kecepatan**: Grafik perbandingan SpeedTest DL/UL, FTP DL/UL, Capacity Test, HTTP Transfer, distribusi boxplot, dan komparasi per wilayah.
   - 🌐 **Latensi & Aplikasi OTT**: Analisis latensi Ping RTT, Packet Loss, Web Browsing, YouTube Streaming (TTFP, Freezing, Visual Quality, proporsi resolusi 144p - 1080p HD), Instagram Upload (Foto vs Video), dan WhatsApp Call & Message.
   - 📞 **Kualitas Suara & SMS**: Success Call Rate (CSSR), Blocked Rate (CBR), Dropped Rate (CDR), Mean Opinion Score (MOS), Call Setup Time (CST) untuk Onnet vs Offnet, serta keberhasilan pengiriman SMS < 1 menit.
   - 📶 **Kualitas & Cakupan Sinyal (RF 4G/5G/2G)**: Kuat sinyal 4G RSRP, kualitas 4G SINR/RSRQ, distribusi kategori sinyal (Baik Sekali, Baik, Cukup, Kurang), korelasi RSRP vs SINR, dan analisis persentase Bad Samples.
   - 🗺️ **Peta Spasial Interaktif**: Peta OpenStreetMap / CartoDB memetakan seluruh titik pengukuran dengan filter pewarnaan berdasarkan Operator, Kecepatan DL, atau Kuat Sinyal RSRP, lengkap dengan tooltip & popup informatif.
   - ⚖️ **Benchmarking Operator**: Perbandingan langsung head-to-head operator per wilayah kabupaten/kota.
   - 📋 **Data Explorer & Export**: Eksplorasi tabel data mentah dengan fitur pencarian teks dan tombol unduh data terfilter ke format **Excel (.xlsx)** dan **CSV**.

---

## 🚀 Cara Menjalankan Aplikasi

### Cara 1: Menggunakan Script 1-Klik (Windows)
Cukup klik ganda (double click) pada file:
```
run_dashboard.bat
```

### Cara 2: Melalui Terminal / Command Prompt
1. Buka terminal di folder project:
   ```bash
   cd "d:\HASIL PENGOLAHAN QOS\Project Dashboard QOS"
   ```
2. Jalankan perintah Streamlit:
   ```bash
   streamlit run app.py
   ```
3. Dashboard akan terbuka otomatis di browser pada alamat:
   `http://localhost:8501`

---

## 📦 Kebutuhan Dependensi
Semua dependensi tertera di `requirements.txt`:
- `streamlit`
- `pandas`
- `plotly`
- `folium`
- `streamlit-folium`
- `openpyxl`
- `geopandas`
