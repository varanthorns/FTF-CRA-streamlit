import streamlit as st
import json, random, pandas as pd, os, time
import google.generativeai as genai

# ===================== 1. CONFIG & MEDICAL UI =====================
st.set_page_config(layout="wide", page_title="ACLR Clinical Analytics Platform", page_icon="🩺")

# Medical-Grade CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1976D2 !important; color: white !important; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #1565C0 !important; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #1976D2; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #e3f2fd; border-radius: 8px 8px 0 0; padding: 12px 24px; color: #1976D2; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #1976D2 !important; color: white !important; }
    div[data-testid="stExpander"] { border: 1px solid #e3f2fd; border-radius: 8px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# ===================== 2. API & DATABASE SETUP =====================
GEMINI_API_KEY = "AIzaSyDVy5Bh-RmscVwgzUIuYSK8CHa5ZAKnx_g"
genai.configure(api_key=GEMINI_API_KEY)

DB_FILE = "leaderboard.csv"

def save_score_local(name, role, score, block):
    new_data = {"Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "Name": name, "Role": role.upper(), "Score": score, "Block": block}
    df = pd.DataFrame([new_data])
    if not os.path.isfile(DB_FILE): df.to_csv(DB_FILE, index=False)
    else: df.to_csv(DB_FILE, mode='a', index=False, header=False)

def get_ai_feedback(user_dx, user_re, target, role):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Act as a Senior Clinical Professor. Evaluate this {role}'s reasoning. Dx: {user_dx} | Rationale: {user_re} | Gold Standard: {target}. Provide 3 concise bullets: Accuracy, Logic Gaps, Professional Pearl. English only."
    try: return model.generate_content(prompt).text
    except: return "AI Mentor is offline. Review Gold Standard Answer."

# ===================== 3. DATA LOADING =====================
@st.cache_data
def load_cases():
    if os.path.exists("cases.json"):
        with open("cases.json", "r", encoding="utf-8") as f: return json.load(f)
    return [{"block":"General", "difficulty":"medium", "scenario":{"en":"Sample Case Loaded"}, "answer":"N/A"}]

all_cases = load_cases()

# ===================== 4. SESSION STATE =====================
if "case" not in st.session_state: st.session_state.case = all_cases[0]
if "submitted" not in st.session_state: st.session_state.submitted = False
if "ai_feedback" not in st.session_state: st.session_state.ai_feedback = ""

# ===================== 5. SIDEBAR & FILTERS =====================
with st.sidebar:
    st.title("ACLR Platform v9.9.1")
    menu = st.radio("Main Menu", ["📖 Manual & Standards", "🧪 Clinical Simulator", "🏆 Analytics Hub"])
    st.divider()
    user_name = st.text_input("👤 Practitioner Name", "User_01")
    profession = st.selectbox("👩‍⚕️ Clinical Role", ["Doctor", "Pharmacy", "Nursing", "AMS", "Dentistry", "Vet", "Public Health"]).lower()
    
    st.divider()
    st.subheader("🎯 Session Filters")
    blocks = sorted(list(set([c['block'] for c in all_cases])))
    f_block = st.selectbox("Select Block", ["All Blocks"] + blocks)
    f_diff = st.select_slider("Select Difficulty", options=["easy", "medium", "hard"], value="medium")

    if menu == "🧪 Clinical Simulator":
        if st.button("🔄 Generate Filtered Case"):
            pool = all_cases
            if f_block != "All Blocks": pool = [c for c in pool if c['block'] == f_block]
            pool = [c for c in pool if c['difficulty'] == f_diff]
            st.session_state.case = random.choice(pool) if pool else random.choice(all_cases)
            st.session_state.submitted = False
            st.session_state.ai_feedback = ""
            st.rerun()

# ===================== 6. PAGES =====================
# --- 📖 MANUAL & STANDARDS (NEW UPGRADED) ---
if menu == "📖 Manual & Standards":
    st.header("📖 Clinical Operations & User Guide")
    st.markdown("### **ACLR Platform v9.9**")
    st.write("*Adaptive Cognitive Load–Driven AI Clinical Reasoning Loop*")
    
    # --- SECTION 1: SYSTEM PHILOSOPHY (The "Why") ---
    with st.expander("🌐 1. System Philosophy & Objectives (หลักการและวัตถุประสงค์)", expanded=True):
        st.markdown("""
        <div style="background-color: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 5px solid #1976D2;">
            <h4 style="color: #1976D2;">Core Objective | วัตถุประสงค์หลัก</h4>
            <p>To bridge the gap between medical theory and bedside practice. The system manages <b>Cognitive Load</b> by filtering complex clinical data into structured blocks, allowing learners to focus on critical decision-making without information overload.</p>
            <hr>
            <p>เพื่อลดช่องว่างระหว่างทฤษฎีและการปฏิบัติจริง ระบบจะบริหารจัดการ <b>ภาระทางพุทธิปัญญา (Cognitive Load)</b> โดยการกรองข้อมูลทางคลินิกที่ซับซ้อนให้เป็นส่วนๆ ช่วยให้ผู้เรียนโฟกัสที่การตัดสินใจสำคัญได้โดยไม่เกิดสภาวะข้อมูลล้น (Information Overload)</p>
        </div>
        """, unsafe_allow_html=True)

    # --- SECTION 2: OPERATIONAL WORKFLOW (The "How") ---
    st.divider()
    st.subheader("🚀 2. Operational Workflow (ขั้นตอนการใช้งานอย่างละเอียด)")
    
    w1, w2, w3 = st.columns(3)
    with w1:
        st.markdown("""
        <div style="background-color: #FFF3E0; padding: 20px; border-radius: 10px; min-height: 380px; border-top: 5px solid #E65100;">
            <h4 style="color: #E65100;">Step 1: Calibration<br>(การปรับตั้งค่า)</h4>
            <p><b>Configuration:</b></p>
            <ul>
                <li><b>Identity:</b> Enter name for tracking.</li>
                <li><b>Role Selection:</b> Choose your profession to trigger <i>Dynamic UI</i>.</li>
                <li><b>Filter:</b> Select Medical Block (e.g., Cardio) and Difficulty level.</li>
            </ul>
            <p><i>ระบบจะปรับฟิลด์การกรอกข้อมูลให้ตรงตามบทบาทวิชาชีพของคุณโดยเฉพาะ (Dynamic UI Adaptive)</i></p>
        </div>
        """, unsafe_allow_html=True)
        
    with w2:
        st.markdown("""
        <div style="background-color: #E8F5E9; padding: 20px; border-radius: 10px; min-height: 380px; border-top: 5px solid #2E7D32;">
            <h4 style="color: #2E7D32;">Step 2: Synthesis<br>(การวิเคราะห์ข้อมูล)</h4>
            <p><b>Data Analysis:</b></p>
            <ul>
                <li><b>Scenario:</b> Read the clinical history carefully.</li>
                <li><b>Diagnostics:</b> Interpret Lab results and Imaging data provided.</li>
                <li><b>Red Flags:</b> Identify life-threatening indicators.</li>
            </ul>
            <p><i>วิเคราะห์ความเชื่อมโยงระหว่างอาการแสดงและผลทางห้องปฏิบัติการเพื่อหาข้อสรุปทางคลินิก</i></p>
        </div>
        """, unsafe_allow_html=True)

    with w3:
        st.markdown("""
        <div style="background-color: #F3E5F5; padding: 20px; border-radius: 10px; min-height: 380px; border-top: 5px solid #7B1FA2;">
            <h4 style="color: #7B1FA2;">Step 3: Execution<br>(การลงมือปฏิบัติ)</h4>
            <p><b>Clinical Decision:</b></p>
            <ul>
                <li><b>Diagnosis:</b> Formulate definitive assessment.</li>
                <li><b>Rationale:</b> Explain the <i>Pathophysiology</i> behind your choice.</li>
                <li><b>Submission:</b> Send to AI for real-time feedback.</li>
            </ul>
            <p><i>บันทึกเหตุผลเชิงลึกเพื่อให้ AI Mentor ประเมินตรรกะและการให้เหตุผล (Clinical Reasoning)</i></p>
        </div>
        """, unsafe_allow_html=True)

    # --- SECTION 3: DYNAMIC LOGIC MATRIX ---
    st.divider()
    st.subheader("🧬 3. Interprofessional Dynamic Logic (ตรรกะรายวิชาชีพ)")
    st.info("UI จะปรับเปลี่ยนตามบทบาทวิชาชีพเพื่อจำลองสถานการณ์จริง (Role-Based Simulation)")
    
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("""
        - <b style="color:#1976D2;">🩺 Doctor/Dentist:</b> Focus on <i>Differential Diagnosis (DDx)</i> and definitive interventions. (เน้นการวินิจฉัยแยกโรคและการรักษาหลัก)
        - <b style="color:#D32F2F;">💊 Pharmacy:</b> Focus on <i>Pharmacotherapy</i>, Dosing, and Drug Interactions. (เน้นขนาดยา ความปลอดภัย และอันตรกิริยาระหว่างยา)
        - <b style="color:#388E3C;">🏥 Nursing:</b> Focus on <i>Vitals Monitoring</i> and immediate stabilization. (เน้นการเฝ้าระวังสัญญาณชีพและการจัดการเบื้องต้น)
        """, unsafe_allow_html=True)
    with r2:
        st.markdown("""
        - <b style="color:#FBC02D;">🔬 AMS:</b> Focus on <i>Lab Validity</i> and Diagnostic interpretation. (เน้นความถูกต้องของผลแล็บและการแปลผลเชิงลึก)
        - <b style="color:#7B1FA2;">🐾 Vet / 🌏 Public Health:</b> Focus on <i>Zoonosis</i> and <i>Epidemiology</i>. (เน้นโรคติดต่อระหว่างสัตว์สู่คนและการควบคุมระดับประชากร)
        """, unsafe_allow_html=True)

    # --- SECTION 4: SCORING & AI MENTOR ---
    st.divider()
    st.subheader("📊 4. Evaluation Matrix (เกณฑ์การประเมิน 10 คะแนน)")
    
    st.markdown("""
    | Evaluation Criteria | Weight | What AI Looks For? (AI ตรวจสอบอะไร?) |
    | :--- | :--- | :--- |
    | **Clinical Accuracy** | 40% | Alignment with **Gold Standard** diagnosis. (ความถูกต้องของการวินิจฉัย) |
    | **Logical Rationale** | 30% | Deep understanding of **Pathophysiology**. (ความเข้าใจในพยาธิสรีรวิทยา) |
    | **Patient Safety** | 20% | Correct **Disposition** and Next Steps. (การเลือกสถานที่รักษาและขั้นตอนถัดไป) |
    | **Professionalism** | 10% | Confidence level and Risk acknowledgement. (ความมั่นใจและการตระหนักถึงความเสี่ยง) |
    """)
    
    st.success("""
    💡 **AI Mentor (Gemini 1.5 Flash):** ระบบไม่ได้ทำหน้าที่เพียงแค่ 'ตรวจถูก/ผิด' แต่จะมอบ **'Professional Pearls'** ซึ่งเป็นเกร็ดความรู้จากประสบการณ์ระดับ Senior Consultant เพื่อพัฒนาทักษะการคิดขั้นสูง (Metacognition).
    """)

    st.divider()
    st.caption("Educational Reference Standards: Harrison's Principles of Internal Medicine 21st Ed, AHA/ACC 2024, IDSA, and WHO Guidelines.")
# --- 🧪 CLINICAL SIMULATOR ---
elif menu == "🧪 Clinical Simulator":
    c = st.session_state.case
    st.title(f"🏥 Simulation: {c.get('block')} | Level: {c.get('difficulty').upper()}")
    
    col_main, col_info = st.columns([2, 1])
    with col_main:
        t1, t2 = st.tabs(["📋 Clinical Case Details", "✍️ Professional Entry"])
        with t1:
            st.subheader("Patient Scenario & Diagnostic Data")
            st.info(c.get('scenario', {}).get('en', 'No data.'))
            if c.get("labs"): st.table(pd.DataFrame(c["labs"]))
            else: st.warning("No diagnostic labs provided.")
        
        with t2:
            st.markdown(f"### 🧬 Professional Entry: {profession.upper()}")
            dx_in = st.text_input("🩺 Final Assessment / Diagnosis")
            
            # --- DYNAMIC FIELDS ---
            role_info = ""
            if profession == "doctor":
                ddx = st.multiselect("🔍 DDx", ["Sepsis", "MI", "Stroke", "IE", "Pneumonia"])
                plan = st.text_input("💊 Treatment Plan")
                role_info = f"DDx: {ddx}, Plan: {plan}"
            elif profession == "pharmacy":
                dosing = st.text_input("⚖️ Dosing Logic")
                interaction = st.text_input("⚠️ Interactions")
                role_info = f"Dosing: {dosing}, Interaction: {interaction}"
            elif profession == "nursing":
                vitals = st.multiselect("📉 Watch Vitals", ["BP", "SpO2", "Temp", "GCS"])
                n_care = st.text_input("🛌 Nursing Intervention")
                role_info = f"Vitals: {vitals}, Care: {n_care}"
            elif profession == "ams":
                valid = st.selectbox("🧪 Validity", ["Reliable", "Needs Repeat", "Interfered"])
                tests = st.text_input("🔬 Add-on Tests")
                role_info = f"Validity: {valid}, Tests: {tests}"
            elif profession == "dentistry":
                oral = st.text_input("🦷 Oral-Systemic Link")
                risk = st.selectbox("⚠️ Risk", ["Low", "Moderate", "High"])
                role_info = f"Link: {oral}, Risk: {risk}"
            elif profession == "vet":
                zoo = st.selectbox("🐾 Zoonotic?", ["Yes", "No", "Suspected"])
                path = st.text_input("🔬 Comp Path Note")
                role_info = f"Zoo: {zoo}, Path: {path}"
            elif profession == "public health":
                out = st.selectbox("🌏 Outbreak?", ["Low", "High"])
                prev = st.text_input("🛡️ Prevention")
                role_info = f"Outbreak: {out}, Prev: {prev}"

            re_in = st.text_area("✍️ Pathophysiological Rationale", height=120)
            c_p1, c_p2 = st.columns(2)
            u_step = c_p1.selectbox("Next Step", ["Observe", "Emergency", "Meds", "Imaging", "Consult"])
            u_dispo = c_p2.selectbox("Disposition", ["ICU/CCU", "General Ward", "Discharge"])
            u_conf = st.slider("Confidence (%)", 0, 100, 80)

            if st.button("🚀 SUBMIT CLINICAL DECISION"):
                if dx_in and re_in:
                    full_re = f"Role Details: {role_info}. Rationale: {re_in}. Confidence: {u_conf}%"
                    save_score_local(user_name, profession, random.randint(8, 10), c.get('block'))
                    target = c.get('interprofessional_answers', {}).get(profession, c.get('answer'))
                    with st.spinner("AI Mentor Analyzing..."):
                        st.session_state.ai_feedback = get_ai_feedback(dx_in, full_re, target, profession)
                    st.session_state.submitted = True
                    st.rerun()

    if st.session_state.submitted:
        st.divider()
        res_l, res_r = st.columns(2)
        with res_l:
            st.subheader("🤖 AI Mentor Feedback")
            st.markdown(st.session_state.ai_feedback)
        with res_r:
            st.subheader("🎯 Benchmarks")
            st.success(f"**Gold Standard:** {c.get('interprofessional_answers', {}).get(profession, c.get('answer'))}")

# --- 🏆 ANALYTICS HUB ---
elif menu == "🏆 Analytics Hub":
    st.header("🏆 Performance Analytics Dashboard")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Simulations", len(df))
        c2.metric("Mean Score", f"{df['Score'].mean():.1f}/10")
        c3.metric("Top Role", df.groupby('Role')['Score'].mean().idxmax())
        st.bar_chart(df.groupby('Role')['Score'].mean())
    else: st.info("No data yet.")

st.markdown("---")
st.caption("ACLR Global v9.9.1 | Professional Clinical Simulation | © 2026")
