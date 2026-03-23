import streamlit as st
import json, random, pandas as pd, time
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ต้องอยู่บรรทัดแรกสุดของสคริปต์
st.set_page_config(layout="wide", page_title="ACLR Clinical Reasoning Professional")

# ===================== UTILS & LOAD =====================
def safe_case(case):
    case.setdefault("block", "General")
    case.setdefault("difficulty", "medium")
    case.setdefault("task", {})
    case.setdefault("interprofessional_answers", {})
    case.setdefault("reference", {"source":"Unknown","year":"-"})
    case.setdefault("key_points", [])
    case.setdefault("labs", []) # เพิ่มเพื่อรองรับระบบ Lab
    return case

@st.cache_data
def load_cases():
    try:
        with open("cases.json","r",encoding="utf-8") as f:
            data = json.load(f)
            return [safe_case(c) for c in data]
    except FileNotFoundError:
        # Mock Data ระดับ Professional สำหรับทดสอบ
        return [safe_case({
            "block":"Cardiovascular", 
            "difficulty":"hard", 
            "scenario":{"en":"A 62-year-old male with a history of HTN and smoking presents with 2 hours of substernal chest pressure and diaphoresis. BP 150/90, HR 95."}, 
            "labs": [
                {"Test": "Troponin T", "Result": "250", "Unit": "ng/L", "Range": "< 14"},
                {"Test": "CK-MB", "Result": "12.5", "Unit": "ng/mL", "Range": "< 5.0"}
            ],
            "answer":"ST-Elevation Myocardial Infarction", 
            "key_points":["chest pressure", "diaphoresis", "troponin", "smoking"],
            "interprofessional_answers": {
                "medicine": "Activate cath lab for primary PCI.",
                "nursing": "Establish IV access and continuous ECG monitoring.",
                "pharmacy": "Administer Aspirin 325mg and Clopidogrel loading dose."
            },
            "reference": {"source": "AHA/ACC STEMI Guidelines", "year": "2026"}
        })]

cases = load_cases()

def normalize(t): return str(t).lower().strip()

def semantic_score(a, b):
    try:
        vec = TfidfVectorizer().fit_transform([a, b])
        return cosine_similarity(vec[0:1], vec[1:2])[0][0]
    except:
        return 0

def extract_steps(reasoning):
    keys = ["because","therefore","thus","so","เนื่องจาก","ดังนั้น", "ทำให้", "ส่งผล", "เนื่องด้วย"]
    return [s.strip() for s in reasoning.split(".") if any(k in s.lower() for k in keys) and s.strip()]

# ===================== SCORING =====================
def evaluate(dx, reasoning, case, profession):
    target = case.get("interprofessional_answers", {}).get(profession, case.get("answer", ""))
    sim = semantic_score(dx, target)

    if normalize(dx) == normalize(target):
        dx_score, level = 5, "correct"
    elif sim > 0.6:
        dx_score, level = 3, "close"
    else:
        dx_score, level = 0, "wrong"

    r_score = 0
    used = []
    for k in case.get("key_points", []):
        if k.lower() in reasoning.lower():
            r_score += 1
            used.append(k)

    steps = extract_steps(reasoning)
    d_score = min(3, len(steps))
    r_score = min(5, r_score + (1 if len(reasoning.split()) > 20 else 0))
    total = min(10, dx_score + r_score + d_score)

    return total, dx_score, r_score, d_score, target, used, steps, level

# ===================== SESSION STATE =====================
if "case" not in st.session_state:
    st.session_state.case = random.choice(cases)

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ===================== HEADER =====================
st.title("🧠 ACLR – Clinical Reasoning Platform")
st.caption("UWorld + AMBOSS + OSCE + Interprofessional Simulation (Edition 2026)")

user = st.text_input("👤 User ID / Name")
if not user:
    st.info("Please enter your User ID to begin.")
    st.stop()

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("⚙️ Settings")
    profession = st.selectbox("👩‍⚕️ Profession", ["medicine","dentistry","nursing","vet","pharmacy","public_health","ams"])
    
    all_blocks = ["All"] + list(set(c["block"] for c in cases))
    block_choice = st.selectbox("📚 Block", all_blocks)
    diff_choice = st.selectbox("🎯 Difficulty", ["easy","medium","hard"])
    mode = st.radio("Mode", ["Practice", "OSCE", "Battle"])

    if st.button("🔄 New Case"):
        filtered = [c for c in cases if (block_choice == "All" or c["block"] == block_choice) and c["difficulty"] == diff_choice]
        if filtered:
            st.session_state.case = random.choice(filtered)
            st.session_state.submitted = False
            st.session_state.pop("start", None)
            st.rerun()
        else:
            st.warning("No cases found matching these criteria.")

case = st.session_state.case

# ===================== MAIN LAYOUT (UPGRADED) =====================
col1, col2 = st.columns([2, 1])

