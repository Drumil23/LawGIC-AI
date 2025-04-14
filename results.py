import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import re
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from math import pi
from dotenv import load_dotenv

# Load environment variables from .env
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

# Function for radar chart (multi-agent comparison)
def plot_radar_chart(df, agents):
    categories = ['Retrieval_Accuracy', 'Correctness', 'Completeness']
    values = []
    for agent in agents:
        values.append(df[agent].mean())

    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    values += values[:1]  # Close the circle
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), dpi=80, subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='blue', alpha=0.25)
    ax.plot(angles, values, color='blue', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)

    st.pyplot(fig)

# Streamlit layout
st.set_page_config(
    page_title="LawGIC Evaluation Dashboard",
    page_icon="📊",
    layout="wide"
)
st.title("📊 LawGIC-AI Evaluation Dashboard")
st.markdown("Upload an `.xlsx` file with **Expected** and **Actual** responses. The app will evaluate chatbot answers based on legal accuracy.")

# File upload
uploaded_file = st.file_uploader("Upload XLSX file", type=["xlsx"])
if uploaded_file:
    df = read_xlsx(uploaded_file)
    df.columns = ['ID', 'Expected', 'Actual'] + list(df.columns[3:])
    st.success("✅ File uploaded and parsed successfully.")
    st.dataframe(df.head())

    # Grading Threshold Sliders
    st.sidebar.title("Grading Controls")
    retrieval_threshold = st.sidebar.slider("Set Retrieval Accuracy Threshold", 0.0, 1.0, 0.6)
    correctness_threshold = st.sidebar.slider("Set Correctness Threshold", 0.0, 1.0, 0.7)
    completeness_threshold = st.sidebar.slider("Set Completeness Threshold", 0.0, 1.0, 0.75)

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

        # Apply filters based on user-defined thresholds
        filtered_df = df[
            (df['Retrieval_Accuracy'] >= retrieval_threshold) &
            (df['Correctness'] >= correctness_threshold) &
            (df['Completeness'] >= completeness_threshold)
        ]

        st.subheader("Filtered Data Based on Thresholds")
        st.dataframe(filtered_df)

        # Charts
        st.subheader("Evaluation Scores Overview")
        st.line_chart(df[["Retrieval_Accuracy", "Correctness", "Completeness"]])

        # Bar chart for score distribution
        def plot_bar_chart(data, column_name):
            fig, ax = plt.subplots()
            ax.bar(data['ID'], data[column_name], color="skyblue")
            ax.set_xlabel("ID")
            ax.set_ylabel(f"{column_name} Score")
            ax.set_title(f"Distribution of {column_name}")
            st.pyplot(fig)

        # Plot individual scores
        plot_bar_chart(df, "Retrieval_Accuracy")
        plot_bar_chart(df, "Correctness")
        plot_bar_chart(df, "Completeness")

        # Heatmap of evaluation scores
        st.subheader("Heatmap of Scores")
        corr = df[['Retrieval_Accuracy', 'Correctness', 'Completeness']].corr()
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)

        # Boxplot for score distribution
        st.subheader("Boxplot of Scores")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.boxplot(data=df[['Retrieval_Accuracy', 'Correctness', 'Completeness']], ax=ax)
        st.pyplot(fig)

        # Pie chart for score threshold distribution
        st.subheader("Pie Chart of Scores Above Threshold")
        above_threshold = [
            (df['Retrieval_Accuracy'] >= retrieval_threshold).sum(),
            (df['Correctness'] >= correctness_threshold).sum(),
            (df['Completeness'] >= completeness_threshold).sum()
        ]
        labels = ['Retrieval Accuracy', 'Correctness', 'Completeness']
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(above_threshold, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)

        # Radar Chart for Multi-Agent Comparison (replace with actual agents)
        st.subheader("📊 Multi-Agent Comparison")
        plot_radar_chart(df, ['Retrieval_Accuracy', 'Correctness', 'Completeness'])

        # Row-by-row inspection
        st.subheader("Inspect Individual Evaluation")
        index = st.number_input("Select Row", 0, len(df) - 1, 0)
        st.text_area("Expected Response", df.loc[index, "Expected"], height=150)
        st.text_area("Chatbot Response", df.loc[index, "Actual"], height=150)
        st.text(f"Evaluation Comments: {df.loc[index, 'LLM_Comments']}")
        st.text(f"Retrieval Accuracy: {df.loc[index, 'Retrieval_Accuracy']}")
        st.text(f"Correctness: {df.loc[index, 'Correctness']}")
        st.text(f"Completeness: {df.loc[index, 'Completeness']}")