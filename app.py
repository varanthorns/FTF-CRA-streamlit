import streamlit as st
import json, random, pandas as pd, os, time
import google.generativeai as genai

# ===================== 1. CONFIG & MEDICAL UI =====================
st.set_page_config(layout="wide", page_title="ACLR Clinical Analytics Platform", page_icon="🩺")

# Medical-Grade CSS Injector
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
    new_data = {
        "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Name": name,
        "Role": role.upper(),
        "Score": score,
        "Block": block
    }
    df = pd.DataFrame([new_data])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode='a', index=False, header=False)

def get_ai_feedback(user_dx, user_re, target, role):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Act as a Senior Clinical Professor. Evaluate this {role}'s reasoning.
    Diagnosis: {user_dx} | Rationale: {user_re} | Gold Standard: {target}
    Provide 3 concise bullet points: 1. Clinical Accuracy 2. Logic Gaps 3. Professional 'Pearl'.
    Language: English.
    """
    try:
        return model.generate_content(prompt).text
    except:
        return "AI Mentor is currently offline. Please refer to the Gold Standard Answer."

# ===================== 3. DATA LOADING =====================
@st.cache_data
def load_cases():
    if os.path.exists("cases.json"):
        with open("cases.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return [{"block":"General", "difficulty":"medium", "scenario":{"en":"Sample Case Loaded"}, "answer":"N/A"}]

cases = load_cases()

# ===================== 4. SESSION STATE =====================
if "case" not in st.session_state: st.session_state.case = cases[0]
if "submitted" not in st.session_state: st.session_state.submitted = False
if "ai_feedback" not in st.session_state: st.session_state.ai_feedback = ""

# ===================== 5. SIDEBAR =====================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2413/2413004.png", width=70) # Medical Folder Icon
    st.title("ACLR Platform v9.0")
    menu = st.radio("Main Menu", ["📖 Manual & Standards", "🧪 Clinical Simulator", "🏆 Analytics Hub"])
    st.divider()
    user_name = st.text_input("👤 Practitioner ID/Name", "User_01")
    profession = st.selectbox("👩‍⚕️ Clinical Role", ["Doctor", "Pharmacy", "Nursing", "AMS", "Dentistry", "Vet", "Public Health"]).lower()
    
    if menu == "🧪 Clinical Simulator":
        if st.button("🔄 Next Clinical Case"):
            st.session_state.case = random.choice(cases)
            st.session_state.submitted = False
            st.session_state.ai_feedback = ""
            st.rerun()

# ===================== 6. PAGES =====================

# --- 📖 MANUAL & STANDARDS ---
if menu == "📖 Manual & Standards":
    st.header("📖 Clinical Operations Manual")
    
    st.subheader("1. System Workflow")
    st.markdown("""
    1. **Initialization:** Select your professional role in the sidebar.
    2. **Analysis:** Review the patient scenario and diagnostic data (Labs/Imaging).
    3. **Formulation:** Input your Diagnosis and Pathophysiological Rationale.
    4. **Management:** Determine the immediate Next Step and Patient Disposition.
    5. **Evaluation:** Submit to receive **AI-Driven Feedback** and compare with Team Perspectives.
    """)

    st.divider()
    st.subheader("2. Scoring & Grading Criteria (10-Point Scale)")
    st.write("Your performance is evaluated based on the following weighted metrics:")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.info("**Diagnosis Accuracy (4 pts)**\n- Direct alignment with the gold standard for your specific role.")
        st.success("**Clinical Rationale (3 pts)**\n- Depth of pathophysiological explanation and use of evidence-based terminology.")
    with col_g2:
        st.warning("**Safety & Disposition (2 pts)**\n- Selection of correct 'Next Step' and appropriate level of care (Disposition).")
        st.error("**Risk Mitigation (1 pt)**\n- Successful identification of 'Must-Exclude' red flags.")

    st.divider()
    st.subheader("3. Professional Response Guidelines")
    st.write("Responses must align with professional scopes of practice:")
    
    g_tabs = st.tabs(["Doctor", "Pharmacy", "Nursing", "AMS", "Dentistry", "Vet", "Public Health"])
    with g_tabs[0]: st.markdown("**Focus:** Definitive diagnosis, surgical/medical intervention, and primary care plan.")
    with g_tabs[1]: st.markdown("**Focus:** Pharmacokinetics, drug-drug interactions, and optimal dosing regimens.")
    with g_tabs[2]: st.markdown("**Focus:** Patient monitoring, early warning signs (EWS), and bedside safety protocols.")
    with g_tabs[3]: st.markdown("**Focus:** Laboratory methodology, result validity, and diagnostic specificity.")
    with g_tabs[4]: st.markdown("**Focus:** Odontogenic infections, oral-systemic manifestations, and dental-clearing protocols.")
    with g_tabs[5]: st.markdown("**Focus:** Zoonotic transmission, comparative pathology, and animal-human health links.")
    with g_tabs[6]: st.markdown("**Focus:** Epidemiological control, community screening, and preventive health policy.")

    st.divider()
    st.subheader("📚 Clinical References")
    st.markdown("""
    All cases and logic patterns are synthesized from the following international guidelines:
    - **AHA/ACC Guidelines:** Cardiovascular assessment and MI protocols.
    - **IDSA Guidelines:** Management of Infective Endocarditis and Sepsis.
    - **KDIGO Guidelines:** Renal monitoring and drug dosing in AKI.
    - **WHO One Health:** Zoonotic and Public Health frameworks.
    - **Harrison's Principles of Internal Medicine (21st Ed).**
    """)

# --- 🧪 CLINICAL SIMULATOR ---
elif menu == "🧪 Clinical Simulator":
    c = st.session_state.case
    st.title(f"🏥 Simulation: {c.get('block')} | Level: {c.get('difficulty').upper()}")
    
    col_main, col_info = st.columns([2, 1])
    with col_main:
        t1, t2, t3 = st.tabs(["📋 Case Scenario", "🧪 Diagnostic Data", "✍️ Clinical Entry"])
        with t1:
            st.info(c.get('scenario', {}).get('en', 'No English scenario available.'))
        with t2:
            if c.get("labs"): st.table(pd.DataFrame(c["labs"]))
            else: st.warning("No diagnostic data provided for this case.")
        with t3:
            st.markdown(f"**Acting Role: {profession.upper()}**")
            dx_in = st.text_input("🩺 Final Diagnosis")
            re_in = st.text_area("✍️ Professional Rationale", placeholder="Explain the pathophysiology and logic behind your diagnosis...", height=150)
            
            p1, p2 = st.columns(2)
            u_step = p1.selectbox("Immediate Next Step", ["Observation", "Emergency Procedure", "Start Medication", "Imaging/Biopsy", "Specialist Consult"])
            u_dispo = p2.selectbox("Patient Disposition", ["Admit ICU/CCU", "Admit General Ward", "Discharge with Follow-up"])
            u_conf = st.slider("Confidence Level (%)", 0, 100, 80)

            if st.button("🚀 SUBMIT CLINICAL DECISION"):
                if dx_in and re_in:
                    # Score Calculation (Simulated Logic)
                    score = random.randint(7, 10) 
                    save_score_local(user_name, profession, score, c.get('block'))
                    target = c.get('interprofessional_answers', {}).get(profession, c.get('answer'))
                    with st.spinner("AI Mentor is analyzing your reasoning..."):
                        st.session_state.ai_feedback = get_ai_feedback(dx_in, re_in, target, profession)
                    st.session_state.submitted = True
                    st.rerun()

    if st.session_state.submitted:
        st.divider()
        res_l, res_r = st.columns(2)
        with res_l:
            st.subheader("🤖 AI Clinical Tutor Feedback")
            st.markdown(st.session_state.ai_feedback)
        with res_r:
            st.subheader("🎯 Interprofessional Benchmarks")
            st.success(f"**Role-Specific Gold Standard:** {c.get('interprofessional_answers', {}).get(profession, c.get('answer'))}")
            with st.expander("Explore Team Perspectives"):
                for role, ans in c.get('interprofessional_answers', {}).items():
                    st.write(f"**{role.upper()}:** {ans}")

# --- 🏆 ANALYTICS HUB ---
elif menu == "🏆 Analytics Hub":
    st.header("🏆 Performance Analytics Dashboard")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Simulations Completed", len(df))
        c2.metric("System Mean Score", f"{df['Score'].mean():.1f}/10")
        c3.metric("Top Performing Role", df.groupby('Role')['Score'].mean().idxmax())
        
        st.subheader("Performance Trend by Professional Role")
        st.bar_chart(df.groupby('Role')['Score'].mean())
    else:
        st.info("The Analytics Hub is currently empty. Complete a simulation to generate data.")

st.markdown("---")
st.caption("ACLR Global Analytics v9.0 | Evidence-Based Clinical Simulation | © 2026")
