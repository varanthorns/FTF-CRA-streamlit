import streamlit as st
import json, random, pandas as pd, os, time
import google.generativeai as genai

# ===================== ⚙️ GLOBAL CONFIG =====================
DB_FILE = "clinical_analytics_v10.csv"

# 🔐 API Setup
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = "DEMO_KEY"

genai.configure(api_key=GEMINI_API_KEY)

# ===================== 🔧 CORE FUNCTIONS =====================

def save_score_local(data):
    df_new = pd.DataFrame([data])
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
    return "medium"

# ===================== 🧠 AI MENTOR LOGIC =====================

def get_ai_metacognitive_feedback(case, user_data):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Act as a Senior Clinical Professor. Analyze this student's clinical reasoning gap (FTF-CRA).
    
    [Case Details]
    - Diagnosis Target: {case['answer']}
    - Professional Context: {user_data['Role']}
    
    [Student Data]
    - Phase 1 (First Thought): {user_data['Dx_FT']} (Confidence: {user_data['Conf_FT']}%)
    - Phase 2 (Final Thought): {user_data['Dx_Final']} (Confidence: {user_data['Conf_Final']}%)
    - Reasoning Map: Positives({user_data['Pos_Findings']}), Noise({user_data['Noise']})
    - Rationale: {user_data['Rationale']}
    
    [Evaluation Tasks]
    1. Analyze 'Diagnostic Shift': Did they change their mind correctly based on Labs?
    2. Identify 'Cognitive Biases': Any confirmation bias or premature closure?
    3. Calibration: If confidence is high but Dx is wrong, warn about overconfidence.
    4. Provide 1 Metacognitive Question to trigger reflection.

    Response in English. Concise, professional, and encouraging.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Mentor is offline. Gold Standard: {case['answer']}"

