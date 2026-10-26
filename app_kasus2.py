"""
Dashboard Streamlit - Bedah Kasus 2: Dataset Profil Mahasiswa
Nama : Ganesia Alkhan Fikriano
NIM  : 241051019

Jalankan:  streamlit run app_kasus2.py
Data    :  data_profil_mahasiswa.csv (satu folder dengan file ini). Jika tidak ada,
           data sintetis 1.000 baris dibuat otomatis dengan seed yang sama seperti di notebook.
"""
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------- Identitas & konstanta
NAMA, NIM = "Ganesia Alkhan Fikriano", "241051019"
BIRU, BIRU_TUA, ORANYE, ORANYE_TUA = "#2E9BD6", "#1F6FA8", "#F5A03A", "#B4570A"
BLUES = ["#08306B", "#08519C", "#2171B5", "#4292C6", "#6BAED6", "#9ECAE1", "#C6DBEF", "#DEEBF7"]
SEM_URUT = list(range(1, 11))
PREDIKAT = ["Perlu Pembinaan", "Memuaskan", "Sangat Memuaskan", "Dengan Pujian"]
KOLOM_WAJIB = ["Jurusan", "Semester", "IPK", "Usia"]

st.set_page_config(page_title=f"Dashboard Profil Mahasiswa - {NIM}", page_icon="🎓", layout="wide")

def buat_data_mahasiswa(n=1000, seed=241051019):
    """Dataset profil mahasiswa sintetis. 1 baris = 1 mahasiswa.
    Kolom: Jurusan (nominal), Semester (ordinal 1-10), IPK (kontinu 0-4), Usia (kontinu, dicatat tahun penuh).
    """
    rng = np.random.default_rng(seed)

    # jurusan: (proporsi mahasiswa, rata-rata IPK dasar)
    jurusan = {
        "Teknik Informatika": (0.18, 3.15), "Manajemen": (0.17, 3.30),
        "Sistem Informasi": (0.15, 3.25), "Akuntansi": (0.13, 3.30),
        "Ilmu Hukum": (0.11, 3.25), "Psikologi": (0.09, 3.40),
        "Teknik Sipil": (0.09, 3.05), "Desain Komunikasi Visual": (0.08, 3.35),
    }
    nama = list(jurusan)
    p_jur = np.array([v[0] for v in jurusan.values()])
    base_ipk = np.array([v[1] for v in jurusan.values()])

    # Semester 1-8 masa studi normal, 9-10 mahasiswa yang memperpanjang studi.
    # Jumlah mahasiswa menurun di semester atas (mahasiswa mengundurkan diri / lulus).
    p_sem = np.array([17, 15, 15, 13, 12, 11, 9, 6, 1.5, 0.5])
    semester = rng.choice(np.arange(1, 11), size=n, p=p_sem / p_sem.sum())
    idx_jur = rng.choice(len(nama), size=n, p=p_jur / p_jur.sum())

    # Usia: usia saat masuk (miring ke kanan) + lama studi; sebagian kecil mahasiswa dewasa/pekerja
    masuk = 17.6 + rng.gamma(2.0, 0.45, n)
    dewasa = rng.random(n) < 0.03
    masuk = np.where(dewasa, masuk + rng.uniform(3, 12, n), masuk)
    usia = np.floor(masuk + (semester - 1) / 2).astype(int)
    usia = np.clip(usia, 17, 45)

    # IPK: dipengaruhi jurusan dan semester; makin tinggi semester, sebaran makin sempit
    mu = base_ipk[idx_jur] + 0.015 * (semester - 1) - 0.05 * (semester > 8)
    sd = 0.40 / np.sqrt(1 + 0.20 * (semester - 1))
    ipk = rng.normal(mu, sd)
    bermasalah = rng.random(n) < 0.05                       # mahasiswa dengan kendala akademik
    ipk = np.where(bermasalah, ipk - rng.uniform(0.4, 1.0, n), ipk)
    ipk = np.where(ipk > 4.0, 8.0 - ipk, ipk)               # pantulkan di batas 4.00 (hindari tumpukan di 4.00)
    ipk = np.round(np.clip(ipk, 1.0, 4.0), 2)

    return pd.DataFrame({"Jurusan": np.array(nama)[idx_jur], "Semester": semester, "IPK": ipk, "Usia": usia})


