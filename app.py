import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# KONFIGURASI & CSS
# ==========================================
st.set_page_config(page_title="AI Literacy Assessment", layout="centered", page_icon="🤖")

# Injeksi CSS (Diadaptasi dari versi Shiny)
st.markdown("""
<style>
    /* Mengubah background utama */
    .stApp { background: linear-gradient(135deg, #fff7fb 0%, #eef7ff 48%, #f4fff8 100%); }
    
    /* Style Komponen Custom */
    .hero {
        background: rgba(255,255,255,0.90); border: 1px solid rgba(214,204,236,0.90);
        border-radius: 30px; padding: 30px 34px; margin-bottom: 22px;
        box-shadow: 0 18px 45px rgba(155,142,183,0.18); text-align: center;
    }
    .hero h1 { color: #6f5c8d; font-weight: 800; margin-bottom: 0; padding-bottom: 0; }
    .hero p { color: #6b6880; font-size: 16px; margin-top: 5px; }
    
    .chip {
        display: inline-block; padding: 8px 15px; border-radius: 999px;
        background: #ede7ff; color: #68578d; font-weight: 800; margin-bottom: 12px;
    }
    .note {
        background: #f6efff; border-left: 6px solid #c8b6ff; border-radius: 16px;
        padding: 14px 16px; margin: 12px 0 18px 0; color: #625b72;
    }
    
    /* Score Grid & Box */
    .score-grid { display: flex; gap: 16px; margin: 18px 0; flex-wrap: wrap; }
    .score-box {
        flex: 1; background: #ffffff; border: 1px solid #eee6ff; border-radius: 22px;
        padding: 20px; text-align: center; box-shadow: 0 8px 20px rgba(155,142,183,0.10); min-width: 150px;
    }
    .score-box .num { font-size: 34px; font-weight: 900; color: #6f5c8d; }
    .score-box .label { color: #6b6880; font-weight: 700; font-size: 14px;}
    .score-box .sub { color: #8a839c; font-size: 12px; margin-top: 6px; }
    
    .mini-cat { display: inline-block; border-radius: 999px; padding: 5px 11px; font-size: 12px; font-weight: 800; }
    .cat-low { background: #ffd6e0; color: #703045; }
    .cat-mid { background: #fff0b3; color: #6b5720; }
    .cat-high { background: #c8f7dc; color: #24563c; }
    
    /* Bar Chart Custom */
    .bar-card {
        background: #ffffff; border: 1px solid #eee6ff; border-radius: 20px;
        padding: 16px; margin: 12px 0; box-shadow: 0 8px 20px rgba(155,142,183,0.08);
    }
    .bar-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .bar-label { font-weight: 900; color: #5e527d; }
    .bar-shell { background: #f0ebff; border-radius: 999px; height: 14px; overflow: hidden; }
    .bar-fill { background: linear-gradient(90deg, #ffc8dd, #b8c0ff, #bde0fe); height: 100%; border-radius: 999px; }
    .bar-note { color: #6b6880; font-size: 13px; margin-top: 8px; }
    
    /* Hembusan Rapi untuk radio button bawaan Streamlit */
    div.stRadio > div { background: white; padding: 10px 15px; border-radius: 16px; border: 1px solid #eee6ff; box-shadow: 0 5px 15px rgba(155,142,183,0.08);}
</style>
""", unsafe_allow_html=True)

# ==========================================
# FUNGSI HELPER TEKS & LOGIKA
# ==========================================
def category_label(score):
    if score < 60: return "Rendah"
    if score < 80: return "Sedang"
    return "Tinggi"

def category_class(label):
    if label == "Rendah": return "cat-low"
    if label == "Sedang": return "cat-mid"
    return "cat-high"

def score_level_text(score):
    if score < 60: return "Perlu penguatan"
    if score < 80: return "Cukup berkembang"
    return "Sangat baik"

def score_attitude_item(value, polarity):
    v = int(value)
    p = str(polarity).strip().lower()
    if p in ["-", "negative", "negatif", "minus"]:
        return 5 - v
    return v

# --- Fungsi Teks Laporan (Sama persis dengan versi R) ---
def profile_total(score):
    if score < 60: return "Profil siswa menunjukkan kategori Pengguna Dasar. Siswa sudah mengenal AI secara umum, tetapi masih memerlukan pendampingan."
    if score < 80: return "Profil siswa menunjukkan kategori Pengguna Fungsional. Siswa sudah dapat menggunakan AI untuk mendukung kegiatan belajar, namun perlu peningkatan verifikasi."
    return "Profil siswa menunjukkan kategori Pengguna Terampil. Siswa sudah memiliki pemahaman dan sikap yang baik dalam menggunakan AI secara kritis dan etis."

