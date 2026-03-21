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

# -------------------- SYNONYMS --------------------
SYNONYMS = {
    "myocardial infarction": ["mi","heart attack","acute coronary syndrome"],
    "stroke": ["cva","cerebrovascular accident"],
    "diabetes mellitus": ["diabetes"],
    "pulmonary embolism": ["pe"],
}

def normalize(t): return t.lower().strip()

# -------------------- SEMANTIC SIM --------------------
def semantic_score(user, answer):
    texts = [user, answer]
    vec = TfidfVectorizer().fit_transform(texts)
    sim = cosine_similarity(vec[0:1], vec[1:2])[0][0]
    return sim

# -------------------- NLP REASONING --------------------
def reasoning_analysis(text, case):
    text = normalize(text)
    score = 0
    explanation = []

    # keyword check
    for k in case.get("key_points",[]):
        if k.lower() in text:
            score += 1
            explanation.append(f"✔ used key feature: {k}")

    # structure check
    if "because" in text or "เนื่องจาก" in text:
        score += 1
        explanation.append("✔ shows causal reasoning")

    if "therefore" in text or "ดังนั้น" in text:
        score += 1
        explanation.append("✔ shows conclusion logic")

    return score, explanation

# -------------------- SCORING --------------------
def evaluate(diagnosis, reasoning, case):

    diagnosis = normalize(diagnosis)
    answer = normalize(case["answer"])

    # --- semantic similarity ---
    sim = semantic_score(diagnosis, answer)

    if sim > 0.7:
        dx_score = 5
    elif sim > 0.4:
        dx_score = 3
    elif any(a in diagnosis for a in SYNONYMS.get(answer,[])):
        dx_score = 3
    else:
        dx_score = 0

    # --- reasoning ---
    r_score_raw, r_explain = reasoning_analysis(reasoning, case)

    if r_score_raw >= 3:
        r_score = 5
    elif r_score_raw == 2:
        r_score = 3
    elif r_score_raw == 1:
        r_score = 2
    else:
        r_score = 0

    # --- bias ---
    bias = []
    if len(reasoning.split()) < 5:
        bias.append("Premature closure")
    if "first" in reasoning:
        bias.append("Anchoring bias")

    total = dx_score + r_score

    feedback = f"""
Correct diagnosis: {case['answer']}

Similarity score: {round(sim,2)}

Reasoning insights:
{chr(10).join(r_explain)}

Improvement:
- Include more key clinical features
- Structure reasoning clearly
"""

    return {
        "dx": dx_score,
        "reason": r_score,
        "total": total,
        "bias": bias,
        "feedback": feedback
    }

# -------------------- ADAPTIVE --------------------
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "easy"

def adjust(score):
    if score >= 8: return "hard"
    elif score >= 5: return "medium"
    else: return "easy"

# -------------------- UI --------------------
st.title("🧠 ACLR Advanced Offline Trainer")

language = st.selectbox("Language",["English","Thai"])
lang = "en" if language=="English" else "th"

blocks = sorted(list(set([c["block"] for c in cases])))
block = st.selectbox("Block",["All"]+blocks)

difficulty_select = st.selectbox(
    "Difficulty Mode",
    ["adaptive","easy","medium","hard"]
)

# filter
filtered = cases
if block!="All":
    filtered = [c for c in filtered if c["block"]==block]

if difficulty_select!="adaptive":
    filtered = [c for c in filtered if c.get("difficulty","easy")==difficulty_select]
else:
    filtered = [c for c in filtered if c.get("difficulty","easy")==st.session_state.difficulty]

if "case" not in st.session_state:
    st.session_state.case = random.choice(filtered)

if st.button("New case"):
    st.session_state.case = random.choice(filtered)

case = st.session_state.case

# -------------------- DISPLAY --------------------
st.subheader("Case")
st.write(case["scenario"][lang])
st.write(case["additional"][lang])

diagnosis = st.text_input("Diagnosis")
reasoning = st.text_area("Reasoning")

# -------------------- SUBMIT --------------------
if st.button("Submit"):

    result = evaluate(diagnosis, reasoning, case)

    st.success(f"Score: {result['total']}/10")

    st.write("Diagnosis:", result["dx"])
    st.write("Reasoning:", result["reason"])

    st.write("Bias:", result["bias"] if result["bias"] else "None")

    st.write("Feedback")
    st.write(result["feedback"])

    # adaptive
    if difficulty_select=="adaptive":
        st.session_state.difficulty = adjust(result["total"])
        st.info(f"Next difficulty: {st.session_state.difficulty}")

    # save
    data = {
        "time": datetime.now(),
        "case_id": case["case_id"],
        "block": case["block"],
        "difficulty": case["difficulty"],
        "score": result["total"]
    }

    df = pd.DataFrame([data])

    try:
        old = pd.read_csv("responses.csv")
        df = pd.concat([old,df],ignore_index=True)
    except:
        pass

    df.to_csv("responses.csv",index=False)

# -------------------- DASHBOARD --------------------
st.divider()
st.header("📊 Dashboard")

try:
    df = pd.read_csv("responses.csv")

    st.line_chart(df["score"])

    st.write("Average score:", round(df["score"].mean(),2))

    st.bar_chart(df["block"].value_counts())

    st.subheader("History")
    st.dataframe(df.tail(10))

except:
    st.info("No data yet")
