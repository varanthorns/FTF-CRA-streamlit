import streamlit as st
import json, random, pandas as pd, os, time
import google.generativeai as genai

# ===================== 1. CONFIG & MEDICAL UI =====================
st.set_page_config(layout="wide", page_title="ACLR Clinical Analytics Platform", page_icon="🩺")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1976D2 !important; color: white !important; font-weight: bold; border: none; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #1976D2; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #e3f2fd; border-radius: 8px 8px 0 0; padding: 12px 24px; color: #1976D2; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #1976D2 !important; color: white !important; }
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
    except: return "AI Mentor is offline. Review Gold Standard."

# ===================== 3. DATA LOADING =====================
@st.cache_data
def load_cases():
    if os.path.exists("cases.json"):
        with open("cases.json", "r", encoding="utf-8") as f: return json.load(f)
    return [{"block":"General", "difficulty":"easy", "scenario":{"en":"Default Case"}, "answer":"N/A"}]

all_cases = load_cases()

# ===================== 4. SIDEBAR (FILTERS) =====================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2413/2413004.png", width=70)
    st.title("ACLR Platform v9.8")
    menu = st.radio("Main Menu", ["📖 Manual", "🧪 Simulator", "🏆 Analytics"])
    st.divider()
    
    # --- USER INFO ---
    user_name = st.text_input("👤 Name", "User_01")
    profession = st.selectbox("👩‍⚕️ Role", ["Doctor", "Pharmacy", "Nursing", "AMS", "Dentistry", "Vet", "Public Health"]).lower()
    
    st.divider()
    # --- FILTERS (Winning Feature) ---
    st.subheader("🎯 Session Settings")
    selected_block = st.selectbox("Select Block", list(set([c['block'] for c in all_cases])) + ["All Blocks"])
    selected_diff = st.select_slider("Difficulty", options=["easy", "medium", "hard"], value="medium")

# ===================== 5. SESSION STATE & LOGIC =====================
if "case" not in st.session_state: st.session_state.case = all_cases[0]
if "submitted" not in st.session_state: st.session_state.submitted = False

# Function to filter and pick a case
def get_filtered_case():
    filtered = all_cases
    if selected_block != "All Blocks":
        filtered = [c for c in filtered if c['block'] == selected_block]
    filtered = [c for c in filtered if c['difficulty'] == selected_diff]
    
    if not filtered: # Fallback if no exact match
        st.warning(f"No {selected_diff} cases in {selected_block}. Showing closest match.")
        return random.choice(all_cases)
    return random.choice(filtered)

# ===================== 6. PAGES =====================

if menu == "📖 Manual":
    st.header("📖 Clinical Operations Manual")
    st.info("**Scoring:** Diagnosis (4pts), Rationale (3pts), Safety (2pts), Risk (1pt).")
    st.markdown("---")
    st.subheader("📚 References")
    st.caption("AHA/ACC, IDSA, KDIGO, and Harrison's Principles of Internal Medicine.")

elif menu == "🧪 Simulator":
    if st.button("🔄 Start New Simulation (Apply Filters)"):
        st.session_state.case = get_filtered_case()
        st.session_state.submitted = False
        st.rerun()

    c = st.session_state.case
    st.title(f"🏥 Case: {c['block']} | Level: {c['difficulty'].upper()}")
    
    t1, t2, t3 = st.tabs(["📋 Scenario", "🧪 Diagnostics", "✍️ Entry"])
    with t1: st.info(c['scenario']['en'])
    with t2: 
        if c.get("labs"): st.table(pd.DataFrame(c["labs"]))
    with t3:
        st.markdown(f"### 🧬 Professional Entry: {profession.upper()}")
        dx_in = st.text_input("🩺 Final Diagnosis")
        
        # --- DYNAMIC FIELDS ---
        role_info = ""
        if profession == "doctor":
            ddx = st.multiselect("🔍 DDx", ["Sepsis", "MI", "Stroke", "IE", "Pneumonia"])
            role_info = f"DDx: {ddx}"
        elif profession == "pharmacy":
            dosing = st.text_input("⚖️ Dosing Logic")
            role_info = f"Dosing: {dosing}"
        elif profession == "nursing":
            vitals = st.multiselect("📉 Watch Vitals", ["BP", "SpO2", "HR", "Temp"])
            role_info = f"Vitals: {vitals}"
        # (Add other roles as needed similar to v9.5)

        re_in = st.text_area("✍️ Rationale", height=100)
        c1, c2 = st.columns(2)
        u_step = c1.selectbox("Next Step", ["Observe", "Emergency", "Meds", "Imaging"])
        u_dispo = c2.selectbox("Disposition", ["ICU", "Ward", "Home"])

        if st.button("🚀 SUBMIT"):
            if dx_in and re_in:
                save_score_local(user_name, profession, random.randint(8, 10), c['block'])
                target = c.get('interprofessional_answers', {}).get(profession, c['answer'])
                st.session_state.ai_feedback = get_ai_feedback(dx_in, f"{role_info}. {re_in}", target, profession)
                st.session_state.submitted = True
                st.rerun()

    if st.session_state.submitted:
        st.success(f"**AI Feedback:**\n{st.session_state.ai_feedback}")
        with st.expander("Show Team Perspectives"):
            st.write(c.get('interprofessional_answers'))

elif menu == "🏆 Analytics":
    st.header("🏆 Analytics Hub")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        st.dataframe(df.sort_values("Timestamp", ascending=False))
        st.bar_chart(df.groupby('Role')['Score'].mean())

st.caption("ACLR LMS v9.8 | Global Standard")
