import streamlit as st
import matplotlib.pyplot as plt
from utils.analysis import process_kecamatan_data
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib.units import inch

# --------------------------------------------------
# CONFIG & CUSTOM CSS
# --------------------------------------------------
st.set_page_config(
    page_title="Kapten Naratel Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Oswald:wght@400;600&display=swap');
html, body, [class*="css"] { background-color: #000; color: #fff; font-family: 'Oswald', sans-serif; }
h1,h2,h3,h4 { color: #FFD700; font-family:'Bebas Neue',sans-serif; letter-spacing:1px; }
.stSidebar { background-color:#111; width:300px; }
.stButton>button { background: linear-gradient(to right,#FFD700,#FFC300); color:#000; font-weight:bold; border-radius:8px; padding:.5em 1em;}
.card { background:#111; padding:1rem; margin-bottom:1rem; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.5); }
[data-testid="stSidebar"] { position:fixed; top:0; left:0; height:100vh; z-index:1000; }
[data-testid="stAppViewContainer"] > div:nth-child(1) { margin-left:0!important; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
with st.spinner("🔄 Memuat data..."):
    kecamatan_dfs = process_kecamatan_data()

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def get_rekomendasi(row):
    if row["kategori_potensi"] == "🔥 High Potential":
        return ("💡 Perkuat promosi & perluas coverage."
                if row["SOM"] < row["SAM"] * 0.6 else "✅ Performa baik. Pantau terus.")
    else:
        return ("📉 Potensi rendah—fokus promosi lokal."
                if row["homepass"] > 100 and row["SOM"] < 20 else "⚠️ Tidak prioritas. Alihkan sumber daya.")

def plot_market_pie_agg(df):
    total_hp = df["homepass"].sum()
    total_sam = df["SAM"].sum()
    total_som = df["SOM"].sum()
    labels = ["Homepass","SAM","SOM"]
    values = [total_hp, total_sam, total_som]
    colors_pie = ["#6EC1E4","#FFD700","#FF5733"]
    fig, ax = plt.subplots(figsize=(3.5,3.5))
    wedges, _ = ax.pie(values, startangle=140, colors=colors_pie)
    ax.axis("equal")
    total = sum(values)
    legend = [f"{l}: {v} ({v/total*100:.1f}%)" for l,v in zip(labels,values)]
    ax.legend(wedges, legend, loc="center left", bbox_to_anchor=(1,0.5), fontsize=8)
    return fig

def create_pdf_report_kecamatan(kecamatan, df):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=40, rightMargin=40,
                            topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    elems = []

    # Title and subtitle
    elems.append(Paragraph("Kapten Naratel – Laporan Pasar Homepass", styles['Title']))
    elems.append(Paragraph(f"Kecamatan {kecamatan.title()}", styles['Heading2']))
    elems.append(Spacer(1, 12))

    # Intro
    intro = (
        "Berikut adalah ringkasan potensi pasar Homepass untuk semua kelurahan "
        f"di Kecamatan <b>{kecamatan.title()}</b>. Termasuk total Homepass, SAM, dan SOM."
    )
    elems.append(Paragraph(intro, styles['BodyText']))
    elems.append(Spacer(1, 12))

    # Table summary
    table_data = [["Kelurahan", "Homepass", "SAM", "SOM", "Kategori"]]
    for _, row in df.iterrows():
        table_data.append([
            row["kelurahan"],
            row["homepass"],
            row["SAM"],
            row["SOM"],
            row["kategori_potensi"]
        ])
    tbl = Table(table_data, colWidths=[100, 60, 60, 60, 120])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FFD700")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke, colors.lightgrey]),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 12))

    # Bar chart SOM per kelurahan
    buf_bar = io.BytesIO()
    colors_bar = df["kategori_potensi"].apply(
        lambda x: "#FFD700" if "High" in x else "#808080")
    fig2, ax2 = plt.subplots(figsize=(6,3))
    ax2.bar(df["kelurahan"], df["SOM"], color=colors_bar)
    ax2.set_title("SOM per Kelurahan")
    ax2.set_ylabel("Jumlah SOM")
    plt.xticks(rotation=45, ha="right", fontsize=7)
    plt.tight_layout()
    fig2.savefig(buf_bar, format="PNG", bbox_inches="tight")
    plt.close(fig2)
    buf_bar.seek(0)
    elems.append(Image(buf_bar, width=6*inch, height=3*inch))
    elems.append(Spacer(1, 12))

    # Note: pie chart has been removed as requested

    doc.build(elems)
    buf.seek(0)
    return buf

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
st.sidebar.title("🏡 Kapten Naratel")
page = st.sidebar.radio("Pilih Halaman", ["Homepage", "Analisis Pasar"])

# --------------------------------------------------
# HOMEPAGE
# --------------------------------------------------
if page == "Homepage":
    st.title("🏠 Beranda – Kapten Naratel")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Apa itu TAM, SAM, dan SOM?")
    st.markdown("""
    - **TAM**: Total Addressable Market  
    - **SAM**: Serviceable Available Market  
    - **SOM**: Serviceable Obtainable Market  
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Panduan Penggunaan")
    st.markdown("""
    1. Pilih **Analisis Pasar** di sidebar  
    2. Pilih Kecamatan & Kelurahan  
    3. Lihat statistik, grafik & rekomendasi  
    4. Unduh laporan PDF  
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Keunggulan")
    st.markdown("""
    - Visual interaktif & rekomendasi otomatis  
    - Desain gelap modern  
    - PDF ringkasan per kecamatan  
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# ANALISIS PASAR
# --------------------------------------------------
else:
    st.title("📍 Analisis Pasar Homepass Kapten Naratel")
    sel_kec = st.selectbox("Pilih Kecamatan:", sorted(kecamatan_dfs.keys()))
    df_kec = kecamatan_dfs[sel_kec]

    sel_kel = st.selectbox("Pilih Kelurahan:", df_kec["kelurahan"])
    data_kel = df_kec[df_kec["kelurahan"] == sel_kel].iloc[0]

    st.subheader(f"📊 Statistik {sel_kel.title()}")
    c1, c2, c3 = st.columns(3)
    c1.metric("🏘️ Homepass", data_kel["homepass"])
    c2.metric("🧮 ODP", data_kel["ODP"])
    c3.metric("💰 SOM", data_kel["SOM"])
    st.info(f"**Kategori:** {data_kel['kategori_potensi']}")
    st.markdown(f"**🧠 Rekomendasi:** {get_rekomendasi(data_kel)}")

    with st.expander("📋 Tabel Semua Kelurahan"):
        st.dataframe(df_kec, use_container_width=True)

    st.subheader("📈 Visualisasi")
    left, right = st.columns(2)
    with left:
        st.markdown("#### 🥧 Distribusi Pasar (Kelurahan)")
        st.pyplot(plot_market_pie_agg(df_kec))
    with right:
        st.markdown("#### 📶 SOM per Kelurahan")
        colors_bar = df_kec["kategori_potensi"].apply(
            lambda x: "#FFD700" if "High" in x else "#808080"
        )
        fig, ax = plt.subplots(figsize=(6,3))
        ax.bar(df_kec["kelurahan"], df_kec["SOM"], color=colors_bar)
        ax.set_xticklabels(df_kec["kelurahan"], rotation=45, ha="right", fontsize=8)
        st.pyplot(fig)

    # Download PDF per kecamatan
    st.subheader("📑 Unduh Laporan Kecamatan")
    pdf_buf = create_pdf_report_kecamatan(sel_kec, df_kec)
    st.download_button(
        "📥 Download PDF Kecamatan",
        data=pdf_buf,
        file_name=f"laporan_{sel_kec}.pdf",
        mime="application/pdf"
    )
