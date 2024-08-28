import streamlit as st
import pandas as pd
import geopandas as gpd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import plotly.express as px
import matplotlib.colors as mcolors
import plotly.graph_objects as go


# CSS untuk memastikan semua tombol memiliki lebar yang sama
st.markdown("""
    <style>
    .stButton button {
        width: 100%;
        min-width: 200px;
        max-width: 200px;
    }
    </style>
    """, unsafe_allow_html=True)
# Fungsi untuk mengimpor data
def upload_data():
    uploaded_files = st.file_uploader("Pilih file Excel", type=["xlsx"], accept_multiple_files=True, key="file_uploader")
    return uploaded_files

# Fungsi untuk memproses data untuk visualisasi 1
def process_visualization_one(files):
    dfs = [pd.read_excel(file) for file in files]
    df = pd.merge(dfs[0], dfs[1], on='kode_kabupaten_kota')
    kmeans = KMeans(n_clusters=3, random_state=0)
    clusters = kmeans.fit_predict(df[['jumlah_stasiun', 'jumlah_terminal']])
    df['cluster'] = clusters + 1
    df['ID_KAB'] = df['kode_kabupaten_kota']
    df_clustered = df[['ID_KAB', 'cluster']]
    return df_clustered

# Fungsi untuk memproses data untuk visualisasi 2
def process_visualization_two(files):
    # Membaca file Excel
    dfs = [pd.read_excel(file) for file in files]
    
    # Menggabungkan data berdasarkan kolom 'kode_kabupaten_kota'
    df = dfs[0]
    for additional_df in dfs[1:]:
        df = pd.merge(df, additional_df, on='kode_kabupaten_kota', how='outer', suffixes=('', '_drop'))
        
        # Hapus kolom yang duplikat setelah penggabungan
        df = df.loc[:, ~df.columns.str.endswith('_drop')]

    # Memastikan kolom yang diperlukan ada di dalam dataframe
    required_columns = ['jumlah_moda_angkutan_barang', 'jumlah_moda_angkutan_asdp', 'jumlah_kapal', 'jumlah_angkutan_akdp']
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"Kolom {col} tidak ditemukan di dalam dataframe.")
    
    # Menghitung jumlah angkutan barang dan penumpang
    df['jumlah_angkutan_barang'] = (df['jumlah_moda_angkutan_barang'] + 
                                    df['jumlah_moda_angkutan_asdp'] + 
                                    df['jumlah_kapal'])
    df['jumlah_angkutan_penumpang'] = df['jumlah_angkutan_akdp']
    
    # Menambahkan kolom 'ID_KAB'
    df['ID_KAB'] = df['kode_kabupaten_kota']
    
    # Melakukan clustering (contoh dengan KMeans)
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=3)
    df['cluster'] = kmeans.fit_predict(df[['jumlah_angkutan_barang', 'jumlah_angkutan_penumpang']])
    
    # Menyiapkan dataframe untuk output
    df_clustered = df[['ID_KAB', 'cluster']]
    
    return df_clustered


