import streamlit as st
import json, random, pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(layout="wide")

# -------------------- LOAD --------------------
@st.cache_data
def load_cases():
    with open("cases.json","r",encoding="utf-8") as f:
        return json.load(f)

cases = load_cases()

# -------------------- UTILS --------------------
def normalize(t): return t.lower().strip()

def semantic_score(a,b):
    try:
        vec = TfidfVectorizer().fit_transform([a,b])
        return cosine_similarity(vec[0:1], vec[1:2])[0][0]
    except:
        return 0

# -------------------- SCORING --------------------
def evaluate(dx, reasoning, case):

    dx_n = normalize(dx)
    ans = normalize(case["answer"])

    sim = semantic_score(dx_n, ans)

    if sim > 0.7:
        dx_score = 5
    elif sim > 0.4:
        dx_score = 3
    else:
        dx_score = 0

    # reasoning
    score = 0
    for k in case.get("key_points",[]):
        if k.lower() in reasoning.lower():
            score += 1

    if "because" in reasoning.lower():
        score += 1

    r_score = min(5, score)

    bias = []
    if len(reasoning.split()) < 5:
        bias.append("Premature closure")

    total = dx_score + r_score

    return dx_score, r_score, total, bias, sim

# -------------------- SESSION --------------------
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "easy"

def adjust(score):
    if score >= 8: return "hard"
    elif score >= 5: return "medium"
    else: return "easy"

# -------------------- TABS --------------------
tab1, tab2, tab3 = st.tabs(["🧠 Practice", "📊 Analytics", "📜 History"])

# =========================================================
# 🧠 TAB 1: PRACTICE
# =========================================================
with tab1:

    st.title("🧠 ACLR Practice")

    language = st.selectbox("Language",["English","Thai"])
    lang = "en" if language=="English" else "th"

    blocks = sorted(list(set([c["block"] for c in cases])))
    block = st.selectbox("Block",["All"]+blocks)

    mode = st.selectbox("Difficulty",["adaptive","easy","medium","hard"])

    filtered = cases

    if block!="All":
        filtered = [c for c in filtered if c["block"]==block]

    if mode!="adaptive":
        filtered = [c for c in filtered if c.get("difficulty","easy")==mode]
    else:
        filtered = [c for c in filtered if c.get("difficulty","easy")==st.session_state.difficulty]

    if not filtered:
        filtered = cases

    if "case" not in st.session_state:
        st.session_state.case = random.choice(filtered)

    if st.button("New Case"):
        st.session_state.case = random.choice(filtered)

    case = st.session_state.case

    st.subheader("Case")
    st.write(case["scenario"][lang])
    st.write(case["additional"][lang])

    dx = st.text_input("Diagnosis")
    reasoning = st.text_area("Reasoning")

    if st.button("Submit"):

        dx_s, r_s, total, bias, sim = evaluate(dx, reasoning, case)

        st.success(f"Score: {total}/10")
        st.write("Diagnosis:", dx_s)
        st.write("Reasoning:", r_s)
        st.write("Similarity:", round(sim,2))
        st.write("Bias:", bias if bias else "None")

        if mode=="adaptive":
            st.session_state.difficulty = adjust(total)
            st.info(f"Next difficulty: {st.session_state.difficulty}")

        row = {
            "time": datetime.now(),
            "case_id": case["case_id"],
            "block": case["block"],
            "difficulty": case["difficulty"],
            "score": total
        }

        df = pd.DataFrame([row])

        try:
            old = pd.read_csv("responses.csv")
            df = pd.concat([old,df])
        except:
            pass

        df.to_csv("responses.csv",index=False)

# =========================================================
# 📊 TAB 2: ANALYTICS
# =========================================================
with tab2:

    st.title("📊 Learning Analytics")

    try:
        df = pd.read_csv("responses.csv")

        st.subheader("📈 Learning Curve")
        st.line_chart(df["score"])

        st.subheader("📊 Average Score")
        st.metric("Mean Score", round(df["score"].mean(),2))

        st.subheader("📚 Performance by Block")
        st.bar_chart(df["block"].value_counts())

        st.subheader("🎯 Difficulty Distribution")
        st.bar_chart(df["difficulty"].value_counts())

    except:
        st.info("No data yet")

# =========================================================
# 📜 TAB 3: HISTORY
# =========================================================
with tab3:

    st.title("📜 Attempt History")

    try:
        df = pd.read_csv("responses.csv")

        st.dataframe(df.sort_values("time", ascending=False))

        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "aclr_results.csv"
        )

    except:
        st.info("No history yet")
