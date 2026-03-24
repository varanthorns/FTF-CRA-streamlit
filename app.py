import streamlit as st
import json, random, pandas as pd, time
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_mic_recorder import mic_recorder

# ===================== 1. CONFIG =====================
st.set_page_config(layout="wide", page_title="ACLR Ultimate Clinical Reasoning")

# ===================== 2. EVALUATION LOGIC =====================
def evaluate_base(dx, reasoning, case, profession):
    """คำนวณคะแนนพื้นฐาน (Dx, Evidence, Logic)"""
    target = case.get("interprofessional_answers", {}).get(profession, case.get("answer", ""))
    
    # 1. Accuracy Score (5 pts)
    try:
        vec = TfidfVectorizer().fit_transform([str(dx).lower(), str(target).lower()])
        sim = cosine_similarity(vec[0:1], vec[1:2])[0][0]
    except: sim = 0
    dx_score = 5 if sim > 0.75 else (3 if sim > 0.45 else 0)
    level = "correct" if sim > 0.75 else ("close" if sim > 0.45 else "wrong")

    # 2. Key Evidence Score (3 pts)
    found_keys = [k for k in case.get("key_points", []) if k.lower() in reasoning.lower()]
    r_score = min(3, len(found_keys))

    # 3. Clinical Logic Score (2 pts)
    logic_words = ["because", "therefore", "thus", "due to", "เนื่องจาก", "ดังนั้น", "ทำให้", "ส่งผล"]
    d_score = 2 if any(w in reasoning.lower() for w in logic_words) else 0

    return dx_score, r_score, d_score, target, found_keys, level

def evaluate_pro(dx, reasoning, case, profession, confidence, selected_ddx):
    """คำนวณคะแนนระดับสูง (Safety + Calibration)"""
    dx_s, r_s, d_s, target, used, level = evaluate_base(dx, reasoning, case, profession)
    total_base = dx_s + r_s + d_s

    # Safety Check
    must_exclude = case.get("must_exclude", [])
    safety_score = 1 if all(item in selected_ddx for item in must_exclude) else -1
    
    # Confidence Bonus/Penalty
    bonus = 0
    if level == "correct" and confidence > 80: bonus = 1 
    elif level == "wrong" and confidence > 90: bonus = -2 

    final_score = max(0, min(10, total_base + safety_score + bonus))
    return final_score, dx_s, r_s, d_s, safety_score, target, used, level

# ===================== 3. DATA LOADING =====================
def safe_case(case):
    case.setdefault("block", "General")
    case.setdefault("difficulty", "easy")
    case.setdefault("must_exclude", [])
    case.setdefault("key_points", [])
    case.setdefault("labs", [])
    case.setdefault("scenario", {"en": "No scenario."})
    case.setdefault("answer", "Unknown")
    case.setdefault("interprofessional_answers", {})
    return case

