import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Configure Gemini API
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash-latest",
        system_instruction=(
            "You are a legal evaluation AI. Only return JSON as instructed. "
            "Never respond with explanations or text outside the JSON."
        )
    )
else:
    st.error("❌ API key not found. Please set GOOGLE_API_KEY in your .env file.")
    st.stop()

# Function to read XLSX
def read_xlsx(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        if df.empty or df.shape[1] < 3:
            raise ValueError("XLSX must contain at least 3 columns.")
        return df
    except Exception as e:
        st.error(f"❌ Error reading Excel file: {e}")
        st.stop()

# Streamlit layout
st.set_page_config(page_title="LLM Grading Dashboard (XLSX)", layout="wide")
st.title("📊 LawGIC-AI Evaluation Dashboard")
st.markdown("Upload an `.xlsx` file with **Expected** and **Actual** responses. The app will evaluate chatbot answers based on legal accuracy.")

# File upload
uploaded_file = st.file_uploader("📂 Upload XLSX file", type=["xlsx"])
if uploaded_file:
    df = read_xlsx(uploaded_file)
    df.columns = ['ID', 'Expected', 'Actual'] + list(df.columns[3:])
    st.success("✅ File uploaded and parsed successfully.")
    st.dataframe(df.head())

    if st.button("🚀 Run Evaluation"):
        progress = st.progress(0)
        results = []
        total = len(df)

        for i, row in enumerate(df.itertuples(index=False), 1):
            prompt = f"""
You are a legal expert AI evaluating chatbot performance.

You will be given:

• An **Expected Response** – the legally correct answer.
• An **Actual Response** – the chatbot's answer.

Evaluate on:
1. Retrieval Accuracy (Did it refer to correct laws/sections?)
2. Response Correctness (Is the legal advice correct?)
3. Response Completeness (Did it cover all key points?)

Return ONLY JSON like:
{{
  "retrieval_accuracy": float (0.0 to 1.0),
  "response_correctness": float (0.0 to 1.0),
  "response_completeness": float (0.0 to 1.0),
  "comments": "brief explanation"
}}

---

Expected Response:
{row.Expected}

Chatbot Response:
{row.Actual}
"""
            try:
                response = model.generate_content(prompt)
                json_text = re.search(r'{.*}', response.text, re.DOTALL).group()
                parsed = json.loads(json_text)
            except Exception as e:
                parsed = {
                    "retrieval_accuracy": 0.0,
                    "response_correctness": 0.0,
                    "response_completeness": 0.0,
                    "comments": f"Parsing error or invalid format"
                }

            results.append(parsed)
            progress.progress(i / total)

        # Attach results
        df["Retrieval_Accuracy"] = [r["retrieval_accuracy"] for r in results]
        df["Correctness"] = [r["response_correctness"] for r in results]
        df["Completeness"] = [r["response_completeness"] for r in results]
        df["LLM_Comments"] = [r["comments"] for r in results]

        st.success("✅ Evaluation complete!")
        st.dataframe(df)

        # Charts
        st.subheader("Score Overview")
        st.line_chart(df[["Retrieval_Accuracy", "Correctness", "Completeness"]])

        # Row-by-row inspection
        st.subheader("🔍 Inspect Individual Evaluation")
        index = st.number_input("Select Row", 0, len(df) - 1, 0)
        st.text_area("Expected Response", df.loc[index, "Expected"], height=150)
        st.text_area("Chatbot Response", df.loc[index, "Actual"], height=150)
        st.text(f"Evaluation Comments: {df.loc[index, 'LLM_Comments']}")
        st.text(f"Retrieval Accuracy: {df.loc[index, 'Retrieval_Accuracy']}")
        st.text(f"Correctness: {df.loc[index, 'Correctness']}")
        st.text(f"Completeness: {df.loc[index, 'Completeness']}")