def recommend_cognitive(score):
    if score < 60: return "Kemampuan kognitif perlu diperkuat. Disarankan mempelajari kembali konsep dasar AI, bias algoritma, dan halusinasi informasi."
    if score < 80: return "Kemampuan kognitif cukup baik. Perlu lebih banyak latihan menganalisis output AI dan memeriksa sumber primer."
    return "Kemampuan kognitif baik. Siswa mampu memahami logika kerja AI dan mengidentifikasi potensi bias."

def recommend_affective(score):
    if score < 60: return "Sikap penggunaan AI perlu diarahkan agar tidak menyalin mentah-mentah, menjaga privasi data, dan tidak bergantung penuh pada mesin."
    if score < 80: return "Sikap penggunaan AI cukup baik. Perlu lebih konsisten melakukan cross-check dan reflektif."
    return "Sikap penggunaan AI baik. Siswa menunjukkan kecenderungan kritis dan bertanggung jawab."

# ==========================================
# MEMUAT DATA
# ==========================================
@st.cache_data
def load_data():
    os.makedirs("data", exist_ok=True)
    # Dummy data creator jika file tidak ada (agar aplikasi langsung jalan saat pertama dites)
    if not os.path.exists("data/soal_kognitif.csv"):
        pd.DataFrame([
            {"no_soal": 1, "soal": "Apa kepanjangan dari AI?", "A": "Artificial Intelligence", "B": "Auto Internet", "C": "Art Intel", "D": "Anon Info", "E": "Alien Intel", "kunci": "A", "gambar": ""},
            {"no_soal": 2, "soal": "Kelemahan utama Generative AI (seperti ChatGPT) adalah?", "A": "Terlalu cepat", "B": "Sering berhalusinasi (fakta palsu)", "C": "Membuat kopi", "D": "Bisa terbang", "E": "Tidak butuh listrik", "kunci": "B", "gambar": ""}
        ]).to_csv("data/soal_kognitif.csv", index=False)
        pd.DataFrame([
            {"no_butir": 1, "pernyataan": "Saya selalu memverifikasi ulang jawaban dari AI.", "sifat": "positif"},
            {"no_butir": 2, "pernyataan": "Saya menyalin (copy-paste) seluruh tugas saya dari ChatGPT tanpa membaca.", "sifat": "negatif"}
        ]).to_csv("data/soal_sikap.csv", index=False)

    df_cog = pd.read_csv("data/soal_kognitif.csv", dtype=str).fillna("")
    df_aff = pd.read_csv("data/soal_sikap.csv", dtype=str).fillna("")
    return df_cog, df_aff

cog, aff = load_data()

# ==========================================
# MANAJEMEN STATE (SESI)
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "identity"
    st.session_state.cog_idx = 0
    st.session_state.aff_idx = 0
    st.session_state.answers_cog = {}
    st.session_state.answers_aff = {}
    st.session_state.identity = {}
    st.session_state.result = None

# ==========================================
# KOMPONEN UI UTAMA
# ==========================================
st.markdown('<div class="hero"><h1>AI Literacy Assessment</h1><p>Instrumen penilaian literasi AI siswa berbasis tes kognitif dan angket sikap.</p></div>', unsafe_allow_html=True)

