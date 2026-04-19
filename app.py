import streamlit as st
import json, random, pandas as pd, os, time
import google.generativeai as genai

# ===================== ⚙️ 1. GLOBAL CONFIG & UI SETUP =====================
# ต้องอยู่บรรทัดแรกสุดของไฟล์ ห้ามมี st อื่นก่อนหน้านี้
st.set_page_config(layout="wide", page_title="FTF-CRA Clinical Platform", page_icon="🩺")

DB_FILE = "clinical_scores.csv"

# 🔐 1.1 API Setup - ปิดก้อน try/except ให้จบในตัวทันที
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    else:
        GEMINI_API_KEY = "DEMO_KEY"
except Exception:
    GEMINI_API_KEY = "DEMO_KEY"

genai.configure(api_key=GEMINI_API_KEY)

# 💾 1.2 Database & Logic Functions
def save_score_local(user, role, score, block, competency=None, time_taken=0):
    new_entry = {
        "User": user, "Role": role, "Score": score, "Block": block,
        "Time": time_taken, "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if competency:
        new_entry.update(competency)
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

def get_ai_feedback_v9_5(user_dx, user_re, user_map, target, role, time_taken, confidence, stress):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Evaluate this {role}: Dx={user_dx}, Rationale={user_re}, Map={user_map}, Answer={target}, Time={time_taken}s."
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "🚨 AI Mentor Offline"

# ===================== 🎨 2. UI STYLING =====================
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1976D2 !important; color: white !important; font-weight: bold; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; border-left: 5px solid #1976D2; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stress-timer { font-size: 28px; font-weight: bold; color: #d32f2f; text-align: center; border: 3px solid #d32f2f; padding: 10px; border-radius: 15px; background: white; }
    </style>
    """, unsafe_allow_html=True)

# 🔄 Session State Init
if "submitted" not in st.session_state: st.session_state.submitted = False
if "ai_feedback" not in st.session_state: st.session_state.ai_feedback = ""
if "start_time" not in st.session_state: st.session_state.start_time = time.time()

# ===================== 🧭 3. SIDEBAR =====================
with st.sidebar:
    st.title("🩺 FTF-CRA v9.9.5")
    menu = st.radio("Main Menu", ["📖 Manual & Standards", "🧪 Clinical Simulator", "🏆 Analytics Hub"])
    st.divider()
    user_name = st.text_input("👤 Practitioner Name", "User_01")
    profession = st.selectbox("👩‍⚕️ Clinical Role", ["Doctor", "Pharmacy", "Nursing", "AMS", "Dentistry", "Vet"]).lower()
    
    adaptive_mode = st.checkbox("🧠 AI Adaptive Mode", value=False)
    f_diff = get_adaptive_difficulty(user_name) if adaptive_mode else st.select_slider("Set Difficulty", options=["easy", "medium", "hard"], value="medium")

# ===================== 🚥 4. PAGE ROUTING =====================

# --- 📖 MANUAL PAGE ---
if menu == "📖 Manual & Standards":
    st.header("📖 Clinical Operations Guide")
    st.info("System Philosophy: Adaptive Cognitive Load–Driven AI Loop")
    st.write("Welcome to the clinical reasoning platform. Follow the steps in the Simulator to begin.")

# --- 🧪 SIMULATOR PAGE ---
elif menu == "🧪 Clinical Simulator":
    st.header("🧪 Clinical Simulator")
    elapsed = int(time.time() - st.session_state.start_time)
    
    st.markdown(f"<div class='stress-timer'>⏳ Time Elapsed: {elapsed}s</div>", unsafe_allow_html=True)
    
    dx_in = st.text_input("🩺 Your Diagnosis")
    re_in = st.text_area("✍️ Pathophysiological Rationale")
    
    if st.button("🚀 SUBMIT DECISION"):
        if dx_in and re_in:
            with st.spinner("AI Evaluating..."):
                st.session_state.ai_feedback = get_ai_feedback_v9_5(dx_in, re_in, "None", "STEMI", profession, elapsed, 100, 5)
                st.session_state.submitted = True
                save_score_local(user_name, profession, 10, "Cardiology", time_taken=elapsed)
                st.rerun()

    if st.session_state.submitted:
        st.subheader("👨‍🏫 AI Mentor Feedback")
        st.markdown(st.session_state.ai_feedback)
        if st.button("🔄 Reset Case"):
            st.session_state.submitted = False
            st.session_state.start_time = time.time()
            st.rerun()

# --- 🏆 ANALYTICS PAGE ---
elif menu == "🏆 Analytics Hub":
    st.header("🏆 Performance Analytics Dashboard")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Sims", len(df))
            c2.metric("Mean Score", f"{df['Score'].mean():.1f}/10")
            c3.metric("Avg Speed", f"{df['Time'].mean():.0f}s")
            st.line_chart(df.set_index("Timestamp")["Score"])
        else: st.warning("No simulation data yet.")
    else: st.info("Database not found. Start a simulation first!")

st.markdown("---")
st.caption("FTF-CRA Global v9.9.5 | © 2026")