# ----------------------------------------------------------------------------- Gaya
st.markdown("""
<style>
.block-container { padding-top: 1.6rem; padding-bottom: 4.5rem; }
.hdr { display:flex; align-items:stretch; gap:16px; margin-bottom:.4rem; }
.hdr .stripe { display:flex; flex-direction:column; width:8px; border-radius:4px; overflow:hidden; }
.hdr .stripe span { flex:1; }
.hdr h1 { margin:0; padding:0; font-size:2rem; line-height:1.15; }
.hdr p { margin:.25rem 0 0 0; color:#5b6068; }
.hdr .idbox { margin-left:auto; text-align:right; padding:.5rem .9rem; border:1px solid #d9dce1; border-radius:8px; font-size:.92rem; line-height:1.45; }
.tag { border-left:5px solid var(--c); padding:.35rem .8rem; margin:.2rem 0 .8rem 0; background:rgba(127,127,127,.08); border-radius:0 6px 6px 0; font-size:.93rem; }
.footer-id { position:fixed; left:0; right:0; bottom:0; z-index:999; text-align:center; font-size:.82rem;
             padding:.4rem; background:rgba(255,255,255,.96); color:#444; border-top:1px solid #d9dce1; }
.sid { border:1px solid #d9dce1; border-radius:8px; padding:.6rem .8rem; line-height:1.5; font-size:.92rem; }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------- Utilitas
def id_num(x, d=0):
    """Angka gaya Indonesia: 1.234,56"""
    return f"{x:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def tag(teks, warna):
    st.markdown(f'<div class="tag" style="--c:{warna}">{teks}</div>', unsafe_allow_html=True)


def rapikan(fig, tinggi=420, judul=None):
    fig.update_layout(template="plotly_white", height=tinggi, margin=dict(l=10, r=10, t=55 if judul else 25, b=10),
                      legend_title_text="", title=dict(text=judul, font=dict(size=15)) if judul else None)
    return fig


def sumbu_semester(fig):
    """Pertahankan urutan ordinal Semester pada sumbu x."""
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=[str(i) for i in SEM_URUT])
    return fig


# ----------------------------------------------------------------------------- Data
@st.cache_data(show_spinner=False)
def muat_bawaan():
    csv = Path(__file__).with_name("data_profil_mahasiswa.csv")
    return pd.read_csv(csv) if csv.exists() else buat_data_mahasiswa(1000)


def siapkan(df):
    df = df.copy()
    df["Jurusan"] = df["Jurusan"].astype(str)
    df["Semester"] = df["Semester"].astype("int64")
    df["IPK"] = df["IPK"].astype(float)
    df["Usia"] = df["Usia"].astype("int64")
    df["Semester_Label"] = df["Semester"].astype(str)                        # untuk sumbu kategori berurutan
    df["Predikat"] = pd.cut(df["IPK"], [0, 1.995, 2.755, 3.505, 4.0], labels=PREDIKAT, ordered=True)
    return df


# ----------------------------------------------------------------------------- Sidebar
with st.sidebar:
    st.markdown(f'<div class="sid"><b>{NAMA}</b><br>NIM {NIM}</div>', unsafe_allow_html=True)
    st.markdown("### Filter data")
    data_mentah = muat_bawaan()
    with st.expander("Gunakan data lain (CSV)"):
        up = st.file_uploader("Unggah CSV dengan kolom: Jurusan, Semester, IPK, Usia", type="csv")
        if up is not None:
            try:
                tmp = pd.read_csv(up)
                hilang = [k for k in KOLOM_WAJIB if k not in tmp.columns]
                if hilang:
                    st.error(f"Kolom belum lengkap, tidak ada: {', '.join(hilang)}. Memakai data bawaan.")
                elif not tmp["Semester"].between(1, 10).all():
                    st.error("Semester harus berada pada rentang 1-10. Memakai data bawaan.")
                else:
                    data_mentah = tmp
                    st.success(f"{len(tmp):,} baris dimuat.".replace(",", "."))
            except Exception as e:  # noqa: BLE001
                st.error(f"CSV tidak bisa dibaca ({e}). Memakai data bawaan.")

df = siapkan(data_mentah)

semua_jur = sorted(df["Jurusan"].unique())
jur_pilih = st.sidebar.multiselect("Jurusan", semua_jur, default=semua_jur)
sem_rng = st.sidebar.select_slider("Semester", options=SEM_URUT, value=(1, 10), help="Ordinal: urutan 1 sampai 10.")
imin, imax = float(np.floor(df["IPK"].min() * 100) / 100), float(np.ceil(df["IPK"].max() * 100) / 100)
ipk_rng = st.sidebar.slider("IPK", imin, imax, (imin, imax), step=0.01, format="%.2f")
umin, umax = int(df["Usia"].min()), int(df["Usia"].max())
usia_rng = st.sidebar.slider("Usia (tahun)", umin, umax, (umin, umax))

st.sidebar.markdown("### Pengaturan tampilan")
cutoff = st.sidebar.slider("Batas IPK pembanding", 2.0, 4.0, 3.5, 0.05, format="%.2f",
                           help="Dipakai untuk kartu '% IPK di atas batas' dan garis pada grafik IPK.")

mask = (df["Jurusan"].isin(jur_pilih) & df["Semester"].between(*sem_rng)
        & df["IPK"].between(*ipk_rng) & df["Usia"].between(*usia_rng))
f = df[mask]

# ----------------------------------------------------------------------------- Header
st.markdown(f"""
<div class="hdr">
  <div class="stripe"><span style="background:{BIRU}"></span><span style="background:{ORANYE}"></span></div>
  <div><h1>Dashboard Profil Mahasiswa</h1>
       <p>Bedah Kasus 2. Data sintetis 1.000 mahasiswa, divisualisasikan sesuai skala pengukuran tiap kolom.</p></div>
  <div class="idbox"><b>{NAMA}</b><br>NIM {NIM}</div>
</div>
""", unsafe_allow_html=True)
st.caption("Kode warna mengikuti gambar tugas: biru untuk data kategorik (nominal dan ordinal), oranye untuk numerik kontinu.")
st.markdown(f'<div class="footer-id">{NAMA} &nbsp;|&nbsp; NIM {NIM} &nbsp;|&nbsp; Bedah Kasus 2: Dataset Profil Mahasiswa</div>',
            unsafe_allow_html=True)

if f.empty:
    st.warning("Tidak ada mahasiswa yang cocok dengan filter. Longgarkan pilihan jurusan, rentang semester, atau slider IPK/usia di sidebar.")
    st.stop()

# ----------------------------------------------------------------------------- KPI
k = st.columns(5)
k[0].metric("Jumlah mahasiswa", id_num(len(f)), f"{len(f) / len(df):.0%} dari seluruh data", delta_color="off")
k[1].metric("Rata-rata IPK", id_num(f["IPK"].mean(), 2), f"median {id_num(f['IPK'].median(), 2)}", delta_color="off")
k[2].metric("Median semester", id_num(f["Semester"].median()), f"modus {f['Semester'].mode().iloc[0]}", delta_color="off")
k[3].metric("Rata-rata usia", f"{id_num(f['Usia'].mean(), 1)} th", f"median {f['Usia'].median():.0f} th", delta_color="off")
k[4].metric(f"IPK >= {id_num(cutoff, 2)}", f"{(f['IPK'] >= cutoff).mean():.1%}", f"{int((f['IPK'] >= cutoff).sum())} mahasiswa", delta_color="off")

tabs = st.tabs(["Ringkasan", "Jurusan", "Semester", "IPK", "Usia", "Hubungan", "Data"])

# ============================================================================= TAB 1 RINGKASAN
with tabs[0]:
    c1, c2 = st.columns(2)
    jc = f["Jurusan"].value_counts().reset_index()
    jc.columns = ["Jurusan", "Jumlah"]
    fig = px.pie(jc, names="Jurusan", values="Jumlah", hole=.5, color_discrete_sequence=BLUES)
    fig.update_traces(textinfo="percent", sort=False)
    c1.plotly_chart(rapikan(fig, 400, "Komposisi mahasiswa per Jurusan"), width="stretch", key="r_pie")

    sc = f["Semester"].value_counts().reindex(SEM_URUT, fill_value=0).reset_index()
    sc.columns = ["Semester", "Jumlah"]
    sc["Semester"] = sc["Semester"].astype(str)
    fig = px.bar(sc, x="Semester", y="Jumlah", color_discrete_sequence=[BIRU_TUA], text="Jumlah")
    fig.update_traces(textposition="outside", cliponaxis=False)
    c2.plotly_chart(sumbu_semester(rapikan(fig, 400, "Jumlah mahasiswa per Semester (berurutan)")), width="stretch", key="r_sem")

    ipk_j = f.groupby("Jurusan")["IPK"].mean()
    st.info(f"**Temuan cepat.** Jurusan terbesar: **{jc.iloc[0]['Jurusan']}** ({jc.iloc[0]['Jumlah'] / len(f):.0%}). "
            f"Rata-rata IPK tertinggi: **{ipk_j.idxmax()}** ({ipk_j.max():.2f}), terendah: **{ipk_j.idxmin()}** ({ipk_j.min():.2f}). "
            f"Mahasiswa dengan IPK di bawah 2,76: **{(f['IPK'] < 2.76).mean():.1%}**.")

# ============================================================================= TAB 2 JURUSAN (NOMINAL)
with tabs[1]:
    tag("<b>Kategorik (Nominal)</b>: Jurusan hanya berupa label pembeda. Visualisasi yang sesuai: Bar chart atau Pie chart.", BIRU)
    a, b = st.columns(2)
    jenis = a.radio("Jenis grafik", ["Bar chart", "Pie chart"], horizontal=True)
    if jenis == "Bar chart":
        ukuran = b.radio("Ukuran", ["Jumlah mahasiswa", "Rata-rata IPK", "Rata-rata usia"], horizontal=True)
    else:
        ukuran = "Jumlah mahasiswa"
        b.caption("Pie chart hanya untuk komposisi (jumlah mahasiswa).")

    agg = f.groupby("Jurusan").agg(**{"Jumlah mahasiswa": ("IPK", "size"), "Rata-rata IPK": ("IPK", "mean"),
                                      "Median IPK": ("IPK", "median"), "Rata-rata usia": ("Usia", "mean"),
                                      "Median semester": ("Semester", "median")})
    agg["Persen"] = agg["Jumlah mahasiswa"] / agg["Jumlah mahasiswa"].sum() * 100
    d = agg.sort_values(ukuran).reset_index()
    c1, c2 = st.columns([1.15, 1])
    if jenis == "Bar chart":
        fig = px.bar(d, x=ukuran, y="Jurusan", orientation="h", color_discrete_sequence=[BIRU], text=ukuran)
        fig.update_traces(texttemplate="%{text:.2f}" if ukuran != "Jumlah mahasiswa" else "%{text:,.0f}", textposition="outside", cliponaxis=False)
        if ukuran == "Rata-rata IPK":
            fig.update_xaxes(range=[max(0, d[ukuran].min() - .3), min(4, d[ukuran].max() + .15)])
            c1.caption("Sumbu IPK dipotong agar selisih antar jurusan terlihat; perhatikan angka pada batang.")
    else:
        fig = px.pie(d.sort_values("Jumlah mahasiswa", ascending=False), names="Jurusan", values="Jumlah mahasiswa", hole=.45, color_discrete_sequence=BLUES)
        fig.update_traces(textinfo="percent+label", sort=False)
    c1.plotly_chart(rapikan(fig, 460, f"{ukuran} per Jurusan"), width="stretch", key="j_main")

    fig = px.box(f, x="IPK", y="Jurusan", color_discrete_sequence=[ORANYE], points="outliers")
    fig.update_yaxes(categoryorder="median ascending")
    c2.plotly_chart(rapikan(fig, 460, "Sebaran IPK per Jurusan"), width="stretch", key="j_box")

    st.markdown(f"**Modus:** {agg['Jumlah mahasiswa'].idxmax()} ({int(agg['Jumlah mahasiswa'].max())} mahasiswa)")
    st.dataframe(agg.sort_values("Jumlah mahasiswa", ascending=False).reset_index(), hide_index=True, width="stretch", column_config={
        "Rata-rata IPK": st.column_config.NumberColumn(format="%.2f"), "Median IPK": st.column_config.NumberColumn(format="%.2f"),
        "Rata-rata usia": st.column_config.NumberColumn(format="%.1f"),
        "Persen": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})

# ============================================================================= TAB 3 SEMESTER (ORDINAL)
with tabs[2]:
    tag("<b>Kategorik (Ordinal)</b>: Semester memiliki tingkatan dan urutan jelas (1, 2, 3, ...). Visualisasi yang sesuai: Bar chart berurutan.", BIRU)
    a, b = st.columns(2)
    mode = a.radio("Tampilkan", ["Jumlah", "Persentase", "Persentase kumulatif"], horizontal=True)
    pecah = b.toggle("Pecah per jurusan (stacked)", value=False)

    ts = f["Semester"].value_counts().reindex(SEM_URUT, fill_value=0).to_frame("Jumlah")
    ts["Persentase"] = ts["Jumlah"] / ts["Jumlah"].sum() * 100
    ts["Persentase kumulatif"] = ts["Persentase"].cumsum()
    ts = ts.reset_index(names="Semester").assign(Semester=lambda x: x["Semester"].astype(str))

    c1, c2 = st.columns([1.2, 1])
    if pecah and mode == "Jumlah":
        sj = f.groupby(["Semester_Label", "Jurusan"]).size().reset_index(name="Jumlah")
        fig = px.bar(sj, x="Semester_Label", y="Jumlah", color="Jurusan", color_discrete_sequence=px.colors.qualitative.T10, labels={"Semester_Label": "Semester"})
    else:
        if pecah:
            b.caption("Pecah per jurusan hanya untuk mode Jumlah.")
        fig = px.bar(ts, x="Semester", y=mode, color_discrete_sequence=[BIRU_TUA], text=mode) if mode != "Persentase kumulatif" else \
            px.line(ts, x="Semester", y=mode, markers=True, color_discrete_sequence=[BIRU_TUA], text=mode)
        fig.update_traces(texttemplate="%{text:,.0f}" if mode == "Jumlah" else "%{text:.1f}%", textposition="top center" if mode == "Persentase kumulatif" else "outside", cliponaxis=False)
    med = f["Semester"].median()
    c1.plotly_chart(sumbu_semester(rapikan(fig, 440, f"{mode} mahasiswa per Semester (berurutan)")), width="stretch", key="s_main")

    hm = pd.crosstab(f["Jurusan"], f["Semester"]).reindex(columns=SEM_URUT, fill_value=0)
    fig = px.imshow(hm, text_auto=True, color_continuous_scale="Blues", aspect="auto", labels=dict(x="Semester", y="", color="Mahasiswa"))
    fig.update_xaxes(type="category")
    c2.plotly_chart(rapikan(fig, 440, "Heatmap Jurusan x Semester"), width="stretch", key="s_heat")

    m = st.columns(5)
    m[0].metric("Median", f"{med:.0f}")
    m[1].metric("Modus", f"{f['Semester'].mode().iloc[0]}")
    m[2].metric("Kuartil 1 (Q1)", f"{f['Semester'].quantile(.25):.0f}")
    m[3].metric("Kuartil 3 (Q3)", f"{f['Semester'].quantile(.75):.0f}")
    m[4].metric("Semester > 8", f"{(f['Semester'] > 8).mean():.1%}", help="Mahasiswa yang memperpanjang studi.")
    st.caption("Untuk data ordinal, ukuran pemusatan yang tepat adalah median dan modus, bukan rata-rata.")
    st.dataframe(ts, hide_index=True, width="stretch", column_config={
        "Persentase": st.column_config.NumberColumn(format="%.1f%%"), "Persentase kumulatif": st.column_config.NumberColumn(format="%.1f%%")})

# ============================================================================= TAB 4 IPK
with tabs[3]:
    tag("<b>Numerik (Kontinu)</b>: IPK berupa rentang/desimal. Visualisasi yang sesuai: Histogram (distribusi) atau Box plot (sebaran dan pencilan).", ORANYE)
    a, b, c = st.columns(3)
    jenis = a.radio("Jenis grafik", ["Histogram", "Box plot", "Violin"], horizontal=True, key="ipk_jenis")
    grup = b.selectbox("Kelompokkan menurut", ["Tidak ada", "Jurusan", "Semester"], key="ipk_grup")
    bins = c.slider("Jumlah bin (histogram)", 10, 60, 30, key="ipk_bins", disabled=jenis != "Histogram")
    gcol = {"Tidak ada": None, "Jurusan": "Jurusan", "Semester": "Semester_Label"}[grup]

    c1, c2 = st.columns([1.3, 1])
    if jenis == "Histogram":
        fig = px.histogram(f, x="IPK", nbins=bins, color=gcol, marginal="box", barmode="stack",
                           color_discrete_sequence=px.colors.qualitative.Set2 if gcol else [ORANYE],
                           category_orders={"Semester_Label": [str(i) for i in SEM_URUT]})
        fig.add_vline(x=f["IPK"].mean(), line_dash="dash", line_color="#C0392B")
        fig.add_vline(x=f["IPK"].median(), line_dash="dash", line_color="#27AE60")
        c1.caption("Garis putus-putus merah = mean, hijau = median.")
    else:
        fn = px.box if jenis == "Box plot" else px.violin
        kw = dict(box=True, points=False) if jenis == "Violin" else dict(points="outliers")
        if gcol:
            fig = fn(f, x=gcol, y="IPK", color_discrete_sequence=[ORANYE], category_orders={"Semester_Label": [str(i) for i in SEM_URUT]}, **kw)
            if gcol == "Jurusan":
                fig.update_xaxes(categoryorder="median ascending")
            else:
                sumbu_semester(fig)
                fig.update_xaxes(title="Semester")
        else:
            fig = fn(f, y="IPK", color_discrete_sequence=[ORANYE], **kw)
    fig.add_hline(y=cutoff, line_dash="dot", line_color="#555", annotation_text=f"batas {cutoff:.2f}") if jenis != "Histogram" else \
        fig.add_vline(x=cutoff, line_dash="dot", line_color="#555")
    c1.plotly_chart(rapikan(fig, 470, f"IPK: {jenis.lower()}" + (f" menurut {grup}" if gcol else "")), width="stretch", key="ipk_main")

    # QQ-plot manual (tanpa scipy) untuk memeriksa kenormalan
    ys = np.sort(f["IPK"].to_numpy())
    nd = NormalDist()
    teori = [nd.inv_cdf((i - 0.5) / len(ys)) for i in range(1, len(ys) + 1)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=teori, y=ys, mode="markers", marker=dict(color=ORANYE, size=5, opacity=.7), name="IPK"))
    mu, sd = ys.mean(), ys.std(ddof=1) if len(ys) > 1 else 0
    fig.add_trace(go.Scatter(x=[min(teori), max(teori)], y=[mu + sd * min(teori), mu + sd * max(teori)], mode="lines",
                             line=dict(color="#333", dash="dash"), name="Garis normal"))
    fig.update_xaxes(title="Kuantil normal teoretis")
    fig.update_yaxes(title="IPK")
    c2.plotly_chart(rapikan(fig, 470, "QQ-plot: seberapa normal IPK?"), width="stretch", key="ipk_qq")

    s = f["IPK"]
    q1, q3 = s.quantile([.25, .75])
    m = st.columns(6)
    m[0].metric("Mean", f"{s.mean():.2f}")
    m[1].metric("Median", f"{s.median():.2f}")
    m[2].metric("Simpangan baku", f"{s.std():.2f}" if len(s) > 1 else "-")
    m[3].metric("Skewness", f"{s.skew():.2f}" if len(s) > 2 else "-", help="< 0: miring ke kiri (ekor panjang di IPK rendah)")
    m[4].metric("IQR", f"{q3 - q1:.2f}")
    m[5].metric("Pencilan (IQR)", int(((s < q1 - 1.5 * (q3 - q1)) | (s > q3 + 1.5 * (q3 - q1))).sum()))

    p1, p2 = st.columns([1, 1.2])
    pr = f["Predikat"].value_counts().reindex(PREDIKAT, fill_value=0).reset_index()
    pr.columns = ["Predikat", "Jumlah"]
    fig = px.bar(pr, x="Predikat", y="Jumlah", color_discrete_sequence=[ORANYE], text="Jumlah")
    fig.update_traces(textposition="outside", cliponaxis=False)
    p1.plotly_chart(rapikan(fig, 340, "Predikat berdasarkan IPK (ordinal turunan)"), width="stretch", key="ipk_pred")
    p2.markdown("**Statistik deskriptif IPK**")
    p2.dataframe(s.describe(percentiles=[.05, .25, .5, .75, .95]).to_frame("IPK").T.style.format("{:.2f}"), width="stretch")
    p2.caption("Predikat: < 2,00 Perlu Pembinaan, 2,00-2,75 Memuaskan, 2,76-3,50 Sangat Memuaskan, > 3,50 Dengan Pujian.")

# ============================================================================= TAB 5 USIA
with tabs[4]:
    tag("<b>Numerik (Kontinu)</b>: Usia dicatat dalam tahun penuh. Visualisasi yang sesuai: Histogram atau Box plot.", ORANYE)
    a, b = st.columns(2)
    jenis_u = a.radio("Jenis grafik", ["Histogram", "Box plot", "Violin"], horizontal=True, key="usia_jenis")
    grup_u = b.selectbox("Kelompokkan menurut", ["Tidak ada", "Jurusan", "Semester"], key="usia_grup")
    gcol_u = {"Tidak ada": None, "Jurusan": "Jurusan", "Semester": "Semester_Label"}[grup_u]

    c1, c2 = st.columns([1.3, 1])
    if jenis_u == "Histogram":
        fig = px.histogram(f, x="Usia", color=gcol_u, marginal="box", barmode="stack",
                           color_discrete_sequence=px.colors.qualitative.Set2 if gcol_u else [ORANYE],
                           category_orders={"Semester_Label": [str(i) for i in SEM_URUT]})
        fig.update_traces(xbins=dict(start=umin - .5, end=umax + .5, size=1), selector=dict(type="histogram"))
    else:
        fn = px.box if jenis_u == "Box plot" else px.violin
        kw = dict(box=True, points=False) if jenis_u == "Violin" else dict(points="outliers")
        if gcol_u:
            fig = fn(f, x=gcol_u, y="Usia", color_discrete_sequence=[ORANYE], **kw)
            if gcol_u == "Semester_Label":
                sumbu_semester(fig)
                fig.update_xaxes(title="Semester")
        else:
            fig = fn(f, y="Usia", color_discrete_sequence=[ORANYE], **kw)
    c1.plotly_chart(rapikan(fig, 470, f"Usia: {jenis_u.lower()}" + (f" menurut {grup_u}" if gcol_u else "")), width="stretch", key="u_main")

    ru = f.groupby("Semester")["Usia"].agg(["mean", "median", "std", "count"]).reset_index()
    ru["Semester"] = ru["Semester"].astype(str)
    ru["ci"] = 1.96 * ru["std"].fillna(0) / np.sqrt(ru["count"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ru["Semester"], y=ru["mean"], mode="lines+markers", name="Rata-rata (95% CI)", line=dict(color=ORANYE_TUA, width=3),
                             error_y=dict(type="data", array=ru["ci"], visible=True)))
    fig.add_trace(go.Scatter(x=ru["Semester"], y=ru["median"], mode="lines+markers", name="Median", line=dict(color="#777", dash="dash"), marker=dict(symbol="square")))
    fig.update_yaxes(title="Usia (tahun)")
    c2.plotly_chart(sumbu_semester(rapikan(fig, 470, "Usia naik seiring semester")), width="stretch", key="u_line")

    u = f["Usia"]
    q1, q3 = u.quantile([.25, .75])
    m = st.columns(6)
    m[0].metric("Mean", f"{u.mean():.1f}")
    m[1].metric("Median", f"{u.median():.0f}")
    m[2].metric("Modus", f"{u.mode().iloc[0]}")
    m[3].metric("Simpangan baku", f"{u.std():.2f}" if len(u) > 1 else "-")
    m[4].metric("Skewness", f"{u.skew():.2f}" if len(u) > 2 else "-", help="> 0: miring ke kanan (ada mahasiswa dewasa)")
    m[5].metric("Pencilan (IQR)", int((u > q3 + 1.5 * (q3 - q1)).sum()), help="Mahasiswa dengan usia di atas pagar atas.")

# ============================================================================= TAB 6 HUBUNGAN
with tabs[5]:
    tag("<b>Hubungan antar variabel</b>: korelasi Spearman dipakai karena IPK miring dan Semester berskala ordinal.", ORANYE)
    a, b, c = st.columns(3)
    warna = a.selectbox("Warna titik menurut", ["Jurusan", "Semester", "Tidak ada"])
    jitter = b.toggle("Jitter pada usia (hindari titik menumpuk)", value=True)
    garis = c.toggle("Garis tren linear", value=True)

    sc = f.copy()
    rng = np.random.default_rng(1)
    sc["Usia_plot"] = sc["Usia"] + (rng.uniform(-.25, .25, len(sc)) if jitter else 0)
    cmap = {"Jurusan": "Jurusan", "Semester": "Semester_Label", "Tidak ada": None}[warna]
    fig = px.scatter(sc, x="Usia_plot", y="IPK", color=cmap, opacity=.7, hover_data=["Jurusan", "Semester", "Usia"],
                     color_discrete_sequence=px.colors.qualitative.Safe if cmap != "Semester_Label" else px.colors.qualitative.Alphabet,
                     category_orders={"Semester_Label": [str(i) for i in SEM_URUT]}, labels={"Usia_plot": "Usia (tahun)", "Semester_Label": "Semester"})
    if cmap is None:
        fig.update_traces(marker=dict(color=ORANYE))
    if garis and len(f) > 2 and f["Usia"].nunique() > 1:
        kof = np.polyfit(f["Usia"], f["IPK"], 1)
        xs = np.array([f["Usia"].min(), f["Usia"].max()])
        fig.add_trace(go.Scatter(x=xs, y=kof[0] * xs + kof[1], mode="lines", line=dict(color="#C0392B", width=3), name="Tren linear"))
    c1, c2 = st.columns([1.3, 1])
    c1.plotly_chart(rapikan(fig, 470, "IPK vs Usia"), width="stretch", key="h_sc")

    if len(f) > 2:
        cor = f[["IPK", "Usia", "Semester"]].corr(method="spearman")
        fig = px.imshow(cor, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r")
        c2.plotly_chart(rapikan(fig, 470, "Korelasi Spearman"), width="stretch", key="h_cor")
        m = st.columns(3)
        m[0].metric("IPK vs Usia", f"{cor.loc['IPK', 'Usia']:+.2f}")
        m[1].metric("IPK vs Semester", f"{cor.loc['IPK', 'Semester']:+.2f}")
        m[2].metric("Usia vs Semester", f"{cor.loc['Usia', 'Semester']:+.2f}", help="Hubungan kuat: usia bertambah seiring semester.")
    else:
        c2.info("Data terlalu sedikit untuk menghitung korelasi.")

    c3, c4 = st.columns(2)
    pv = f.pivot_table(index="Jurusan", columns="Semester", values="IPK", aggfunc="mean").reindex(columns=SEM_URUT)
    nn = f.pivot_table(index="Jurusan", columns="Semester", values="IPK", aggfunc="count").reindex(columns=SEM_URUT)
    pv = pv.where(nn >= 5).dropna(how="all", axis=1)
    if pv.empty:
        c3.info("Belum ada sel Jurusan x Semester dengan minimal 5 mahasiswa pada filter ini.")
    else:
        fig = px.imshow(pv, text_auto=".2f", color_continuous_scale="YlOrBr", aspect="auto", labels=dict(x="Semester", y="", color="Rata-rata IPK"))
        fig.update_xaxes(type="category")
        c3.plotly_chart(rapikan(fig, 380, "Rata-rata IPK: Jurusan x Semester (sel n >= 5)"), width="stretch", key="h_heat")

    sd = f.groupby("Semester")["IPK"].std().reset_index()
    sd["Semester"] = sd["Semester"].astype(str)
    fig = px.line(sd, x="Semester", y="IPK", markers=True, color_discrete_sequence=[ORANYE_TUA], labels={"IPK": "Simpangan baku IPK"})
    c4.plotly_chart(sumbu_semester(rapikan(fig, 380, "Variasi IPK per Semester")), width="stretch", key="h_sd")

# ============================================================================= TAB 7 DATA
with tabs[6]:
    st.markdown(f"**{id_num(len(f))} mahasiswa** sesuai filter dari {id_num(len(df))} total.")
    st.dataframe(f[KOLOM_WAJIB + ["Predikat"]], hide_index=True, width="stretch",
                 column_config={"IPK": st.column_config.NumberColumn(format="%.2f")})
    st.download_button("Unduh data terfilter (CSV)", f[KOLOM_WAJIB].to_csv(index=False).encode("utf-8"),
                       file_name="data_mahasiswa_terfilter.csv", mime="text/csv")
    st.markdown("**Kamus data dan pilihan visualisasi**")
    st.dataframe(pd.DataFrame({
        "Kolom": ["Jurusan", "Semester", "IPK", "Usia"],
        "Tipe / skala": ["Kategorik - Nominal", "Kategorik - Ordinal", "Numerik - Kontinu", "Numerik - Kontinu"],
        "Contoh": ["Sistem Informasi", "3", "3,85", "20"],
        "Visualisasi": ["Bar / Pie", "Bar chart berurutan", "Histogram / Box plot", "Histogram / Box plot"]}),
        hide_index=True, width="stretch")
