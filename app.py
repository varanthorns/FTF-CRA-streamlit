import streamlit as st
import json
import random
import pandas as pd
from datetime import datetime

# Load cases
with open("cases.json", "r", encoding="utf-8") as f:
    cases = json.load(f)

st.title("🧠 ACLR Clinical Reasoning Trainer")

# Language selector
language = st.selectbox("Language / ภาษา", ["en", "th"])

# Random case
if "case" not in st.session_state:
    st.session_state.case = random.choice(cases)

case = st.session_state.case

# Show case
st.subheader("Case")
st.write(case["scenario"][language])
st.write(case["additional"][language])

# User input
diagnosis = st.text_input("Diagnosis / การวินิจฉัย")
reasoning = st.text_area("Reasoning / เหตุผล")

# Submit
if st.button("Submit / ส่งคำตอบ"):

    # Simple scoring (placeholder)
    correct = case["answer"].lower() in diagnosis.lower()

    score = 10 if correct else 5

    feedback = "Correct!" if correct else f"Expected: {case['answer']}"

    st.success(f"Score: {score}/10")
    st.write(feedback)

    # Save data
    data = {
        "time": datetime.now(),
        "case_id": case["case_id"],
        "diagnosis": diagnosis,
        "reasoning": reasoning,
        "score": score,
        "language": language
    }

    df = pd.DataFrame([data])

    try:
        old = pd.read_csv("responses.csv")
        df = pd.concat([old, df], ignore_index=True)
    except:
        pass

    df.to_csv("responses.csv", index=False)

    # New case button
    if st.button("Next Case"):
        st.session_state.case = random.choice(cases)