# ------------------------------------------
# HALAMAN 1: IDENTITAS
# ------------------------------------------
if st.session_state.page == "identity":
    st.markdown('<span class="chip">Identitas Siswa</span>', unsafe_allow_html=True)
    st.markdown("### Isi identitas sebelum memulai asesmen")
    st.markdown('<div class="note">Data identitas digunakan untuk menyimpan hasil asesmen siswa.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    nama = col1.text_input("Nama lengkap", value=st.session_state.identity.get("nama", ""))
    absen = col2.text_input("Nomor Absen", value=st.session_state.identity.get("nomor_absen", ""))
    
    col3, col4, col5 = st.columns([2, 1, 1])
    sekolah = col3.text_input("Sekolah", value=st.session_state.identity.get("sekolah", ""))
    kelas = col4.text_input("Kelas", value=st.session_state.identity.get("kelas", ""))
    jk = col5.selectbox("Jenis kelamin", ["", "Perempuan", "Laki-laki"], 
                        index=["", "Perempuan", "Laki-laki"].index(st.session_state.identity.get("jenis_kelamin", "")) if st.session_state.identity.get("jenis_kelamin", "") != "" else 0)
    
    if st.button("Mulai Bagian A", type="primary"):
        if not nama or not absen or not sekolah or not kelas:
            st.error("Semua kolom identitas wajib diisi!")
        else:
            st.session_state.identity = {"nama": nama, "nomor_absen": absen, "sekolah": sekolah, "kelas": kelas, "jenis_kelamin": jk}
            st.session_state.page = "cognitive"
            st.rerun()

# ------------------------------------------
# HALAMAN 2: TES KOGNITIF
# ------------------------------------------
elif st.session_state.page == "cognitive":
    st.markdown('<span class="chip">Bagian A - Tes Kognitif</span>', unsafe_allow_html=True)
    idx = st.session_state.cog_idx
    row = cog.iloc[idx]
    
    st.progress((idx) / len(cog), text=f"Progres: Soal {idx + 1} dari {len(cog)}")
    st.markdown('<div class="note">Pilih satu jawaban yang paling tepat.</div>', unsafe_allow_html=True)
    
    # Menampilkan Gambar jika ada
    if row.get("gambar", "") != "":
        img_path = os.path.join("img", row["gambar"])
        if os.path.exists(img_path): st.image(img_path, use_column_width=True)
    
    st.markdown(f"**{row['soal']}**")
    
    choices = [f"A. {row['A']}", f"B. {row['B']}", f"C. {row['C']}", f"D. {row['D']}", f"E. {row['E']}"]
    # Menentukan default selection
    prev_ans = st.session_state.answers_cog.get(idx, None)
    default_idx = [c.startswith(prev_ans) for c in choices].index(True) if prev_ans else None
    
    ans = st.radio("Pilihan:", choices, index=default_idx, label_visibility="collapsed")
    
    col_b, col_n = st.columns([1, 4])
    if col_b.button("⬅ Kembali"):
        if idx > 0: st.session_state.cog_idx -= 1
        else: st.session_state.page = "identity"
        st.rerun()
        
    btn_label = "Lanjut ➡" if idx < len(cog) - 1 else "Lanjut ke Bagian B ➡"
    if col_n.button(btn_label, type="primary"):
        if ans is None:
            st.error("Pilih salah satu jawaban terlebih dahulu.")
        else:
            st.session_state.answers_cog[idx] = ans[0] # Ambil huruf A, B, C, D, E
            if idx < len(cog) - 1: st.session_state.cog_idx += 1
            else: st.session_state.page = "affective"
            st.rerun()

# ------------------------------------------
# HALAMAN 3: ANGKET SIKAP
# ------------------------------------------
elif st.session_state.page == "affective":
    st.markdown('<span class="chip">Bagian B - Angket Sikap</span>', unsafe_allow_html=True)
    idx = st.session_state.aff_idx
    row = aff.iloc[idx]
    
    st.progress((idx) / len(aff), text=f"Progres: Pernyataan {idx + 1} dari {len(aff)}")
    st.markdown('<div class="note">Pilih respons yang paling sesuai dengan diri Anda.</div>', unsafe_allow_html=True)
    
    st.markdown(f"**{row['pernyataan']}**")
    
    likert = {"Sangat Tidak Setuju": 1, "Tidak Setuju": 2, "Setuju": 3, "Sangat Setuju": 4}
    prev_ans = st.session_state.answers_aff.get(idx, None)
    default_idx = list(likert.values()).index(prev_ans) if prev_ans else None
    
    ans = st.radio("Pilihan:", list(likert.keys()), index=default_idx, label_visibility="collapsed")
    
    col_b, col_n = st.columns([1, 4])
    if col_b.button("⬅ Kembali"):
        if idx > 0: st.session_state.aff_idx -= 1
        else: st.session_state.page = "cognitive"
        st.rerun()
        
    btn_label = "Submit & Lihat Hasil ✅" if idx == len(aff) - 1 else "Lanjut ➡"
    if col_n.button(btn_label, type="primary"):
        if ans is None:
            st.error("Pilih respons terlebih dahulu.")
        else:
            st.session_state.answers_aff[idx] = likert[ans]
            if idx < len(aff) - 1: 
                st.session_state.aff_idx += 1
                st.rerun()
            else:
                # ===============================
                # KALKULASI HASIL (SUBMIT)
                # ===============================
                # Kalkulasi Kognitif
                cog_correct = sum([1 for i in range(len(cog)) if st.session_state.answers_cog.get(i) == str(cog.iloc[i]['kunci']).strip().upper()])
                cog_score = round(cog_correct / len(cog) * 100, 2)
                
                # Kalkulasi Afektif
                aff_sum = sum([score_attitude_item(st.session_state.answers_aff[i], str(aff.iloc[i]['sifat'])) for i in range(len(aff))])
                aff_score = round(((aff_sum - len(aff)) / (len(aff) * 3)) * 100, 2)
                aff_score = max(0, min(100, aff_score))
                
                total_score = round((cog_score + aff_score) / 2, 2)
                
                res = st.session_state.identity.copy()
                res.update({
                    "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "skor_kognitif": cog_score, "benar_kognitif": cog_correct,
                    "skor_sikap": aff_score, "skor_total": total_score,
                    "kategori": category_label(total_score)
                })
                
                # Tambahkan jawaban individual untuk disimpan
                for i in range(len(cog)): res[f"jawaban_cog_{i+1}"] = st.session_state.answers_cog.get(i)
                for i in range(len(aff)): res[f"jawaban_aff_{i+1}"] = st.session_state.answers_aff.get(i)
                
                # Simpan ke CSV
                df_res = pd.DataFrame([res])
                output_path = "data/hasil_ai_literacy.csv"
                df_res.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
                
                st.session_state.result = res
                st.session_state.page = "result"
                st.rerun()

# ------------------------------------------
# HALAMAN 4: HASIL (RESULT)
# ------------------------------------------
elif st.session_state.page == "result":
    res = st.session_state.result
    st.markdown('<span class="chip">Hasil Akhir</span>', unsafe_allow_html=True)
    st.markdown(f"## Laporan Individual AI Literacy - {res['nama']}")
    st.write(f"Nomor absen: {res['nomor_absen']} | Kelas: {res['kelas']} | Sekolah: {res['sekolah']}")
    
    st.markdown(f'<div class="mini-cat {category_class(res["kategori"])}" style="font-size:16px; padding:8px 16px;">Kategori Umum: {res["kategori"]}</div>', unsafe_allow_html=True)
    
    # Menampilkan 3 Kotak Skor
    st.markdown(f"""
    <div class="score-grid">
        <div class="score-box">
            <div class="num">{res['skor_total']}</div>
            <div class="label">Skor Total AI Literacy</div>
            <div class="sub">Gabungan kognitif dan sikap</div>
        </div>
        <div class="score-box">
            <div class="num">{res['skor_kognitif']}</div>
            <div class="label">Skor Kognitif</div>
            <div class="sub">{res['benar_kognitif']} benar dari {len(cog)} soal</div>
        </div>
        <div class="score-box">
            <div class="num">{res['skor_sikap']}</div>
            <div class="label">Skor Sikap (Afektif)</div>
            <div class="sub">Ditransformasi skala 0-100</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Fungsi Cetak Bar UI HTML
    def render_bar(label, score):
        cat = category_label(score)
        st.markdown(f"""
        <div class="bar-card">
            <div class="bar-head">
                <span class="bar-label">{label}</span>
                <span class="mini-cat {category_class(cat)}">{cat}</span>
            </div>
            <div class="bar-shell"><div class="bar-fill" style="width:{max(0, min(100, score))}%;"></div></div>
            <div class="bar-note">{score:.2f} dari 100 - {score_level_text(score)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("### Ringkasan Skor")
    render_bar("Skor Total AI Literacy", res['skor_total'])
    render_bar("Aspek Kognitif", res['skor_kognitif'])
    render_bar("Aspek Sikap", res['skor_sikap'])
    
    st.markdown("### Profil Kemampuan")
    st.info(f"**Interpretasi umum:**\n\n{profile_total(res['skor_total'])}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"**Kognitif:**\n\n{recommend_cognitive(res['skor_kognitif'])}")
    with col2:
        st.warning(f"**Sikap:**\n\n{recommend_affective(res['skor_sikap'])}")
    
    st.divider()
    col_d, col_r = st.columns([2,1])
    
    csv_data = pd.DataFrame([res]).to_csv(index=False).encode('utf-8')
    col_d.download_button(
        label="📥 Unduh Hasil Pribadi (CSV)",
        data=csv_data,
        file_name=f"hasil_{res['nama']}_{datetime.now().strftime('%Y%m%d%H%M')}.csv",
        mime="text/csv"
    )
    
    if col_r.button("🔄 Mulai Ulang (Siswa Lain)"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()