@st.cache_data
def load_cases():
    try:
        with open("cases.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return [safe_case(c) for c in data]
    except FileNotFoundError:
        return [safe_case({
            "block": "Cardiovascular", "difficulty": "easy",
            "scenario": {"en": "65M with chest pain, ST-elevation V1-V4."},
            "answer": "Anterior Wall MI", "must_exclude": ["PE", "Aortic Dissection"],
            "key_points": ["ST-elevation", "V1-V4"]
        })]

cases = load_cases()

# ===================== 4. SESSION STATE =====================
if "case" not in st.session_state:
    st.session_state.case = cases[0]
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# ===================== 5. SIDEBAR (FILTERS) =====================
with st.sidebar:
    st.title("🧠 ACLR Professional")
    page = st.radio("Navigation", ["📖 User Guide", "🧪 Clinical Simulator", "🏆 Leaderboard"])
    
    st.divider()
    st.subheader("🎯 Station Selection")
    sel_block = st.selectbox("Select Block", ["All"] + list(set(c['block'] for c in cases)))
    sel_diff = st.select_slider("Select Difficulty", options=["easy", "medium", "hard"])
    
    if st.button("🔄 Generate New Case"):
        filtered = [c for c in cases if (sel_block == "All" or c['block'] == sel_block) and (c['difficulty'] == sel_diff)]
        if filtered:
            st.session_state.case = random.choice(filtered)
            st.session_state.submitted = False
            st.session_state.voice_text = ""
            st.rerun()
        else:
            st.warning("No cases found for this criteria!")

    st.divider()
    user_id = st.text_input("👤 User ID", value="Doctor")
    profession = st.selectbox("👩‍⚕️ Your Role", ["medicine", "nursing", "pharmacy", "ams"])

# ===================== 6. MAIN CONTENT =====================

# --- PAGE: USER GUIDE ---
if page == "📖 User Guide":
    st.header("📖 Clinical Reasoning Manual: ACLR Loop")
    st.write("ระบบจำลองการตัดสินใจทางคลินิก (Cognitive Simulator) เพื่อฝึกการวินิจฉัยอย่างเป็นระบบ")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("🛠 Workflow")
        st.markdown("""
        1. **Data Synthesis:** วิเคราะห์ Scenario และ Lab (Tab 1 & 2)
        2. **Must-Exclude DDx:** เลือกโรคอันตรายที่ห้ามพลาด
        3. **Formulation:** อธิบายเหตุผลพยาธิสภาพ (Tab 3)
        4. **Calibration:** ระบุความมั่นใจ (Confidence Score)
        """)
    with col_g2:
        st.subheader("📊 Scoring (10 Points)")
        st.write("- **Dx (5):** ความถูกต้องของโรค")
        st.write("- **Evidence (3):** การดึงจุดสำคัญมาอธิบาย")
        st.write("- **Logic (2):** การใช้คำเชื่อมเหตุและผล")
        st.error("⚠️ หักคะแนน: หากลืม Red Flags หรือมั่นใจผิดที่")

# --- PAGE: SIMULATOR ---
elif page == "🧪 Clinical Simulator":
    case = st.session_state.case
    st.title(f"🏥 Station: {case['block']} | Level: {case['difficulty'].upper()}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        t1, t2, t3 = st.tabs(["📋 Scenario", "🧪 Diagnostics", "✍️ Analysis"])
        with t1:
            st.info(case["scenario"].get("en", ""))
            if case.get("image_url"): st.image(case["image_url"], use_container_width=True)
        with t2:
            if case["labs"]: st.table(pd.DataFrame(case["labs"]))
            else: st.write("No specific labs.")
        with t3:
            st.warning(f"**Task:** วินิจฉัยและอธิบายเหตุผลในบทบาท {profession.upper()}")
            # Voice Recorder
            audio = mic_recorder(start_prompt="🎙️ Record Summary", stop_prompt="Stop", key='recorder')
            if audio: st.session_state.voice_text = f"Input processed: {case['answer']} suspected."
            
            selected_ddx = st.multiselect("🔍 Must-Exclude (Red Flags)", ["MI", "PE", "Aortic Dissection", "Sepsis", "Pneumothorax"])
            dx_in = st.text_input("🩺 Final Diagnosis", value=st.session_state.voice_text)
            re_in = st.text_area("✍️ Pathophysiological Reasoning", placeholder="เหตุผลเพราะว่า...")
            conf_in = st.slider("🎯 Confidence Level (%)", 0, 100, 50)
            
            if st.button("✅ Submit Decision"):
                if dx_in and re_in:
                    st.session_state.submitted = True
                    st.rerun()
                else: st.error("Please fill all fields.")

    if st.session_state.submitted:
        st.divider()
        sc, dx_s, r_s, d_s, s_s, target, used, level = evaluate_pro(dx_in, re_in, case, profession, conf_in, selected_ddx)
        cl, cr = st.columns([2, 1])
        with cl:
            st.subheader(f"📊 Score: {sc}/10")
            st.progress(sc * 10)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Dx", f"{dx_s}/5"); m2.metric("Evidence", f"{r_s}/3")
            m3.metric("Logic", f"{d_s}/2"); m4.metric("Safety", "PASS" if s_s > 0 else "FAIL", delta=s_s)
            st.write(f"**Correct Dx:** `{target}`")
            if s_s < 0: st.error(f"❌ Safety Warning: Missed {', '.join(case['must_exclude'])}")
        with cr:
            st.subheader("👥 Team Feedback")
            for role, ans in case.get("interprofessional_answers", {}).items():
                with st.expander(f"From {role.upper()}"): st.write(ans)

# --- PAGE: LEADERBOARD ---
elif page == "🏆 Leaderboard":
    st.header("🏆 Performance Dashboard")
    st.dataframe(pd.DataFrame({"User": [user_id], "Score": ["-"], "Block": ["-"]}))

st.markdown("---")
st.caption("ACLR Ultimate v3.8 | Simulation-Based Clinical Education 2026")