#
def process_and_store_pendanaan_pie_chart(file):
    df = pd.read_excel(file)
    
    # Pastikan kolom yang diperlukan ada
    kolom_diperlukan = {'program', 'apbd'}
    if kolom_diperlukan.issubset(df.columns):
        # Agregasikan data berdasarkan program
        df_grouped = df.groupby('program').agg({'apbd': 'sum'}).reset_index()

        # Menemukan program dengan APBD terbesar
        max_apbd_program_idx = df_grouped['apbd'].idxmax()
        max_apbd_program = df_grouped.loc[max_apbd_program_idx, 'program']
        max_apbd_value = df_grouped.loc[max_apbd_program_idx, 'apbd']
        explode = [0.1 if i == max_apbd_program_idx else 0 for i in range(len(df_grouped))]  # Pisahkan program dengan APBD terbesar

        # Membuat pie chart
        fig, ax = plt.subplots(figsize=(12, 8))  # Perbesar ukuran pie chart
        wedges, texts, autotexts = ax.pie(df_grouped['apbd'], explode=explode, labels=None, autopct='%1.1f%%',
                                          shadow=True, startangle=140, colors=plt.cm.tab20.colors)

        # Menambahkan legenda
        ax.legend(wedges, df_grouped['program'],
                  title="Program",
                  loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1))

        # Atur label menjadi hanya persentase
        for text in texts:
            text.set_text("")

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(14)
            autotext.set_fontweight('bold')

        # Menyimpan pie chart di session state
        st.session_state['pendanaan_pie_chart'] = fig

        # Menyimpan deskripsi di bawah pie chart
        st.session_state['pendanaan_description'] = f"""
            <div style="background-color: #f0f8f8; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="font-size: 18px;">Pendanaan terbesar pada bidang digunakan untuk</p>
                <p style="font-size: 24px; font-weight: bold; color: blue;">{max_apbd_program}</p>
                <p>dengan jumlah sebesar <b>{max_apbd_value:,.2f}</b> Rupiah.</p>
            </div>
        """
        
    else:
        st.error(f"Data yang diunggah harus memiliki kolom: {', '.join(kolom_diperlukan)}")

# Fungsi untuk memproses data untuk visualisasi 4
def process_visualization_four(files):
    df1 = pd.read_excel(files[0])
    df2 = pd.read_excel(files[1])
    df = pd.merge(df1, df2, on='kode_kabupaten_kota')
    df_selected = df[['kode_kabupaten_kota', 'persentase_penduduk', 'jumlah_pengeluaran_per_kapita']]
    kmeans = KMeans(n_clusters=3, random_state=0)
    clusters = kmeans.fit_predict(df_selected[['persentase_penduduk', 'jumlah_pengeluaran_per_kapita']])
    df_selected['cluster'] = clusters + 1
    df_selected['ID_KAB'] = df_selected['kode_kabupaten_kota']
    df_clustered = df_selected[['ID_KAB', 'cluster']]
    return df_clustered

# Fungsi untuk menampilkan choropleth map
def visualize_choropleth_map(df_clustered, title, target_cluster, total_kabupaten=27):
    gdf = gpd.read_file("Jabar_By_Kab.geojson")
    gdf = gdf.merge(df_clustered, left_on="ID_KAB", right_on="ID_KAB")

    # Buat custom colormap untuk cluster
    cmap = mcolors.ListedColormap(['#66b3ff', '#3399ff', '#0073e6'])
    norm = mcolors.BoundaryNorm([ 0, 1, 2, 3], cmap.N)
    
    # Hitung jumlah kabupaten dalam cluster target
    count_target_cluster = gdf[gdf['cluster'] == target_cluster ].shape[0]

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Plot peta dengan warna yang disesuaikan
    gdf.plot(column='cluster', cmap=cmap, linewidth=0.8, ax=ax, edgecolor='0.8', legend=True, norm=norm)
    
    # Tampilkan nama kabupaten/kota di peta
    for x, y, label in zip(gdf.geometry.centroid.x, gdf.geometry.centroid.y, gdf['KABKOT']):
        ax.text(x, y, label, fontsize=8, ha='center', va='center', color='black', clip_on=True)

    ax.set_axis_off()
    plt.title(title, fontsize=15)
    st.pyplot(fig)

    # Menentukan kalimat berdasarkan jenis visualisasi
    if "transportasi" in title.lower():
        description = f"dengan kategori jumlah transport sangat kurang"
    elif "infrastruktur" in title.lower():
        description = f"dengan kategori jumlah infrastruktur sangat kurang"
    elif "daerah tertinggal" in title.lower():
        description = f"dengan keadaan tertinggal"
    else:
        description = ""

    # Tampilkan informasi jumlah kabupaten
    st.markdown(f"""
        <div style="background-color: #f0f8f8; padding: 15px; border-radius: 10px; text-align: center;">
            <p style="font-size: 18px;">Terdapat</p>
            <p style="font-size: 36px; font-weight: bold; color: blue;">{count_target_cluster} Kabupaten</p>
            <p>dari {total_kabupaten} kabupaten {description}.</p>
        </div>
    """, unsafe_allow_html=True)

