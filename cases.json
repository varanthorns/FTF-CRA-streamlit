import streamlit as st
import json, random, pandas as pd, time
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util

st.set_page_config(layout="wide")

# ===================== LOAD =====================
@st.cache_data
def load_cases():
    with open("cases.json","r",encoding="utf-8") as f:
        return json.load(f)

cases = load_cases()

@st.cache_resource
def load_bert():
    return SentenceTransformer("all-MiniLM-L6-v2")

bert_model = load_bert()

# ===================== UTILS =====================
def normalize(t): return str(t).lower().strip()

def semantic_score(a,b):
    try:
        vec = TfidfVectorizer().fit_transform([a,b])
        return cosine_similarity(vec[0:1], vec[1:2])[0][0]
    except:
        return 0

def bert_similarity(a,b):
    try:
        emb1 = bert_model.encode(a, convert_to_tensor=True)
        emb2 = bert_model.encode(b, convert_to_tensor=True)
        return float(util.cos_sim(emb1, emb2))
    except:
        return 0

# ===================== DECISION =====================
def extract_steps(reasoning):
    keys = ["because","therefore","thus","so","เนื่องจาก","ดังนั้น"]
    return [s for s in reasoning.split(".") if any(k in s.lower() for k in keys)]

# ===================== SCORING =====================
def evaluate(dx, reasoning, case, profession):

    target = case.get("interprofessional_answers",{}).get(profession, case["answer"])

    sim = semantic_score(dx, target)

    if normalize(dx) == normalize(target):
        dx_score = 5
    elif sim > 0.6:
        dx_score = 3
    else:
        dx_score = 0

    key_text = " ".join(case.get("key_points",[]))
    r_sim = bert_similarity(reasoning, key_text)

    if r_sim > 0.75:
        r_score = 5
    elif r_sim > 0.55:
        r_score = 3
    else:
        r_score = 1

    steps = extract_steps(reasoning)
    d_score = min(3,len(steps))

    total = min(10, dx_score + r_score + d_score)

    return total, dx_score, r_score, d_score, target, r_sim

# ===================== WEAKNESS AI =====================
def analyze_weakness(df, user):

    user_df = df[df["user"]==user]

    if len(user_df)<5:
        return "Not enough data"

    weak_block = user_df.groupby("block")["score"].mean().idxmin()
    weak_prof = user_df.groupby("profession")["score"].mean().idxmin()

    return f"Weakest Block: {weak_block} | Weakest Role: {weak_prof}"

# ===================== SESSION =====================
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "easy"

# ===================== UI =====================
st.title("🔥 AI Healthcare Education Platform")

user = st.text_input("Enter Name", key="user")
if not user:
    st.stop()

tab1,tab2,tab3,tab4 = st.tabs(["🧠 Practice","⏱ OSCE","⚔️ Battle","📊 Analytics"])

# ==================================================
# 🧠 PRACTICE
# ==================================================
with tab1:

    col1,col2,col3 = st.columns(3)

    with col1:
        block = st.selectbox("Block",["All"]+list(set(c["block"] for c in cases)), key="block")
    with col2:
        difficulty = st.selectbox("Difficulty",["easy","medium","hard"], key="diff")
    with col3:
        profession = st.selectbox(
            "Profession",
            ["medicine","dentistry","nursing","vet","pharmacy","public_health","ams"],
            key="prof"
        )

    filtered = [c for c in cases if (block=="All" or c["block"]==block) and c["difficulty"]==difficulty]

    if not filtered:
        st.warning("No cases")
        st.stop()

    case = random.choice(filtered)

    st.markdown("### 📋 Case")
    st.write(case["scenario"]["en"])

    dx = st.text_input("Answer", key="dx1")
    reasoning = st.text_area("Reasoning", key="rs1")

    if st.button("Submit", key="sub1"):

        total, dx_s, r_s, d_s, target, sim = evaluate(dx, reasoning, case, profession)

        st.success(f"Score: {total}/10")
        st.write("Correct:", target)

# ==================================================
# ⏱ OSCE MODE
# ==================================================
with tab2:

    st.markdown("## ⏱ OSCE Mode (Timed)")

    duration = st.slider("Time (sec)",30,180,60)

    if st.button("Start OSCE", key="osce_start"):
        st.session_state.start = time.time()

    if "start" in st.session_state:
        remaining = duration - int(time.time()-st.session_state.start)
        st.write(f"Time left: {remaining}s")

        if remaining <= 0:
            st.error("⏰ Time up!")
        else:
            case = random.choice(cases)
            st.write(case["scenario"]["en"])

            dx = st.text_input("Answer", key="osce_dx")
            reasoning = st.text_area("Reasoning", key="osce_rs")

            if st.button("Submit OSCE", key="osce_submit"):
                total, *_ = evaluate(dx, reasoning, case, "medicine")
                st.success(f"Score: {total}")

# ==================================================
# ⚔️ TEAM BATTLE
# ==================================================
with tab3:

    st.markdown("## ⚔️ Team Battle")

    players = st.text_area("Enter players (comma separated)", key="players")
    
    if players:
        players = [p.strip() for p in players.split(",")]

        case = random.choice(cases)
        st.write(case["scenario"]["en"])

        scores = {}

        for p in players:
            dx = st.text_input(f"{p} Diagnosis", key=f"{p}_dx")
            rs = st.text_area(f"{p} Reasoning", key=f"{p}_rs")

            if st.button(f"Submit {p}", key=f"{p}_btn"):
                total, *_ = evaluate(dx, rs, case, "medicine")
                scores[p] = total

        if scores:
            st.write("🏆 Results")
            st.write(sorted(scores.items(), key=lambda x: x[1], reverse=True))

# ==================================================
# 📊 ANALYTICS + WEAKNESS AI
# ==================================================
with tab4:

    try:
        df = pd.read_csv("responses.csv")

        st.line_chart(df["score"])

        st.markdown("## 🧠 Weakness AI")
        st.warning(analyze_weakness(df, user))

        st.bar_chart(df.groupby("block")["score"].mean())
        st.bar_chart(df.groupby("profession")["score"].mean())

    except:
        st.info("No data yet")
