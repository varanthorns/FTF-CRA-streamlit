@@ -5,72 +5,68 @@
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ต้องอยู่บรรทัดแรกสุดของสคริปต์
st.set_page_config(layout="wide", page_title="ACLR Clinical Reasoning")
# --- 1. CONFIG (Must be first) ---
st.set_page_config(layout="wide", page_title="ACLR Pro - Clinical Reasoning Platform")

# ===================== UTILS & LOAD =====================
# --- 2. UTILS & SCORING LOGIC ---
def safe_case(case):
    case.setdefault("task", {})
    case.setdefault("interprofessional_answers", {})
    case.setdefault("reference", {"source":"Unknown","year":"-"})
    case.setdefault("reference", {"source": "Unknown", "year": "-"})
    case.setdefault("key_points", [])
    case.setdefault("labs", [])
    case.setdefault("teaching_pearls", "No pearls available for this case.")
    return case

@st.cache_data
def load_cases():
    # ตรวจสอบว่ามีไฟล์จริงไหม หรือสร้าง Mock data สำหรับทดสอบ
    try:
        with open("cases.json","r",encoding="utf-8") as f:
            return json.load(f)
        with open("cases.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return [safe_case(c) for c in data]
    except FileNotFoundError:
        return [{"block":"General", "difficulty":"easy", "scenario":{"en":"Patient with fever"}, "answer":"Flu", "key_points":["fever"]}]

cases = load_cases()

def normalize(t): return str(t).lower().strip()

def semantic_score(a, b):
    try:
        vec = TfidfVectorizer().fit_transform([a, b])
        return cosine_similarity(vec[0:1], vec[1:2])[0][0]
    except:
        return 0

def extract_steps(reasoning):
    keys = ["because","therefore","thus","so","เนื่องจาก","ดังนั้น"]
    return [s.strip() for s in reasoning.split(".") if any(k in s.lower() for k in keys) and s.strip()]

# ===================== SCORING =====================
def evaluate(dx, reasoning, case, profession):
    target = case.get("interprofessional_answers", {}).get(profession, case.get("answer", ""))
    sim = semantic_score(dx, target)

    if normalize(dx) == normalize(target):
        dx_score, level = 5, "correct"
    elif sim > 0.6:
        dx_score, level = 3, "close"
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
        score = 2
        status = "Incorrect"
    
    return score, status

# ===================== SESSION STATE =====================
# --- 3. SESSION STATE ---
cases = load_cases()
if "case" not in st.session_state:
    st.session_state.case = safe_case(random.choice(cases))
    st.session_state.case = random.choice(cases)

# ===================== HEADER =====================
# --- 4. HEADER & USER AUTH ---
st.title("🧠 ACLR – Clinical Reasoning Platform")
st.caption("UWorld + AMBOSS + OSCE + Interprofessional Simulation")

@@ -79,107 +75,128 @@ def evaluate(dx, reasoning, case, profession):
    st.info("Please enter your User ID to begin.")
    st.stop()

# ===================== SIDEBAR =====================
# --- 5. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    profession = st.selectbox("👩‍⚕️ Profession", ["medicine","dentistry","nursing","vet","pharmacy","public_health","ams"])
    
    profession = st.selectbox("👩‍⚕️ Profession", ["medicine", "dentistry", "nursing", "vet", "pharmacy", "public_health", "ams"])
    all_blocks = ["All"] + list(set(c["block"] for c in cases))
    block_choice = st.selectbox("📚 Block", all_blocks)
    diff_choice = st.selectbox("🎯 Difficulty", ["easy","medium","hard"])
    diff_choice = st.selectbox("🎯 Difficulty", ["easy", "medium", "hard"])
    mode = st.radio("Mode", ["Practice", "OSCE", "Battle"])

    if st.button("🔄 New Case"):
        filtered = [c for c in cases if (block_choice == "All" or c["block"] == block_choice) and c["difficulty"] == diff_choice]
        if filtered:
            st.session_state.case = safe_case(random.choice(filtered))
            st.session_state.pop("start", None) # Reset timer
            st.session_state.case = random.choice(filtered)
            st.session_state.pop("start", None)
            st.rerun()

case = st.session_state.case

# ===================== MAIN LAYOUT =====================
col1, col2 = st.columns([2, 1])
# --- 6. MAIN LAYOUT (TABS) ---
tab1, tab2, tab3 = st.tabs(["📋 Patient Chart", "✍️ Your Assessment", "📊 Analytics"])

with col1:
    st.markdown("## 📋 Clinical Scenario")
    st.info(case["scenario"].get("en", "No scenario available"))
with tab1:
    col_scen, col_lab = st.columns([3, 2])

    if case.get("additional"):
        st.caption(case["additional"].get("en", ""))

    st.markdown("## 🎯 Your Task")
    task_text = case.get("task", {}).get(profession, case.get("task", {}).get("medicine", "Provide your clinical decision"))
    st.warning(task_text)
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

    st.markdown("## 🧠 Think Step-by-Step")
    st.caption("1. Identify symptoms | 2. Link pathophysiology | 3. Consider differential | 4. Decide")
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
            if st.button("▶️ Start OSCE"):
            if st.button("▶️ Start OSCE Timer"):
                st.session_state.start = time.time()
                st.rerun()
        else:
            elapsed = int(time.time() - st.session_state.start)
            remaining = max(0, 60 - elapsed)
            remaining = max(0, 60 - int(time.time() - st.session_state.start))
            st.metric("⏱ Time Left", f"{remaining}s")
            if remaining <= 0:
                st.error("⏰ Time up!")
            if remaining <= 0: st.error("⏰ Time up!")

    dx = st.text_input("停 Your Diagnosis / Answer")
    reasoning = st.text_area("✍️ Clinical Reasoning")
    # Final Inputs
    dx = st.text_input("🩺 Final Diagnosis / Answer")
    reasoning = st.text_area("✍️ Pathophysiology & Clinical Reasoning", placeholder="Explain your 'Why' step-by-step...")
    confidence = st.slider("Confidence (%)", 0, 100, 50)

    if st.button("✅ Submit"):
        total, dx_s, r_s, d_s, target, used, steps, level = evaluate(dx, reasoning, case, profession)
        st.success(f"🏆 Score: {total}/10")
        
        # Feedback
        st.markdown("### 🔍 AI Examiner Feedback")
        if level == "correct": st.success("Excellent accuracy")
        elif level == "close": st.warning("Close but not precise")
        else: st.error("Incorrect diagnosis")
    if st.button("🚀 Submit for AI Review"):
        score, status = ai_grader_logic(dx, reasoning, case)

        st.write(f"**Correct Answer:** {target}")
        # Display Results
        st.divider()
        st.success(f"🏆 Score: {score}/10")

        c_left, c_right = st.columns(2)
        with c_left:
            st.write("**Key Features Found:**", used)
            missing = [k for k in case.get("key_points", []) if k not in used]
            if missing: st.write("**Missing:**", missing)
        col_fb_1, col_fb_2 = st.columns(2)
        with col_fb_1:
            st.markdown(f"### 🤖 AI Examiner Feedback")
            if status == "Correct": st.success("Excellent Diagnostic Accuracy")
            elif status == "Partial": st.warning("Close! Check details again")
            else: st.error("Diagnosis mismatch")
            st.write(f"**Target Answer:** {case['answer']}")

        with c_right:
            st.write("**Logic Steps:**")
            for s in steps: st.write(f"✅ {s}")
        with col_fb_2:
            st.markdown("### 💡 High-Yield Pearls")
            st.warning(case.get("teaching_pearls", ""))

        # Save History
        res_df = pd.DataFrame([{"user": user, "block": case["block"], "score": total, "time": datetime.now()}])
        row = {"user": user, "block": case["block"], "score": score, "time": datetime.now()}
        try:
            old = pd.read_csv("responses.csv")
            res_df = pd.concat([old, res_df])
        except: pass
        res_df.to_csv("responses.csv", index=False)
            pd.concat([old, pd.DataFrame([row])]).to_csv("responses.csv", index=False)
        except:
            pd.DataFrame([row]).to_csv("responses.csv", index=False)

with col2:
    st.markdown("## 👥 Team Decision Board")
    ipa = case.get("interprofessional_answers", {})
    for role, ans in ipa.items():
        if role == profession:
            st.success(f"🟢 {role}: {ans}")
        else:
            st.info(f"⚪ {role}: {ans}")

    st.markdown("## 📖 Reference")
    ref = case.get("reference", {})
    st.write(f"{ref.get('source','-')} ({ref.get('year','-')})")

    st.markdown("---")
    st.markdown("## 📊 Performance")
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
        st.info("No history yet.")
        st.info("No history recorded yet.")