# Fungsi untuk memproses dan menampilkan Indeks transportasi
def process_and_display_transportation_index(file):
    df = pd.read_excel(file)
    
    submenu = st.selectbox("Pilih Indeks yang Ingin Ditampilkan", ["Per Kabupaten/Kota", "Keseluruhan"])
    
    if submenu == "Per Kabupaten/Kota":
        kolom_diperlukan = {'nama_kabupaten_kota', 'jumlah_transportasi_2021', 'jumlah_transportasi_2022'}
        if kolom_diperlukan.issubset(df.columns):
            # Hitung transportasi per area (tidak perlu normalisasi luas jika tidak ada data luas)
            df['transportasi_per_area_2021'] = df['jumlah_transportasi_2021']
            df['transportasi_per_area_2022'] = df['jumlah_transportasi_2022']

            # Hitung persentase pertumbuhan per kabupaten/kota
            df['persentase_pertumbuhan'] = ((df['transportasi_per_area_2022'] - df['transportasi_per_area_2021']) / df['transportasi_per_area_2021']) * 100
            df['indeks_pertumbuhan'] = ((df['transportasi_per_area_2022'] - df['transportasi_per_area_2021']) / df['transportasi_per_area_2021'])

            # Format hasil perhitungan
            df['indeks_pertumbuhan_formatted'] = df['indeks_pertumbuhan'].map(lambda x: f"{x:.4f}")
            df['persentase_pertumbuhan_formatted'] = df['persentase_pertumbuhan'].map(lambda x: f"{x:.2f}%")

            # Tampilkan hasil perhitungan
            st.write("Indeks Transportasi per Kabupaten/Kota pada Tahun 2022:")
            st.dataframe(df[['nama_kabupaten_kota', 'indeks_pertumbuhan_formatted']].style.applymap(
                lambda x: 'color: green;' if float(x) > 0 else 'color: red;', subset=['indeks_pertumbuhan_formatted']))

            st.write("Persentase Perubahan Transportasi per Kabupaten/Kota (2021-2022):")
            st.dataframe(df[['nama_kabupaten_kota', 'persentase_pertumbuhan_formatted']].style.applymap(
                lambda x: 'color: green;' if float(x[:-1]) > 0 else 'color: red;', subset=['persentase_pertumbuhan_formatted']))
            
        else:
            st.error(f"Data yang diunggah harus memiliki kolom: {', '.join(kolom_diperlukan)}")

    elif submenu == "Keseluruhan":
        kolom_diperlukan = {'jumlah_transportasi_2021', 'jumlah_transportasi_2022',}
        if kolom_diperlukan.issubset(df.columns):
            # Hitung total transportasi untuk seluruh daerah
            total_transportasi_2021 = df['jumlah_transportasi_2021'].sum()
            total_transportasi_2022 = df['jumlah_transportasi_2022'].sum()
            
            transportasi_per_area_2021 = total_transportasi_2021
            transportasi_per_area_2022 = total_transportasi_2022
            
            # Hitung persentase pertumbuhan keseluruhan
            indeks_pertumbuhan = ((transportasi_per_area_2022 - transportasi_per_area_2021) / transportasi_per_area_2021)
            persentase_pertumbuhan = indeks_pertumbuhan * 100
            
            # Format hasil perhitungan
            transportasi_per_area_2022_formatted = f"{transportasi_per_area_2022:.4f}"
            persentase_pertumbuhan_formatted = f"{persentase_pertumbuhan:.2f}%"
            
            # Tentukan arah panah dan warna berdasarkan persentase perubahan
            if persentase_pertumbuhan > 0:
                arrow = "&#x25B2;"  # Panah ke atas
                arrow_color = "green"
            else:
                arrow = "&#x25BC;"  # Panah ke bawah
                arrow_color = "red"

            # Tampilkan hasil indeks transportasi
            st.markdown(f"""
                <div style="background-color: #f0f8f8; padding: 15px; border-radius: 10px; text-align: center;">
                    <p style="font-size: 24px;">Transportasi Jawa Barat Tahun 2022</p>
                    <p style="font-size: 48px; font-weight: bold; color: green;">{indeks_pertumbuhan:.2f}</p>
                    <p style="font-size: 24px;">Indeks Transportasi Tahun 2022</p>
                    <p style="font-size: 24px; color: {arrow_color};">{arrow} {persentase_pertumbuhan_formatted} dari tahun sebelumnya</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"Data yang diunggah harus memiliki kolom: {', '.join(kolom_diperlukan)}")

def process_and_display_infrastructure_index(file):
    df = pd.read_excel(file)
    
    submenu = st.selectbox("Pilih Indeks yang Ingin Ditampilkan", ["Per Kabupaten/Kota", "Keseluruhan"])
    
    if submenu == "Per Kabupaten/Kota":
        kolom_diperlukan = {'nama_kabupaten_kota', 'jumlah_infrastruktur_2021', 'jumlah_infrastruktur_2022'}
        if kolom_diperlukan.issubset(df.columns):
            # Hitung infrastruktur per area (tidak perlu normalisasi luas jika tidak ada data luas)
            df['infrastruktur_per_area_2021'] = df['jumlah_infrastruktur_2021']
            df['infrastruktur_per_area_2022'] = df['jumlah_infrastruktur_2022']

            # Hitung persentase pertumbuhan per kabupaten/kota
            df['persentase_pertumbuhan'] = ((df['infrastruktur_per_area_2022'] - df['infrastruktur_per_area_2021']) / df['infrastruktur_per_area_2021']) * 100
            df['indeks_pertumbuhan'] = ((df['infrastruktur_per_area_2022'] - df['infrastruktur_per_area_2021']) / df['infrastruktur_per_area_2021'])

            # Format hasil perhitungan
            df['indeks_pertumbuhan_formatted'] = df['indeks_pertumbuhan'].map(lambda x: f"{x:.4f}")
            df['persentase_pertumbuhan_formatted'] = df['persentase_pertumbuhan'].map(lambda x: f"{x:.2f}%")

            # Tampilkan hasil perhitungan
            st.write("Indeks Infrastruktur per Kabupaten/Kota pada Tahun 2022:")
            st.dataframe(df[['nama_kabupaten_kota', 'indeks_pertumbuhan_formatted']].style.applymap(
                lambda x: 'color: green;' if float(x) > 0 else 'color: red;', subset=['indeks_pertumbuhan_formatted']))

            st.write("Persentase Pertumbuhan Indeks Infrastruktur per Kabupaten/Kota (2021-2022):")
            st.dataframe(df[['nama_kabupaten_kota', 'persentase_pertumbuhan_formatted']].style.applymap(
                lambda x: 'color: green;' if float(x[:-1]) > 0 else 'color: red;', subset=['persentase_pertumbuhan_formatted']))
            
        else:
            st.error(f"Data yang diunggah harus memiliki kolom: {', '.join(kolom_diperlukan)}")

    elif submenu == "Keseluruhan":
        kolom_diperlukan = {'jumlah_infrastruktur_2021', 'jumlah_infrastruktur_2022'}
        if kolom_diperlukan.issubset(df.columns):
            # Hitung total infrastruktur untuk seluruh daerah
            total_infrastruktur_2021 = df['jumlah_infrastruktur_2021'].sum()
            total_infrastruktur_2022 = df['jumlah_infrastruktur_2022'].sum()
            
            infrastruktur_per_area_2021 = total_infrastruktur_2021
            infrastruktur_per_area_2022 = total_infrastruktur_2022
            
            # Hitung persentase pertumbuhan keseluruhan
            indeks_pertumbuhan = ((infrastruktur_per_area_2022 - infrastruktur_per_area_2021) / infrastruktur_per_area_2021)
            persentase_pertumbuhan = indeks_pertumbuhan * 100
            
            # Format hasil perhitungan
            infrastruktur_per_area_2022_formatted = f"{infrastruktur_per_area_2022:.4f}"
            persentase_pertumbuhan_formatted = f"{persentase_pertumbuhan:.2f}%"
            
            # Tentukan arah panah dan warna berdasarkan persentase perubahan
            if persentase_pertumbuhan > 0:
                arrow = "&#x25B2;"  # Panah ke atas
                arrow_color = "green"
            else:
                arrow = "&#x25BC;"  # Panah ke bawah
                arrow_color = "red"

            # Tampilkan hasil indeks infrastruktur
            st.markdown(f"""
                <div style="background-color: #f0f8f8; padding: 15px; border-radius: 10px; text-align: center;">
                    <p style="font-size: 24px;">Infrastruktur Jawa Barat Tahun 2022</p>
                    <p style="font-size: 48px; font-weight: bold; color: green;">{indeks_pertumbuhan:.2f}</p>
                    <p style="font-size: 24px;">Indeks Infrastruktur Tahun 2022</p>
                    <p style="font-size: 24px; color: {arrow_color};">{arrow} {persentase_pertumbuhan_formatted} dari tahun sebelumnya</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"Data yang diunggah harus memiliki kolom: {', '.join(kolom_diperlukan)}")