with col1:
    # ------------------ TABS SECTION ------------------
    tab1, tab2, tab3 = st.tabs(["📋 Clinical Scenario", "🩸 Investigations", "📝 Answer Sheet"])
    
    with tab1:
        st.markdown("### Patient Presentation")
        st.info(case["scenario"].get("en", "No scenario available"))
        if case.get("additional"):
            st.caption(f"**Vitals/Clinical Notes:** {case['additional'].get('en', '')}")
            
    with tab2:
        st.markdown("### 🧪 Laboratory & Diagnostic Results")
        if case.get("labs"):
            st.table(pd.DataFrame(case["labs"]))
        else:
            st.info("No specific laboratory data provided for this case.")
        
        # เพิ่มพื้นที่สำหรับ Imaging ในอนาคต
        st.caption("Note: Radiological images are currently described in the clinical notes.")

    with tab3:
        st.markdown("### 🎯 Your Task")
        task_text = case.get("task", {}).get(profession, "Provide your definitive clinical decision and reasoning.")
        st.warning(task_text)

        if mode == "OSCE":
            if "start" not in st.session_state:
                if st.button("▶️ Start Timer"):
                    st.session_state.start = time.time()
                    st.rerun()
            else:
                elapsed = int(time.time() - st.session_state.start)
                remaining = max(0, 180 - elapsed)
                st.metric("⏱ Time Left", f"{remaining}s")
                if remaining <= 0: st.error("⏰ Time up!")

        # ------------------ INPUT SECTION ------------------
        ddx = st.multiselect("🔍 Differential Diagnosis (Select relevant possibilities)", 
                           ["Sepsis", "MI", "Pulmonary Embolism", "Pneumonia", "Aortic Dissection", "Heart Failure", "Gastroenteritis", "Other"])
        
        dx = st.text_input("🩺 Final Diagnosis / Management Plan")
        reasoning = st.text_area("✍️ Clinical Reasoning (Identify Evidence & Pathophysiology)", height=150)
        
        if st.button("✅ Submit Decision"):
            if dx and reasoning:
                st.session_state.submitted = True
                # ประมวลผลคะแนน
                total, dx_s, r_s, d_s, target, used, steps, level = evaluate(dx, reasoning, case, profession)
                
                # แสดงผลลัพธ์ด้วย Visuals
                st.divider()
                st.markdown(f"### 🏆 Competency Report: {total}/10")
                
                res_cols = st.columns(3)
                res_cols[0].metric("Accuracy Score", f"{dx_s}/5")
                res_cols[1].metric("Reasoning Score", f"{r_s}/5")
                res_cols[2].metric("Logic Steps", f"{d_s}/3")
                
                st.progress(total * 10, text=f"Overall Competency: {level.upper()}")

                # Feedback Detailed
                st.markdown("#### 🔍 AI Examiner Feedback")
                if level == "correct": st.success("Excellent accuracy. Your diagnosis matches current clinical guidelines.")
                elif level == "close": st.warning("Clinically close. However, the exact terminology or specificity could be improved.")
                else: st.error("Diagnosis inconsistent with evidence. Please review the key clinical features.")
                
                st.markdown(f"**Gold Standard Answer:** `{target}`")
                
                c_left, c_right = st.columns(2)
                with c_left:
                    st.write("**Key Clinical Features Identified:**")
                    for u in used: st.write(f"✅ {u}")
                    missing = [k for k in case.get("key_points", []) if k.lower() not in reasoning.lower()]
                    if missing:
                        st.write("**Features Overlooked:**")
                        for m in missing: st.write(f"❌ {m}")
                
                with c_right:
                    st.write("**Logic Path (Causal Links):**")
                    if steps:
                        for s in steps: st.write(f"🔹 {s}")
                    else:
                        st.write("No clear 'Cause-Effect' linking words found (e.g., 'therefore', 'results in').")

                # บันทึกประวัติ
                res_df = pd.DataFrame([{"user": user, "block": case["block"], "score": total, "time": datetime.now()}])
                try:
                    old = pd.read_csv("responses.csv")
                    res_df = pd.concat([old, res_df])
                except: pass
                res_df.to_csv("responses.csv", index=False)
                st.toast("Progress Saved!")
            else:
                st.error("Submission incomplete. Diagnosis and Reasoning are mandatory.")

# ===================== RIGHT SIDEBAR / COL 2 =====================
with col2:
    st.markdown("## 👥 Team Decision Board")
    
    if st.session_state.submitted:
        ipa = case.get("interprofessional_answers", {})
        if ipa:
            for role, ans in ipa.items():
                if role == profession:
                    st.success(f"🟢 **{role.upper()} (Your Role):** \n{ans}")
                else:
                    st.info(f"⚪ **{role.upper()}:** \n{ans}")
        else:
            st.write("No interprofessional data available.")
    else:
        st.info("🔒 **Interprofessional Insights Locked**")
        st.caption("Submit your clinical decision to synchronize with the care team.")

    st.markdown("---")
    st.markdown("## 📖 Reference & Evidence")
    ref = case.get("reference", {})
    st.write(f"📚 **Source:** {ref.get('source','-')}")
    st.write(f"📅 **Year:** {ref.get('year','-')}")

    st.markdown("## 📊 Performance Analytics")
    try:
        df = pd.read_csv("responses.csv")
        user_df = df[df["user"] == user]
        if not user_df.empty:
            st.line_chart(user_df.set_index("time")["score"])
        else:
            st.caption("No data points available yet.")
    except:
        st.caption("History will appear after your first case.")
