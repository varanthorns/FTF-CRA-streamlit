import streamlit as st
import json, random, pandas as pd
from datetime import datetime
import numpy as np
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(layout="wide")

# ================= LOAD =================
@st.cache_data
def load_cases():
    with open("cases.json","r",encoding="utf-8") as f:
        return json.load(f)

cases = load_cases()

# ================= UTILS =================
def normalize(t): return str(t).lower().strip()

def semantic_score(a,b):
    try:
        vec = TfidfVectorizer().fit_transform([a,b])
        return cosine_similarity(vec[0:1], vec[1:2])[0][0]
    except:
        return 0

# ================= SCORING =================
def evaluate(dx, reasoning, case):

    sim = semantic_score(dx, case["answer"])
    dx_score = 5 if sim>0.7 else 3 if sim>0.4 else 0

    r_score = sum([1 for k in case.get("key_points",[]) if k.lower() in reasoning.lower()])
    r_score = min(5, r_score)

    total = dx_score + r_score
    return total

# ================= STATS =================
def compute_stats(df):

    scores = df["score"].values
    mid = len(scores)//2
    early, late = scores[:mid], scores[mid:]

    result = {
        "mean": np.mean(scores),
        "sd": np.std(scores),
        "n": len(scores)
    }

    if len(early)>1 and len(late)>1:
        t,p = stats.ttest_ind(late,early)
        result["p"] = p

    return result

# ================= XP SYSTEM =================
def compute_xp(score):
    return score * 10

def compute_level(xp):
    return xp // 100

# ================= UI =================
st.title("🧠 ACLR Platform (Full System)")

user_id = st.text_input("Enter Student ID")

if not user_id:
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧠 Practice",
    "📊 Analytics",
    "📜 History",
    "🏆 Leaderboard",
    "👨‍🏫 Instructor"
])

# ================= PRACTICE =================
with tab1:

    blocks = sorted(list(set([c["block"] for c in cases])))
    block = st.selectbox("Block",["All"]+blocks)

    filtered = cases if block=="All" else [c for c in cases if c["block"]==block]

    if "case" not in st.session_state:
        st.session_state.case = random.choice(filtered)

    if st.button("New Case"):
        st.session_state.case = random.choice(filtered)

    case = st.session_state.case

    st.write(case["scenario"]["en"])

    dx = st.text_input("Diagnosis")
    reasoning = st.text_area("Reasoning")

    if st.button("Submit"):

        score = evaluate(dx, reasoning, case)
        xp = compute_xp(score)

        st.success(f"Score: {score}/10 | XP: {xp}")

        row = {
            "user": user_id,
            "time": datetime.now(),
            "block": case["block"],
            "score": score,
            "xp": xp
        }

        df = pd.DataFrame([row])

        try:
            old = pd.read_csv("responses.csv")
            df = pd.concat([old,df])
        except:
            pass

        df.to_csv("responses.csv",index=False)

# ================= ANALYTICS =================
with tab2:

    try:
        df = pd.read_csv("responses.csv")

        user_df = df[df["user"]==user_id]

        st.metric("Avg Score", round(user_df["score"].mean(),2))
        st.line_chart(user_df["score"])

    except:
        st.info("No data")

# ================= HISTORY =================
with tab3:

    try:
        df = pd.read_csv("responses.csv")
        st.dataframe(df[df["user"]==user_id])
    except:
        st.info("No data")

# ================= LEADERBOARD =================
with tab4:

    try:
        df = pd.read_csv("responses.csv")

        leaderboard = df.groupby("user").agg({
            "xp":"sum",
            "score":"mean"
        }).sort_values("xp",ascending=False)

        st.subheader("🏆 Leaderboard")
        st.dataframe(leaderboard)

    except:
        st.info("No data")

# ================= INSTRUCTOR =================
with tab5:

    try:
        df = pd.read_csv("responses.csv")

        st.subheader("Class Overview")

        stats = compute_stats(df)
        st.write(stats)

        st.line_chart(df["score"])

        st.subheader("By Student")
        st.bar_chart(df.groupby("user")["score"].mean())

        st.subheader("Weak Topics")
        st.bar_chart(df.groupby("block")["score"].mean())

    except:
        st.info("No data")