# Halaman untuk mengimpor data
def import_data_page():
    st.title("Import Data")
    
    # Pilihan visualisasi untuk impor menggunakan selectbox
    if 'selected_visualization_import' not in st.session_state:
        st.session_state['selected_visualization_import'] = "Pengelompokan berdasarkan jumlah infrastruktur"
    
    st.session_state['selected_visualization_import'] = st.selectbox("Pilih visualisasi untuk mengimpor data:", 
                                        ["Pengelompokan berdasarkan jumlah infrastruktur",
                                         "Pengelompokan berdasarkan jumlah transportasi",
                                         "Pendanaan dalam bidang",
                                         "Pengelompokan daerah tertinggal",
                                         "Indeks infrastruktur dalam periode satu tahun",
                                         "Indeks transportasi dalam periode satu tahun"])
    
    uploaded_files = upload_data()
    
    if uploaded_files:
        if st.session_state['selected_visualization_import'] == "Pengelompokan berdasarkan jumlah infrastruktur" and len(uploaded_files) == 2:
            st.session_state['visualization_1_files'] = uploaded_files
            st.success("Data untuk Visualisasi 1 berhasil diimpor.")
        elif st.session_state['selected_visualization_import'] == "Pengelompokan berdasarkan jumlah transportasi" and len(uploaded_files) == 4:
            st.session_state['visualization_2_files'] = uploaded_files
            st.success("Data untuk Visualisasi 2 berhasil diimpor.")
        elif st.session_state['selected_visualization_import'] == "Pendanaan dalam bidang" and len(uploaded_files) == 1:
            st.session_state['visualization_3_files'] = uploaded_files
            st.success("Data untuk Visualisasi 3 berhasil diimpor.")
        elif st.session_state['selected_visualization_import'] == "Pengelompokan daerah tertinggal" and len(uploaded_files) == 2:
            st.session_state['visualization_4_files'] = uploaded_files
            st.success("Data untuk Visualisasi 4 berhasil diimpor.")
        elif st.session_state['selected_visualization_import'] == "Indeks infrastruktur dalam periode satu tahun" and len(uploaded_files) == 1:
            st.session_state['visualization_infra_index_files'] = uploaded_files
            st.success("Data untuk Visualisasi Indeks Infrastruktur berhasil diimpor.")
        elif st.session_state['selected_visualization_import'] == "Indeks transportasi dalam periode satu tahun" and len(uploaded_files) == 1:
            st.session_state['visualization_transport_index_files'] = uploaded_files
            st.success("Data untuk Visualisasi Indeks Transportasi berhasil diimpor.")
        else:
            st.error("Jumlah file yang diimpor tidak sesuai dengan yang dibutuhkan untuk visualisasi ini.")

