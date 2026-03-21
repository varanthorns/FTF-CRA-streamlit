import streamlit as st
import json
import random
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

# -------------------- LOAD CASE --------------------
@st.cache_data
def load_cases():
    with open("cases.json", "r", encoding="utf-8") as f:
        return json.load(f)

cases = load_cases()

# -------------------- MEDICAL SYNONYMS --------------------
SYNONYMS = {
    "myocardial infarction": ["mi", "heart attack", "acute coronary syndrome"],
    "pulmonary embolism": ["pe", "embolism"],
    "diabetes mellitus": ["diabetes"],
    "stroke": ["cva", "cerebrovascular accident"],
    "pneumonia": ["lung infection"],
    "septic shock": ["sepsis"],
    "hyperthyroidism": ["thyrotoxicosis"],
}

# -------------------- HELPER --------------------
def normalize(text):
    return text.lower().strip()

def expand_terms(term):
    term = normalize(term)
    expanded = [term]
    if term in SYNONYMS:
        expanded += SYNONYMS[term]
    return expanded

# -------------------- SCORING ENGINE --------------------
def evaluate_local_advanced(diagnosis, reasoning, case):

    diagnosis = normalize(diagnosis)
    reasoning = normalize(reasoning)
    answer = normalize(case["answer"])

    # -------- Diagnosis Matching --------
    expanded_answers = expand_terms(answer)

    if any(a in diagnosis for a in expanded_answers):
        diagnosis_score = 5
    else:
        # partial match
        words = answer.split()
        overlap = sum([1 for w in words if w in diagnosis])
        if overlap >= 2:
            diagnosis_score = 3
        elif overlap == 1:
            diagnosis_score = 2
        else:
            diagnosis_score = 0

    # -------- Differential Matching --------
    diff_score = 0
    for d in case.get("distractor", "").split():
        if d.lower() in diagnosis:
            diff_score += 1

    if diff_score > 0 and diagnosis_score == 0:
        diagnosis_score = 2  # partial credit

    # -------- Reasoning Scoring --------
    keywords = case.get("key_points", [])
    weights = {k: 2 for k in keywords}

    score_sum = 0
    for k, w in weights.items():
        if k.lower() in reasoning:
            score_sum += w

    if score_sum >= 4:
        reasoning_score = 5
    elif score_sum >= 2:
        reasoning_score = 3
    elif score_sum > 0:
        reasoning_score = 2
    else:
        reasoning_score = 0

    # -------- Bias Detection --------
    bias = []

    if len(reasoning.split()) < 5:
        bias.append("Premature closure")

    if "first" in reasoning or "initial" in reasoning:
        bias.append("Anchoring bias")

    if "definitely" in reasoning or "sure" in reasoning:
        bias.append("Overconfidence bias")

    # -------- Total --------
    total = diagnosis_score + reasoning_score

    feedback = f"Expected: {case['answer']}"

    return {
        "diagnosis_score": diagnosis_score,
        "reasoning_score": reasoning_score,
        "total_score": total,
        "bias_detected": bias,
        "feedback": feedback
    }

# -------------------- ADAPTIVE DIFFICULTY --------------------
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "easy"

def adjust_difficulty(score):
    if score >= 8:
        return "hard"
    elif score >= 5:
        return "medium"
    else:
        return "easy"

# -------------------- UI --------------------
st.title("🧠 ACLR Offline Intelligent Trainer")

language = st.selectbox("Language", ["English", "Thai"])
lang_key = "en" if language == "English" else "th"

blocks = sorted(list(set([c["block"] for c in cases])))
selected_block = st.selectbox("Block", ["All"] + blocks)

filtered_cases = cases if selected_block == "All" else [c for c in cases if c["block"] == selected_block]

# Filter by difficulty
filtered_cases = [c for c in filtered_cases if c.get("difficulty", "easy") == st.session_state.difficulty]

if not filtered_cases:
    filtered_cases = cases

if "case" not in st.session_state:
    st.session_state.case = random.choice(filtered_cases)

if st.button("🔄 New Case"):
    st.session_state.case = random.choice(filtered_cases)

case = st.session_state.case

# -------------------- DISPLAY --------------------
st.subheader("Case")
st.write(case["scenario"][lang_key])
st.write(case["additional"][lang_key])

diagnosis = st.text_input("Diagnosis (full word)")
reasoning = st.text_area("Reasoning")

# -------------------- SUBMIT --------------------
if st.button("Submit"):

    result = evaluate_local_advanced(diagnosis, reasoning, case)

    st.success(f"Score: {result['total_score']} / 10")

    st.write("### Breakdown")
    st.write(f"Diagnosis: {result['diagnosis_score']}/5")
    st.write(f"Reasoning: {result['reasoning_score']}/5")

    st.write("### Cognitive Bias")
    if result["bias_detected"]:
        for b in result["bias_detected"]:
            st.write("-", b)
    else:
        st.write("None")

    st.write("### Feedback")
    st.write(result["feedback"])

    # -------- ADAPTIVE --------
    st.session_state.difficulty = adjust_difficulty(result["total_score"])

    st.info(f"Next difficulty: {st.session_state.difficulty}")

    # -------- SAVE --------
    data = {
        "time": datetime.now(),
        "case_id": case["case_id"],
        "block": case["block"],
        "difficulty": case["difficulty"],
        "user_diagnosis": diagnosis,
        "reasoning": reasoning,
        "score": result["total_score"]
    }

    df = pd.DataFrame([data])

    try:
        old = pd.read_csv("responses.csv")
        df = pd.concat([old, df], ignore_index=True)
    except:
        pass

    df.to_csv("responses.csv", index=False)
