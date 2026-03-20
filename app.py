import streamlit as st
import json
import random
import pandas as pd
from datetime import datetime
import os
from openai import OpenAI

# -------------------- CONFIG --------------------
st.set_page_config(page_title="ACLR Clinical Reasoning", layout="wide")

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------- LOAD DATA --------------------
@st.cache_data
def load_cases():
    with open("cases.json", "r", encoding="utf-8") as f:
        return json.load(f)

cases = load_cases()

# -------------------- UI HEADER --------------------
st.title("🧠 Adaptive Clinical Reasoning Trainer (ACLR)")

# Language selector
language = st.selectbox(
    "Select Language / เลือกภาษา",
    ["English", "Thai"]
)

lang_key = "en" if language == "English" else "th"

# -------------------- BLOCK FILTER --------------------
blocks = sorted(list(set([c["block"] for c in cases])))
selected_block = st.selectbox(
    "Select Clinical Block / เลือกหมวดวิชา",
    ["All"] + blocks
)

# Filter cases
filtered_cases = cases if selected_block == "All" else [c for c in cases if c["block"] == selected_block]

# -------------------- CASE SELECTION --------------------
if "case" not in st.session_state:
    st.session_state.case = random.choice(filtered_cases)

if st.button("🔄 New Case / เคสใหม่"):
    st.session_state.case = random.choice(filtered_cases)

case = st.session_state.case

# -------------------- DISPLAY CASE --------------------
st.subheader("📋 Clinical Scenario")

st.write(case["scenario"][lang_key])
st.write(case["additional"][lang_key])

# -------------------- USER INPUT --------------------
st.subheader("✍️ Your Response")

diagnosis = st.text_input(
    "Enter full diagnosis (no abbreviations) / ใส่การวินิจฉัยแบบเต็ม"
)

reasoning = st.text_area(
    "Explain your clinical reasoning / อธิบายเหตุผลทางคลินิก",
    height=150
)

confidence = st.slider(
    "Confidence level / ความมั่นใจ (%)",
    0, 100, 50
)

# -------------------- AI SCORING FUNCTION --------------------
def evaluate_with_ai(diagnosis, reasoning, case, language):

    prompt = f"""
You are a medical education expert.

Evaluate the student's response.

CASE:
{case["scenario"]["en"]}
{case["additional"]["en"]}

EXPECTED DIAGNOSIS:
{case["answer"]}

STUDENT RESPONSE:
Diagnosis: {diagnosis}
Reasoning: {reasoning}

SCORING RUBRIC:

1. Diagnosis Accuracy (0-5)
- 5 = correct
- 3-4 = partially correct
- 1-2 = incorrect but related
- 0 = completely wrong

2. Clinical Reasoning Quality (0-5)
- logical progression
- use of key features
- avoidance of errors

3. Cognitive Bias Detection:
Check for:
- Anchoring bias
- Premature closure
- Availability bias

Return STRICT JSON:
{{
  "diagnosis_score": int,
  "reasoning_score": int,
  "total_score": int,
  "bias_detected": ["..."],
  "feedback": "..."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content


# -------------------- SUBMIT --------------------
if st.button("✅ Submit / ส่งคำตอบ"):

    if diagnosis.strip() == "":
        st.warning("Please enter diagnosis")
        st.stop()

    with st.spinner("Analyzing clinical reasoning..."):

        try:
            result = evaluate_with_ai(diagnosis, reasoning, case, language)

            import json as js
            parsed = js.loads(result)

            st.success(f"🎯 Total Score: {parsed['total_score']} / 10")

            st.write("### 📊 Score Breakdown")
            st.write(f"- Diagnosis: {parsed['diagnosis_score']} / 5")
            st.write(f"- Reasoning: {parsed['reasoning_score']} / 5")

            st.write("### 🧠 Cognitive Bias Detected")
            if parsed["bias_detected"]:
                for b in parsed["bias_detected"]:
                    st.write(f"- {b}")
            else:
                st.write("No significant bias detected")

            st.write("### 💬 Feedback")
            st.write(parsed["feedback"])

            # ---------------- SAVE DATA ----------------
            data = {
                "time": datetime.now(),
                "case_id": case["case_id"],
                "block": case["block"],
                "diagnosis": diagnosis,
                "reasoning": reasoning,
                "confidence": confidence,
                "score_total": parsed["total_score"],
                "diagnosis_score": parsed["diagnosis_score"],
                "reasoning_score": parsed["reasoning_score"],
                "bias": ", ".join(parsed["bias_detected"]),
                "language": language
            }

            df = pd.DataFrame([data])

            try:
                old = pd.read_csv("responses.csv")
                df = pd.concat([old, df], ignore_index=True)
            except:
                pass

            df.to_csv("responses.csv", index=False)

        except Exception as e:
            st.error(f"Error: {e}")