# Halaman untuk visualisasi data
def visualization_page():
    st.title("Visualisasi Data")
    
    selected_visualization = st.selectbox("Pilih visualisasi yang ingin ditampilkan:", 
                                          ["Pengelompokan berdasarkan jumlah infrastruktur",
                                           "Pengelompokan berdasarkan jumlah transportasi",
                                           "Pendanaan dalam bidang",
                                           "Pengelompokan daerah tertinggal",
                                           "Indeks infrastruktur dalam periode satu tahun",
                                           "Indeks transportasi dalam periode satu tahun"])

    if selected_visualization == "Pengelompokan berdasarkan jumlah infrastruktur" and 'visualization_1_files' in st.session_state:
        df_clustered = process_visualization_one(st.session_state['visualization_1_files'])
        visualize_choropleth_map(df_clustered, "Pengelompokan Berdasarkan Jumlah Infrastruktur", target_cluster=1)
    
    elif selected_visualization == "Pengelompokan berdasarkan jumlah transportasi" and 'visualization_2_files' in st.session_state:
        df_clustered = process_visualization_two(st.session_state['visualization_2_files'])
        visualize_choropleth_map(df_clustered, "Pengelompokan Berdasarkan Jumlah Transportasi", target_cluster=1)
    
    elif selected_visualization == "Pengelompokan daerah tertinggal" and 'visualization_4_files' in st.session_state:
        df_clustered = process_visualization_four(st.session_state['visualization_4_files'])
        visualize_choropleth_map(df_clustered, "Pengelompokan Daerah Tertinggal", target_cluster=3)
    
    elif selected_visualization == "Indeks infrastruktur dalam periode satu tahun" and 'visualization_infra_index_files' in st.session_state:
        process_and_display_infrastructure_index(st.session_state['visualization_infra_index_files'][0])
    
    elif selected_visualization == "Indeks transportasi dalam periode satu tahun" and 'visualization_transport_index_files' in st.session_state:
        process_and_display_transportation_index(st.session_state['visualization_transport_index_files'][0])

    elif selected_visualization == "Pendanaan dalam bidang" and 'visualization_3_files' in st.session_state:
        process_and_store_pendanaan_pie_chart(st.session_state['visualization_3_files'][0])
    else:
        st.write("Data belum diimpor atau visualisasi tidak ditemukan.")

