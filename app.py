import streamlit as st
import json, random, pandas as pd, time
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- 1. CONFIG (Must be first) ---
st.set_page_config(layout="wide", page_title="ACLR Pro - Clinical Reasoning Platform")

# --- 2. UTILS & SCORING LOGIC ---
def safe_case(case):
    case.setdefault("task", {})
    case.setdefault("interprofessional_answers", {})
    case.setdefault("reference", {"source": "Unknown", "year": "-"})
    case.setdefault("key_points", [])
    case.setdefault("labs", [])
    case.setdefault("teaching_pearls", "No pearls available for this case.")
    return case

@st.cache_data
def load_cases():
    try:
        with open("cases.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return [safe_case(c) for c in data]
    except FileNotFoundError:
        # Fallback Mock Data
        return [safe_case({
            "block": "Cardiology", 
            "difficulty": "hard",
            "scenario": {"en": "A 55-year-old female with sudden shortness of breath and pleuritic chest pain. History of recent hip surgery."},
            "labs": [
                {"item": "D-dimer", "value": 1200, "unit": "ng/mL", "ref": "< 500", "status": "high"},
                {"item": "SpO2", "value": 88, "unit": "%", "ref": "> 95", "status": "low"}
            ],
            "answer": "Pulmonary Embolism",
            "teaching_pearls": "Post-operative state + Sudden dyspnea = Rule out PE first (Wells Criteria)."
        })]

def highlight_labs(val):
    color = 'red' if val in ['high', 'low'] else 'black'
    return f'color: {color}; font-weight: bold'

def ai_grader_logic(user_dx, user_reasoning, case):
    # ระบบ Scoring ผสมระหว่าง Semantic Similarity และ Keyword Check
    target = case.get("answer", "")
    vec = TfidfVectorizer().fit_transform([user_dx.lower(), target.lower()])
    sim = cosine_similarity(vec[0:1], vec[1:2])[0][0]
    
    score = 0
    if sim > 0.8 or target.lower() in user_dx.lower():
        score = 10
        status = "Correct"
    elif sim > 0.4:
        score = 6
        status = "Partial"
    else:
        score = 2
        status = "Incorrect"
    
    return score, status

# --- 3. SESSION STATE ---
cases = load_cases()
if "case" not in st.session_state:
    st.session_state.case = random.choice(cases)

# --- 4. HEADER & USER AUTH ---
st.title("🧠 ACLR – Clinical Reasoning Platform")
st.caption("UWorld + AMBOSS + OSCE + Interprofessional Simulation")

user = st.text_input("👤 User ID / Name")
if not user:
    st.info("Please enter your User ID to begin.")
    st.stop()

# --- 5. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    profession = st.selectbox("👩‍⚕️ Profession", ["medicine", "dentistry", "nursing", "vet", "pharmacy", "public_health", "ams"])
    all_blocks = ["All"] + list(set(c["block"] for c in cases))
    block_choice = st.selectbox("📚 Block", all_blocks)
    diff_choice = st.selectbox("🎯 Difficulty", ["easy", "medium", "hard"])
    mode = st.radio("Mode", ["Practice", "OSCE", "Battle"])

    if st.button("🔄 New Case"):
        filtered = [c for c in cases if (block_choice == "All" or c["block"] == block_choice) and c["difficulty"] == diff_choice]
        if filtered:
            st.session_state.case = random.choice(filtered)
            st.session_state.pop("start", None)
            st.rerun()

case = st.session_state.case

# --- 6. MAIN LAYOUT (TABS) ---
tab1, tab2, tab3 = st.tabs(["📋 Patient Chart", "✍️ Your Assessment", "📊 Analytics"])

with tab1:
    col_scen, col_lab = st.columns([3, 2])
    
    with col_scen:
        st.subheader("Clinical Scenario")
        st.info(case["scenario"].get("en", "No scenario data"))
        if case.get("additional"):
            st.caption(case["additional"].get("en", ""))
        
        st.subheader("🎯 Your Task")
        task_text = case.get("task", {}).get(profession, case.get("task", {}).get("medicine", "Provide your clinical decision"))
        st.warning(task_text)

    with col_lab:
        st.subheader("🧪 Laboratory Results")
        if case.get("labs"):
            df_lab = pd.DataFrame(case["labs"])
            st.table(df_lab.style.applymap(highlight_labs, subset=['status']))
        else:
            st.write("No lab data for this case.")

    st.divider()
    st.subheader("👥 Interprofessional Board")
    ipa = case.get("interprofessional_answers", {})
    if ipa:
        cols = st.columns(len(ipa))
        for i, (role, ans) in enumerate(ipa.items()):
            cols[i].info(f"**{role.upper()}**\n\n{ans}")
    else:
        st.write("Team members are currently assessing...")

with tab2:
    st.subheader("Clinical Decision Making")
    
    # Differential Diagnosis Table
    st.markdown("**Differential Diagnosis (DDx) Table**")
    ddx_init = pd.DataFrame([
        {"Priority": "1 (Most Likely)", "Diagnosis": "", "Key Evidence / Rule-out": ""},
        {"Priority": "2", "Diagnosis": "", "Key Evidence / Rule-out": ""},
        {"Priority": "3", "Diagnosis": "", "Key Evidence / Rule-out": ""},
    ])
    edited_ddx = st.data_editor(ddx_init, use_container_width=True, hide_index=True)

    # Timer for OSCE
    if mode == "OSCE":
        if "start" not in st.session_state:
            if st.button("▶️ Start OSCE Timer"):
                st.session_state.start = time.time()
                st.rerun()
        else:
            remaining = max(0, 60 - int(time.time() - st.session_state.start))
            st.metric("⏱ Time Left", f"{remaining}s")
            if remaining <= 0: st.error("⏰ Time up!")

    # Final Inputs
    dx = st.text_input("🩺 Final Diagnosis / Answer")
    reasoning = st.text_area("✍️ Pathophysiology & Clinical Reasoning", placeholder="Explain your 'Why' step-by-step...")
    confidence = st.slider("Confidence (%)", 0, 100, 50)

    if st.button("🚀 Submit for AI Review"):
        score, status = ai_grader_logic(dx, reasoning, case)
        
        # Display Results
        st.divider()
        st.success(f"🏆 Score: {score}/10")
        
        col_fb_1, col_fb_2 = st.columns(2)
        with col_fb_1:
            st.markdown(f"### 🤖 AI Examiner Feedback")
            if status == "Correct": st.success("Excellent Diagnostic Accuracy")
            elif status == "Partial": st.warning("Close! Check details again")
            else: st.error("Diagnosis mismatch")
            st.write(f"**Target Answer:** {case['answer']}")
        
        with col_fb_2:
            st.markdown("### 💡 High-Yield Pearls")
            st.warning(case.get("teaching_pearls", ""))

        # Save History
        row = {"user": user, "block": case["block"], "score": score, "time": datetime.now()}
        try:
            old = pd.read_csv("responses.csv")
            pd.concat([old, pd.DataFrame([row])]).to_csv("responses.csv", index=False)
        except:
            pd.DataFrame([row]).to_csv("responses.csv", index=False)

with tab3:
    st.subheader(f"📊 {user}'s Performance Dashboard")
    try:
        df = pd.read_csv("responses.csv")
        user_df = df[df["user"] == user]
        if not user_df.empty:
            st.line_chart(user_df.set_index("time")["score"])
            
            avg_score = user_df["score"].mean()
            st.metric("Average Score", f"{avg_score:.2f} / 10")
            
            st.markdown("### Common Weaknesses")
            weak_block = user_df.groupby("block")["score"].mean().idxmin()
            st.error(f"Focus more on: **{weak_block}**")
        else:
            st.info("Complete your first case to see analytics.")
    except:
        st.info("No history recorded yet.")
