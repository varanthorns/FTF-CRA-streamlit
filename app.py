import streamlit as st
import json, random, pandas as pd, time
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_mic_recorder import mic_recorder

# ===================== 1. CONFIG =====================
st.set_page_config(layout="wide", page_title="ACLR Ultimate Clinical Reasoning", page_icon="🧠")

# ===================== 2. EVALUATION LOGIC =====================
def evaluate_pro(dx, reasoning, plan, case, profession, confidence, selected_ddx):
    """ระบบประเมินผลครอบคลุม Dx, Reasoning, และ Management Plan"""
    target_dx = case.get("interprofessional_answers", {}).get(profession, case.get("answer", ""))
    
    # 1. Dx Accuracy (4 pts)
    try:
        vec = TfidfVectorizer().fit_transform([str(dx).lower(), str(target_dx).lower()])
        sim = cosine_similarity(vec[0:1], vec[1:2])[0][0]
    except: sim = 0
    dx_score = 4 if sim > 0.75 else (2 if sim > 0.45 else 0)
    level = "correct" if sim > 0.75 else ("close" if sim > 0.45 else "wrong")

    # 2. Reasoning & Logic (3 pts)
    found_keys = [k for k in case.get("key_points", []) if k.lower() in reasoning.lower()]
    logic_words = ["เพราะ", "เนื่องจาก", "ทำให้", "ส่งผล", "because", "due to", "result in"]
    r_score = min(2, len(found_keys)) + (1 if any(w in reasoning.lower() for w in logic_words) else 0)

    # 3. Management Plan Accuracy (2 pts)
    # ตรวจสอบว่า Next Step และ Disposition สอดคล้องกับเคสหรือไม่
    plan_score = 0
    if plan['step'] == case.get("next_step_correct", "Consult Specialist"): plan_score += 1
    if plan['dispo'] == case.get("dispo_correct", "Admit General Ward"): plan_score += 1

    # 4. Safety & Confidence (1 pt + Bonus/Penalty)
    must_exclude = case.get("must_exclude", [])
    safety_check = 1 if all(item in selected_ddx for item in must_exclude) else -1
    
    # Penalty: วินิจฉัยผิดแต่ส่งกลับบ้าน หรือ มั่นใจผิดที่
    penalty = 0
    if level == "wrong" and plan['dispo'] == "Discharge Home": penalty -= 2
    if level == "wrong" and confidence > 90: penalty -= 1

    final_score = max(0, min(10, dx_score + r_score + plan_score + safety_check + penalty))
    return final_score, dx_score, r_score, plan_score, safety_check, target_dx, found_keys, level

# ===================== 3. DATA LOADING =====================
def safe_case(case):
    case.setdefault("block", "General")
    case.setdefault("difficulty", "easy")
    case.setdefault("must_exclude", ["Aortic Dissection"])
    case.setdefault("key_points", ["chest pain"])
    case.setdefault("labs", [])
    case.setdefault("scenario", {"en": "62M with acute chest pain, ST-elevation."})
    case.setdefault("answer", "Inferior Wall MI")
    case.setdefault("next_step_correct", "Emergency Procedure")
    case.setdefault("dispo_correct", "Admit ICU/CCU")
    case.setdefault("interprofessional_answers", {"medicine": "PCI", "nursing": "EKG Monitor", "pharmacy": "Aspirin"})
    return case