def dashboard_page():
    st.title("Dashboard")
    
    # Layout untuk Indeks Transportasi dan Indeks Infrastruktur
    col1, col2 = st.columns(2)

    # Menampilkan Indeks Transportasi
    with col1:
        st.subheader("Indeks Transportasi")
        if 'visualization_transport_index_files' in st.session_state:
            process_and_store_transportation_index(st.session_state['visualization_transport_index_files'][0])
            st.markdown(st.session_state['transportation_index_html'], unsafe_allow_html=True)
        else:
            st.write("Data tidak tersedia.")
    
    # Menampilkan Indeks Infrastruktur
    with col2:
        st.subheader("Indeks Infrastruktur")
        if 'visualization_infra_index_files' in st.session_state:
            process_and_store_infrastructure_index(st.session_state['visualization_infra_index_files'][0])
            st.markdown(st.session_state['infrastructure_index_html'], unsafe_allow_html=True)
        else:
            st.write("Data tidak tersedia.")
    
    # Distribusi Belanja Pemerintah
    st.subheader("Distribusi Belanja Pemerintah Jawa Barat")
    if 'visualization_3_files' in st.session_state:
        process_and_store_pendanaan_pie_chart(st.session_state['visualization_3_files'][0])
        st.pyplot(st.session_state['pendanaan_pie_chart'])
        st.markdown(st.session_state['pendanaan_description'], unsafe_allow_html=True)
    else:
        st.write("Data tidak tersedia.")