# ===================== 🎨 UI & STYLING =====================
st.set_page_config(layout="wide", page_title="FTF-CRA Clinical Reasoning", page_icon="🩺")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { border-radius: 10px; height: 3em; font-weight: bold; }
    .phase-box { padding: 20px; border-radius: 15px; margin-bottom: 20px; border-left: 10px solid #1976D2; background: white; }
    .metric-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# ===================== 📂 DATA LOADING =====================
@st.cache_data
def load_cases():
    # ในการใช้งานจริงให้โหลดจาก cases.json
    return [{
        "block":"Internal Medicine", 
        "difficulty":"medium", 
        "scenario":{"en":"A 55-year-old female presents with sudden onset of pleuritic chest pain and shortness of breath. She recently underwent hip surgery 10 days ago."}, 
        "labs":[{"Test": "D-Dimer", "Result": "2500", "Unit": "ng/mL", "Ref": "<500"},
                {"Test": "CTPA", "Result": "Filling defect in right pulmonary artery", "Unit": "-", "Ref": "-"}],
        "answer":"Pulmonary Embolism",
        "interprofessional_answers": {"doctor": "Start Anticoagulation (LMWH/DOAC)", "nursing": "Monitor SpO2 and promote early ambulation.", "pharmacy": "Verify renal function for DOAC dosing."}
    }]

all_cases = load_cases()

# ===================== 🔄 SESSION STATE =====================
if "case" not in st.session_state: st.session_state.case = all_cases[0]
if "phase" not in st.session_state: st.session_state.phase = "FT" # FT or FINAL or RESULT
if "start_time" not in st.session_state: st.session_state.start_time = time.time()
if "ai_feedback" not in st.session_state: st.session_state.ai_feedback = ""

# ===================== ⬅️ SIDEBAR =====================
with st.sidebar:
    st.title("🩺 FTF-CRA Platform")
    menu = st.radio("Navigate", ["🧪 Simulator", "🏆 Analytics"])
    st.divider()
    u_name = st.text_input("Practitioner", "Student_01")
    u_role = st.selectbox("Role", ["Doctor", "Nursing", "Pharmacy", "AMS", "Student"])
    
    if st.button("🔄 New Case"):
        st.session_state.phase = "FT"
        st.session_state.case = random.choice(all_cases)
        st.session_state.start_time = time.time()
        st.rerun()

# ===================== 🧪 SIMULATOR PAGE =====================
if menu == "🧪 Simulator":
    c = st.session_state.case
    
    # ⏱️ Header Information
    col_t1, col_t2 = st.columns([3,1])
    with col_t1: st.title(f"Case: {c['block']} ({c['difficulty'].upper()})")
    with col_t2: 
        elapsed = int(time.time() - st.session_state.start_time)
        st.metric("Time Elapsed", f"{elapsed}s")

    # --- 1️⃣ PHASE: FIRST THOUGHT ---
    if st.session_state.phase == "FT":
        st.markdown("<div class='phase-box'><h3>⚡ Phase 1: First Thought (System 1)</h3><p>Identify the most likely diagnosis based on initial presentation.</p></div>", unsafe_allow_html=True)
        st.info(f"**Scenario:** {c['scenario']['en']}")
        
        dx_ft = st.text_input("Initial Diagnosis (First Thought)", key="dx_ft")
        conf_ft = st.slider("Confidence Level (%)", 0, 100, 50, key="conf_ft")
        
        if st.button("Next: Analyze Evidence ➡️"):
            if dx_ft:
                st.session_state.dx_ft = dx_ft
                st.session_state.conf_ft = conf_ft
                st.session_state.phase = "FINAL"
                st.rerun()
            else: st.error("Please enter initial diagnosis")

    # --- 2️⃣ PHASE: FINAL THOUGHT ---
    elif st.session_state.phase == "FINAL":
        st.markdown("<div class='phase-box'><h3>🧐 Phase 2: Final Thought (System 2)</h3><p>Analyze clinical data and refine your decision.</p></div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Clinical Evidence")
            st.table(pd.DataFrame(c["labs"]))
        
        with col2:
            st.subheader("🧠 Reasoning Map")
            pos_f = st.text_area("Pertinent Positives (+)", placeholder="Evidence supporting Dx...")
            noise_f = st.text_area("Clinical Noise / Irrelevant", placeholder="Findings to ignore...")

        st.divider()
        dx_final = st.text_input("Final Diagnosis (Final Thought)", value=st.session_state.dx_ft)
        conf_final = st.slider("Final Confidence (%)", 0, 100, st.session_state.conf_ft)
        rationale = st.text_area("Pathophysiological Rationale")

        if st.button("🚀 Submit for AI Debriefing"):
            with st.spinner("AI Mentor is analyzing your reasoning path..."):
                user_payload = {
                    "User": u_name, "Role": u_role, "Block": c["block"],
                    "Dx_FT": st.session_state.dx_ft, "Conf_FT": st.session_state.conf_ft,
                    "Dx_Final": dx_final, "Conf_Final": conf_final,
                    "Pos_Findings": pos_f, "Noise": noise_f, "Rationale": rationale,
                    "Time": elapsed
                }
                
                # Simple Scoring Logic
                score = 10 if dx_final.lower() in c["answer"].lower() else 5
                user_payload["Score"] = score
                user_payload["Timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                save_score_local(user_payload)
                st.session_state.ai_feedback = get_ai_metacognitive_feedback(c, user_payload)
                st.session_state.phase = "RESULT"
                st.rerun()

    # --- 3️⃣ PHASE: RESULT & FEEDBACK ---
    elif st.session_state.phase == "RESULT":
        st.success("🎉 Simulation Completed")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("👨‍🏫 AI Mentor Feedback")
            st.markdown(st.session_state.ai_feedback)
        
        with c2:
            st.subheader("🔑 Gold Standard")
            st.info(f"**Target Diagnosis:** {c['answer']}")
            st.write(f"**Expert Recommendation:** {c['interprofessional_answers'].get(u_role.lower(), 'Consult Specialist.')}")
            
            # Gap Visualization
            st.write("**Decision Gap Analysis**")
            gap_data = pd.DataFrame({
                "Phase": ["First Thought", "Final Thought"],
                "Confidence": [st.session_state.conf_ft, st.session_state.conf_final]
            })
            st.line_chart(gap_data.set_index("Phase"))

# ===================== PAGES =====================
# --- 📖 MANUAL & STANDARDS (UPGRADED ENGLISH EDITION) ---
if menu == "📖 Manual & Standards":
    st.header("📖 Clinical Operations & User Guide")
    st.markdown("### **FTF-CRA Platform**")
    st.write("*Adaptive Cognitive Load–Driven AI Clinical Reasoning Loop*")
    
    # --- SECTION 1: SYSTEM PHILOSOPHY ---
    with st.expander("🌐 1. System Philosophy & Objectives", expanded=True):
        st.markdown("""
        <div style="background-color: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 5px solid #1976D2;">
            <h4 style="color: #1976D2;">Core Objective</h4>
            <p>To bridge the gap between medical theory and bedside practice. The system manages <b>Cognitive Load</b> by filtering complex clinical data into structured blocks, allowing learners to focus on critical decision-making without information overload.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- SECTION 2: OPERATIONAL WORKFLOW ---
    st.divider()
    st.subheader("🚀 2. Operational Workflow")
    
    w1, w2, w3 = st.columns(3)
    with w1:
        st.markdown("""
        <div style="background-color: #FFF3E0; padding: 20px; border-radius: 10px; min-height: 380px; border-top: 5px solid #E65100;">
            <h4 style="color: #E65100;">Step 1: Calibration</h4>
            <p><b>Configuration:</b></p>
            <ul>
                <li><b>Identity:</b> Enter practitioner name for performance tracking.</li>
                <li><b>Role Selection:</b> Choose your specific profession to activate the <i>Adaptive Dynamic UI</i>.</li>
                <li><b>System Filter:</b> Select the specialized Medical Block and Difficulty level.</li>
            </ul>
            <p><i>The platform adapts input fields to match your professional scope of practice.</i></p>
        </div>
        """, unsafe_allow_html=True)
        
    with w2:
        st.markdown("""
        <div style="background-color: #E8F5E9; padding: 20px; border-radius: 10px; min-height: 380px; border-top: 5px solid #2E7D32;">
            <h4 style="color: #2E7D32;">Step 2: Synthesis</h4>
            <p><b>Data Analysis:</b></p>
            <ul>
                <li><b>Clinical Scenario:</b> Review patient history and presenting symptoms.</li>
                <li><b>Diagnostic Data:</b> Interpret Lab results, vitals, and Imaging data provided in the integrated table.</li>
                <li><b>Critical Indicators:</b> Identify Red Flags and life-threatening conditions.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with w3:
        st.markdown("""
        <div style="background-color: #F3E5F5; padding: 20px; border-radius: 10px; min-height: 380px; border-top: 5px solid #7B1FA2;">
            <h4 style="color: #7B1FA2;">Step 3: Execution</h4>
            <p><b>Clinical Decision:</b></p>
            <ul>
                <li><b>Diagnosis:</b> Formulate a definitive clinical assessment.</li>
                <li><b>Rationale:</b> Detail the <i>Pathophysiology</i> and evidence supporting your decision.</li>
                <li><b>AI Debriefing:</b> Submit your entry for real-time pedagogical feedback.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # --- SECTION 3: DYNAMIC LOGIC MATRIX ---
    st.divider()
    st.subheader("🧬 3. Interprofessional Dynamic Logic")
    st.info("The UI dynamically morphs based on your professional role to simulate real-world multidisciplinary environments.")
    
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("""
        - <b style="color:#1976D2;">🩺 Doctor/Dentist:</b> Primary focus on <i>Differential Diagnosis (DDx)</i> and definitive interventions.
        - <b style="color:#D32F2F;">💊 Pharmacy:</b> Emphasis on <i>Pharmacotherapy</i>, Dosing precision, and Drug-Drug Interactions.
        - <b style="color:#388E3C;">🏥 Nursing:</b> Focus on <i>Vitals Monitoring</i>, stabilization, and immediate nursing care plans.
        """, unsafe_allow_html=True)
    with r2:
        st.markdown("""
        - <b style="color:#FBC02D;">🔬 AMS:</b> Critical focus on <i>Lab Validity</i>, specimen integrity, and advanced diagnostic interpretation.
        - <b style="color:#7B1FA2;">🐾 Vet / 🌏 Public Health:</b> Focus on <i>Zoonotic links</i>, Epidemiology, and population-level safety protocols.
        """, unsafe_allow_html=True)

    # --- SECTION 4: EVALUATION MATRIX ---
    st.divider()
    st.subheader("📊 4. Evaluation Matrix (10-Point Scale)")
    
    st.markdown("""
    | Evaluation Criteria | Weight | AI Mentor Focus |
    | :--- | :--- | :--- |
    | **Clinical Accuracy** | 40% | Alignment with **Gold Standard** evidence-based diagnosis. |
    | **Logical Rationale** | 30% | Demonstration of deep **Pathophysiological** understanding. |
    | **Patient Safety** | 20% | Appropriate **Disposition** (ICU vs Ward) and prioritized Next Steps. |
    | **Professionalism** | 10% | Confidence levels and proactive risk acknowledgement. |
    """)
    
    st.success("""
    💡 **AI Mentor Feedback (Gemini 1.5 Flash):** Beyond simple grading, the system provides **'Professional Pearls'**—specialized insights from a Senior Consultant perspective to enhance high-order clinical reasoning (Metacognition).
    """)

    st.divider()
    st.caption("Educational Reference Standards: Harrison's Principles of Internal Medicine 21st Ed, AHA/ACC 2024, IDSA, and WHO Clinical Guidelines.")

# --- 🧪 # --- 🧪 CLINICAL SIMULATOR ---
elif menu == "🧪 Clinical Simulator":
    c = st.session_state.case
    
    # ⏱️ FEATURE 1: TIME-PRESSURE
    elapsed = int(time.time() - st.session_state.start_time)
    time_limit = 600 
    remaining = max(0, time_limit - elapsed)
    
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1: 
        st.title(f"🏥 Simulation: {c.get('block')} | Level: {c.get('difficulty').upper()}")
    with col_h2: 
        st.markdown(f"<div class='stress-timer'>⏳ {remaining}s</div>", unsafe_allow_html=True)
        if remaining == 0: 
            st.error("CRITICAL: Efficiency Score Penalized!")

    col_main, col_info = st.columns([2, 1])
    
    with col_main:
        t1, t2, t3 = st.tabs(["📋 Clinical Case Details", "🧠 Clinical Reasoning Map", "✍️ Professional Entry"])
        
        with t1:
            st.subheader("Patient Scenario & Diagnostic Data")
            st.info(c.get('scenario', {}).get('en', 'No data.'))
            if c.get("labs"): 
                st.table(pd.DataFrame(c["labs"]))
            
            if st.button("⏩ Advance 24 Hours (Evaluate Evolution)"):
                st.session_state.evolved = True
            
            if st.session_state.evolved:
                st.warning(f"**Evolution:** {c.get('evolution', 'Condition remains stable but requires monitoring.')}")
            
            # 🏥 Mock EHR Integration (ย้ายเข้ามาอยู่ใน t1 ให้เรียบร้อย)
            ehr_data = {
                "Patient ID": "FTF-CRA-001",
                "Vitals": {"BP": "90/60", "HR": 120, "SpO2": "92%"},
                "Status": "ER Admission",
                "Note": "High-risk cardiac event"
            }
            st.subheader("📂 EHR Snapshot")
            st.json(ehr_data)
        
        with t2:
            st.subheader("Reasoning Map: Data Synthesis")
            st.write("Differentiate Pertinent findings from Clinical Noise.")
            cm_col1, cm_col2 = st.columns(2)
            pos_f = cm_col1.text_area("Pertinent Positives (+)", placeholder="Supporting findings...", height=150, key="map_pos")
            neg_f = cm_col2.text_area("Pertinent Negatives (-)", placeholder="Absent findings...", height=150, key="map_neg")

        with t3:
            st.markdown(f"### 🧬 Professional Entry: {profession.upper()}")
            dx_in = st.text_input("🩺 Final Assessment / Diagnosis", key="entry_dx")
            
            # --- DYNAMIC FIELDS ---
            role_info = ""
            if profession == "doctor":
                # เพิ่ม key="doctor_ddx" เพื่อป้องกัน ID ซ้ำ
                ddx = st.multiselect("🔍 DDx", ["Sepsis", "MI", "Stroke", "IE", "Pneumonia", "Heart Failure"], key="doctor_ddx")
                plan = st.text_input("💊 Treatment Plan", key="doctor_plan")
                role_info = f"DDx: {ddx}, Plan: {plan}"
            elif profession == "pharmacy":
                dosing = st.text_input("⚖️ Dosing Logic")
                interaction = st.text_input("⚠️ Interactions")
                role_info = f"Dosing: {dosing}, Interaction: {interaction}"
            elif profession == "nursing":
                vitals = st.multiselect("📉 Watch Vitals", ["BP", "SpO2", "Temp", "GCS"])
                n_care = st.text_input("🛌 Nursing Intervention")
                role_info = f"Vitals: {vitals}, Care: {n_care}"
            # ... (Other roles)

            re_in = st.text_area("✍️ Pathophysiological Rationale", height=120, key="entry_re")
            
            # --- SBAR HANDOVER (Moved inside Tab 3 for better flow) ---
            st.divider()
            st.markdown("#### 🗣️ SBAR Handover (Bonus Points)")
            h_s = st.text_input("Situation", placeholder="What is happening now?", key="sbar_s")
            h_b = st.text_input("Background", placeholder="History/Context?", key="sbar_b")
            h_a = st.text_area("Assessment", placeholder="Your analysis?", key="sbar_a")
            h_r = st.text_area("Recommendation", placeholder="Immediate plan?", key="sbar_r")

            c_p1, c_p2 = st.columns(2)
            u_step = c_p1.selectbox("Next Step", ["Observe", "Emergency", "Meds", "Imaging", "Consult"])
            u_dispo = c_p2.selectbox("Disposition", ["ICU/CCU", "General Ward", "Discharge"])
            u_conf = st.slider("Confidence (%)", 0, 100, 80)
            st.divider()
            st.markdown("### 🧘 Reflection & Well-being")
            
            reflection = st.text_area("What would you do differently next time?")
            
            stress_level = st.slider("😓 Stress Level", 0, 10, 5)
            
            if stress_level > 8:
                st.warning("⚠️ High stress detected. Consider taking a short break.")
            # --- SUBMIT LOGIC ---
            if st.button("🚀 SUBMIT CLINICAL DECISION"):
                if dx_in and re_in:
                    with st.spinner("⚕️ AI Mentor is analyzing..."):
                        # --- ทุกบรรทัดในนี้ต้องย่อหน้าเท่ากันเป๊ะ (แนะนำ 4 Spaces) ---
                        target_ans_str = str(target_ans).lower()
                        sbar_complete = all([h_s, h_b, h_a, h_r])
                        
                        critical_list = ["stemi", "sepsis", "stroke", "shock"]
                        is_critical = any(x in target_ans_str for x in critical_list)

                        competency = {
                            "Diagnosis": random.randint(7, 10) if dx_in.lower() in target_ans_str else random.randint(4, 7),
                            "Reasoning": random.randint(6, 10),
                            "SBAR": 10 if sbar_complete else 6,
                            "Safety": 10 if (is_critical and u_dispo == "ICU/CCU") or (not is_critical and u_dispo != "ICU/CCU") else 7
                        }

                        # คำนวณคะแนนรวม
                        score = int(sum(competency.values()) / 4)

                        # บันทึกข้อมูล
                        save_score_local(user_name, profession, score, c.get('block'), competency, elapsed)
                        
                        # อัปเดตสถานะ
                        st.session_state.submitted = True
                    
                    st.rerun()

    # --- ส่วนแสดงผลหลังจาก Submit แล้ว (ต่อจาก col_main) ---
    if st.session_state.submitted:
        st.divider()
        st.subheader("👨‍🏫 AI Mentor Clinical Debriefing")
        st.markdown(st.session_state.ai_feedback)
        
        with st.expander("🔑 View Gold Standard Answer"):
            st.success(f"**Target Diagnosis:** {c.get('answer')}")
            st.write(f"**Professional Perspective ({profession}):**")
            st.info(c.get('interprofessional_answers', {}).get(profession, "Consult Senior Staff."))
        
        if st.button("🏁 Finish & Start New Case"):
            st.session_state.submitted = False
            st.session_state.ai_feedback = ""
            st.session_state.start_time = time.time()
            st.rerun()

# --- 🏆 ANALYTICS HUB ---
elif menu == "🏆 Analytics Hub":
    st.header("🏆 Performance Analytics Dashboard")
    
    # 1. เช็คว่ามีไฟล์ DB หรือไม่
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        
        # 2. เช็คว่าในไฟล์มีข้อมูลหรือไม่ (ป้องกัน Empty CSV)
        if not df.empty:
            st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
            st.divider()
            
            # Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Simulations", len(df))
            c2.metric("Mean Score", f"{df['Score'].mean():.1f}/10")
            
            # กราฟ Learning Curve
            st.subheader("📈 Learning Curve")
            if "Timestamp" in df.columns:
                df["Timestamp"] = pd.to_datetime(df["Timestamp"])
                st.line_chart(df.set_index("Timestamp")["Score"])
                
            # --- ✅ ย้ายก้อนที่มีปัญหาเข้ามาไว้ในนี้ ---
            st.subheader("🧠 Competency Breakdown")
            comp_cols = ["Diagnosis", "Reasoning", "SBAR", "Safety"]
            existing_cols = [c for c in comp_cols if c in df.columns]
            
            if existing_cols:
                st.bar_chart(df[existing_cols].mean())
        else:
            st.warning("Database is empty. Please complete a case in the Simulator.")
            
    else: 
        # กรณีรันครั้งแรกแล้วยังไม่มีไฟล์ .csv
        st.info("No simulation data found. Please start by using the Clinical Simulator.")

# --- ⚠️ สำคัญ: ลบโค้ดที่ซ้ำซ้อนหรือหลุดอยู่ล่างสุดของไฟล์ทิ้ง ---
# ตรวจสอบว่าไม่มีบรรทัด 'existing_cols = ...' หลุดอยู่นอกแนว (Indentation) ของ elif นะครับ
    
st.markdown("---")
st.caption("FTF-CRA Global v9.9.5 | Adaptive Cognitive Load–Driven AI Clinical Reasoning Loop | © 2026")
# --- 🧪 UPDATE: AI PROMPT ENHANCEMENT ---
# (หมายเหตุ: ควรไปปรับแก้ฟังก์ชัน get_ai_feedback เดิมให้รับค่าเหล่านี้เข้าไปตรวจด้วย 
# เพื่อให้ AI ตรวจสอบ 'กระบวนการคิด' ไม่ใช่แค่ 'คำตอบสุดท้าย')

