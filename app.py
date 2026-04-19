import streamlit as st
import json, random, pandas as pd, os, time
import google.generativeai as genai

# ===================== ⚙️ 1. SETUP & CONFIG =====================
st.set_page_config(layout="wide", page_title="FTF-CRA Clinical Platform", page_icon="🩺")

DB_FILE = "clinical_scores.csv"

# 🔐 API Setup - ปิดจบในก้อนเดียว ห้ามมี elif มาแทรกตรงนี้
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    else:
        GEMINI_API_KEY = "DEMO_KEY"
except Exception:
    GEMINI_API_KEY = "DEMO_KEY"

genai.configure(api_key=GEMINI_API_KEY)

# 💾 Database Functions
def save_score_local(user, role, score, block, competency=None, time_taken=0):
    new_entry = {
        "User": user, "Role": role, "Score": score, "Block": block,
        "Time": time_taken, "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if competency: new_entry.update(competency)
    df_new = pd.DataFrame([new_entry])
    if os.path.exists(DB_FILE):
        df_old = pd.read_csv(DB_FILE)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(DB_FILE, index=False)

def get_adaptive_difficulty(user):
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        user_df = df[df["User"] == user]
        if len(user_df) >= 3:
            avg = user_df["Score"].mean()
            if avg < 6: return "easy"
            elif avg < 8: return "medium"
            else: return "hard"
    return "easy"

# ===================== 🎨 2. UI & SIDEBAR =====================
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1976D2 !important; color: white !important; font-weight: bold; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; border-left: 5px solid #1976D2; }
    .stress-timer { font-size: 28px; font-weight: bold; color: #d32f2f; text-align: center; border: 3px solid #d32f2f; padding: 10px; border-radius: 15px; background: white; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("🩺 FTF-CRA v9.9.5")
    # ตัวแปร menu ต้องประกาศตรงนี้เท่านั้น!
    menu = st.radio("Main Menu", ["📖 Manual & Standards", "🧪 Clinical Simulator", "🏆 Analytics Hub"])
    st.divider()
    user_name = st.text_input("👤 Name", "User_01")
    profession = st.selectbox("👩‍⚕️ Role", ["Doctor", "Pharmacy", "Nursing", "AMS", "Dentistry", "Vet"]).lower()
    
    adaptive_mode = st.checkbox("🧠 Adaptive Mode", value=False)
    f_diff = get_adaptive_difficulty(user_name) if adaptive_mode else st.select_slider("Difficulty", options=["easy", "medium", "hard"], value="medium")

# ===================== 🚥 3. PAGE ROUTING (The Clean Fix) =====================

# 🏆 หน้า 1: Analytics (ใช้ if ตัวแรกเสมอ)
if menu == "🏆 Analytics Hub":
    st.header("🏆 Performance Analytics Dashboard")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Sims", len(df))
            c2.metric("Mean Score", f"{df['Score'].mean():.1f}")
            c3.metric("Avg Speed", f"{df['Time'].mean():.0f}s")
            st.line_chart(df.set_index("Timestamp")["Score"])
        else:
            st.warning("No data found.")
    else:
        st.info("No database found.")

# 📖 หน้า 2: Manual
elif menu == "📖 Manual & Standards":
    st.header("📖 Clinical Operations Guide")
    st.info("System Philosophy: Adaptive Cognitive Load–Driven AI Loop")
    st.markdown("### 🚀 Workflow: Calibration -> Synthesis -> Execution")

# 🧪 หน้า 3: Simulator
elif menu == "🧪 Clinical Simulator":
    st.header("🧪 Clinical Simulator")
    if "start_time" not in st.session_state: st.session_state.start_time = time.time()
    elapsed = int(time.time() - st.session_state.start_time)
    
    st.markdown(f"<div class='stress-timer'>⏳ Time: {elapsed}s</div>", unsafe_allow_html=True)
    
    # ตัวอย่างช่องกรอก
    dx_in = st.text_input("🩺 Assessment")
    if st.button("🚀 SUBMIT"):
        st.success("Decision Submitted! (Add your simulator logic here)")
        save_score_local(user_name, profession, 10, "General", time_taken=elapsed)

st.divider()
st.caption("FTF-CRA Global | © 2026")