# Simpan hasil visualisasi dan indeks ke dalam session_state setelah mereka dihitung
def process_and_store_transportation_index(file):
    df = pd.read_excel(file)
    total_transportasi_2021 = df['jumlah_transportasi_2021'].sum()
    total_transportasi_2022 = df['jumlah_transportasi_2022'].sum()

    # Menghitung indeks pertumbuhan dengan cara yang sama seperti di process_and_display_transportation_index
    indeks_pertumbuhan = (total_transportasi_2022 - total_transportasi_2021) / total_transportasi_2021
    persentase_pertumbuhan = indeks_pertumbuhan * 100

    # Tentukan arah panah dan warna berdasarkan persentase perubahan
    if persentase_pertumbuhan > 0:
        arrow = "&#x25B2;"  # Panah ke atas
        arrow_color = "green"
    else:
        arrow = "&#x25BC;"  # Panah ke bawah
        arrow_color = "red"

    st.session_state['transportation_index_html'] = f"""
        <div style="background-color: #f0f8f8; padding: 15px; border-radius: 10px; text-align: center;">
            <p style="font-size: 24px;">Transportasi Jawa Barat Tahun 2022</p>
            <p style="font-size: 48px; font-weight: bold; color: green;">{indeks_pertumbuhan:.2f}</p>
            <p style="font-size: 24px;">Indeks Transportasi Tahun 2022</p>
            <p style="font-size: 24px; color: {arrow_color};">{arrow} {persentase_pertumbuhan:.2f}% dari tahun sebelumnya</p>
        </div>
    """

def process_and_store_infrastructure_index(file):
    df = pd.read_excel(file)
    total_infrastruktur_2021 = df['jumlah_infrastruktur_2021'].sum()
    total_infrastruktur_2022 = df['jumlah_infrastruktur_2022'].sum()

    # Menghitung indeks pertumbuhan dengan cara yang sama seperti di process_and_display_infrastructure_index
    indeks_pertumbuhan = (total_infrastruktur_2022 - total_infrastruktur_2021) / total_infrastruktur_2021
    persentase_pertumbuhan = indeks_pertumbuhan * 100

    # Tentukan arah panah dan warna berdasarkan persentase perubahan
    if persentase_pertumbuhan > 0:
        arrow = "&#x25B2;"  # Panah ke atas
        arrow_color = "green"
    else:
        arrow = "&#x25BC;"  # Panah ke bawah
        arrow_color = "red"

    st.session_state['infrastructure_index_html'] = f"""
        <div style="background-color: #f0f8f8; padding: 15px; border-radius: 10px; text-align: center;">
            <p style="font-size: 24px;">Infrastruktur Jawa Barat Tahun 2022</p>
            <p style="font-size: 48px; font-weight: bold; color: green;">{indeks_pertumbuhan:.2f}</p>
            <p style="font-size: 24px;">Indeks Infrastruktur Tahun 2022</p>
            <p style="font-size: 24px; color: {arrow_color};">{arrow} {persentase_pertumbuhan:.2f}% dari tahun sebelumnya</p>
        </div>
    """

def display_pendanaan_pie_chart():
    if 'pendanaan_pie_chart' in st.session_state and 'pendanaan_description' in st.session_state:
        st.pyplot(st.session_state['pendanaan_pie_chart'])
        st.markdown(st.session_state['pendanaan_description'], unsafe_allow_html=True)
    else:
        st.warning("Tidak ada data pendanaan yang tersedia untuk ditampilkan.")

# Sidebar Layout
st.sidebar.markdown("<h2 style='margin-bottom: 25px;'>Menu</h2>", unsafe_allow_html=True)

# Button untuk Navigasi
import_data_button = st.sidebar.button("Import Data")
visualize_data_button = st.sidebar.button("Tampil Visualisasi")
dashboard_button = st.sidebar.button("Dashboard")

# Logika untuk menavigasi halaman berdasarkan tombol yang diklik
if import_data_button:
    st.session_state['current_page'] = "Import Data"
elif visualize_data_button:
    st.session_state['current_page'] = "Tampil Visualisasi"
elif dashboard_button:
    st.session_state['current_page'] = "Dashboard"

# Render halaman sesuai pilihan
if st.session_state.get('current_page') == "Import Data":
    import_data_page()  # Fungsi untuk mengimpor data
elif st.session_state.get('current_page') == "Tampil Visualisasi":
    visualization_page()  # Fungsi untuk menampilkan visualisasi
elif st.session_state.get('current_page') == "Dashboard":
    dashboard_page()  # Fungsi untuk menampilkan dashboard
else:
    st.sidebar.write("Pilih opsi di atas untuk melanjutkan.")