@st.cache_data
def load_cases():
    try:
        with open("cases.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return [safe_case(c) for c in data]
    except FileNotFoundError:
        return [safe_case({})]

cases = load_cases()

# ===================== 4. SESSION STATE =====================
if "case" not in st.session_state: st.session_state.case = cases[0]
if "submitted" not in st.session_state: st.session_state.submitted = False
if "voice_text" not in st.session_state: st.session_state.voice_text = ""
if "user_plan" not in st.session_state: st.session_state.user_plan = {}

# ===================== 5. SIDEBAR =====================
with st.sidebar:
    st.title("🧠 ACLR Professional")
    page = st.radio("Navigation", ["📖 User Guide", "🧪 Clinical Simulator", "🏆 Leaderboard"])
    st.divider()
    
    if page == "🧪 Clinical Simulator":
        st.subheader("🎯 Station Control")
        sel_block = st.selectbox("Select Block", ["All"] + sorted(list(set(c['block'] for c in cases))))
        sel_diff = st.select_slider("Select Difficulty", options=["easy", "medium", "hard"])
        if st.button("🔄 Generate New Case"):
            filtered = [c for c in cases if (sel_block == "All" or c['block'] == sel_block) and (c['difficulty'] == sel_diff)]
            if filtered:
                st.session_state.case = random.choice(filtered)
                st.session_state.submitted = False
                st.session_state.voice_text = ""
                st.rerun()
            else: st.warning("No cases match criteria.")
    
    st.divider()
    user_id = st.text_input("👤 User ID", value="Doctor")
    profession = st.selectbox("👩‍⚕️ Role", ["medicine", "nursing", "pharmacy", "ams"])

# ===================== 6. PAGES =====================

if page == "📖 User Guide":
    st.header("📖 Clinical Reasoning Manual: ACLR Loop")
    st.write("ระบบจำลองการตัดสินใจทางคลินิก (Cognitive Simulator) เพื่อฝึกการวินิจฉัยและวางแผนการรักษา")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🛠 Workflow")
        st.markdown("""
        1. **Gathering:** วิเคราะห์ Scenario และ Lab (Tab 1-2)
        2. **DDx Selection:** เลือกโรคอันตราย (Red Flags) ที่ต้องระวัง
        3. **Decision:** วินิจฉัยโรคและระบุเหตุผลพยาธิสภาพ
        4. **Management:** เลือก **Next Step** และ **Disposition** ให้เหมาะสม
        5. **Calibration:** ประเมินความมั่นใจก่อนกดส่ง
        """)
    with c2:
        st.subheader("📊 Scoring (10 Points)")
        st.write("- **Dx (4):** ความถูกต้องแม่นยำของโรค")
        st.write("- **Reasoning (3):** หลักฐานและตรรกะเหตุผล")
        st.write("- **Plan (2):** การเลือกขั้นตอนถัดไปและสถานที่ส่งต่อ")
        st.write("- **Safety (1):** การคัดกรอง Red Flags")
        st.error("⚠️ Penalty: หักคะแนนหากแผนการรักษาเป็นอันตรายต่อผู้ป่วย")

elif page == "🧪 Clinical Simulator":
    case = st.session_state.case
    st.title(f"🏥 Station: {case['block']} | Level: {case['difficulty'].upper()}")
    
    col_main, col_side = st.columns([2, 1])
    with col_main:
        t1, t2, t3 = st.tabs(["📋 Scenario", "🧪 Diagnostics", "✍️ Analysis & Action"])
        with t1:
            st.info(case["scenario"].get("en", ""))
            if case.get("image_url"): st.image(case["image_url"], use_container_width=True)
        with t2:
            if case["labs"]: st.table(pd.DataFrame(case["labs"]))
            else: st.write("No specific labs provided.")
        with t3:
            st.warning(f"**Task:** วินิจฉัยและวางแผนการรักษาในบทบาท {profession.upper()}")
            # Voice
            audio = mic_recorder(start_prompt="🎙️ Record Summary", stop_prompt="Stop", key='rec')
            if audio: st.session_state.voice_text = f"Suspected {case['answer']}"
            
            # --- Diagnosis Section ---
            dx_in = st.text_input("🩺 Final Diagnosis", value=st.session_state.voice_text)
            re_in = st.text_area("✍️ Pathophysiological Reasoning", placeholder="เนื่องจาก... จึงส่งผลให้...")
            
            st.divider()
            # --- Management Plan (Next Step) ---
            st.subheader("🚀 Management Plan")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                next_step = st.selectbox("🎯 Next Immediate Step", ["Observation", "Emergency Procedure", "Start Medication", "Diagnostic Imaging", "Consult Specialist", "Referral"])
            with p_col2:
                disposition = st.selectbox("🏥 Patient Disposition", ["Discharge Home", "Admit General Ward", "Admit ICU/CCU", "Emergency Operation"])
            
            selected_ddx = st.multiselect("🔍 Must-Exclude (Red Flags)", ["MI", "PE", "Aortic Dissection", "Sepsis", "Pneumothorax", "Stroke"])
            conf_in = st.slider("🎯 Confidence Level (%)", 0, 100, 50)
            
            if st.button("✅ Submit Decision"):
                if dx_in and re_in:
                    st.session_state.user_plan = {"step": next_step, "dispo": disposition}
                    st.session_state.submitted = True
                    st.rerun()
                else: st.error("Please provide Diagnosis and Reasoning.")

    if st.session_state.submitted:
        st.divider()
        sc, dx_s, r_s, p_s, s_s, target, used, level = evaluate_pro(dx_in, re_in, st.session_state.user_plan, case, profession, conf_in, selected_ddx)
        
        res_l, res_r = st.columns([2, 1])
        with res_l:
            st.subheader(f"📊 Assessment: {sc}/10")
            st.progress(sc * 10)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Dx", f"{dx_s}/4"); m2.metric("Reasoning", f"{r_s}/3")
            m3.metric("Plan", f"{p_s}/2"); m4.metric("Safety", "PASS" if s_s > 0 else "FAIL", delta=s_s)
            
            st.write(f"**Correct Dx:** `{target}`")
            st.write(f"**Your Decision:** {st.session_state.user_plan['step']} ➡️ {st.session_state.user_plan['dispo']}")
            if level == "wrong" and st.session_state.user_plan['dispo'] == "Discharge Home":
                st.error("❌ Critical Safety Error: วินิจฉัยผิดและปล่อยผู้ป่วยกลับบ้านเป็นอันตรายร้ายแรง")
        with res_r:
            st.subheader("👥 Team Feedback")
            for role, ans in case.get("interprofessional_answers", {}).items():
                with st.expander(f"Perspective from {role.upper()}"): st.write(ans)

elif page == "🏆 Leaderboard":
    st.header("🏆 Performance Dashboard")
    st.info("ระบบจะเริ่มเก็บสถิติเมื่อมีการเชื่อมต่อ Database (เช่น Google Sheets หรือ SQL)")

st.markdown("---")
st.caption("ACLR Ultimate v4.0 | Advanced Management Edition 2026")
