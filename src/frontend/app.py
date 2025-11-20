# src/frontend/app.py

from __future__ import annotations

import sys
from pathlib import Path

# ---- Make project root and src/ importable ----
# app.py 路径： .../VisGenAIGroup7/src/frontend/app.py
# parents[2] = .../VisGenAIGroup7
ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"

for p in (ROOT_DIR, SRC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
# ----------------------------------------------

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.backend.pipeline.workflow import run_pipeline
from src.shared.schemas import PipelineState

load_dotenv()

st.set_page_config(page_title="Project Baseline", page_icon="📊", layout="wide")

st.title("📊 Project Baseline - Prompt-to-Vis Agent")

SAMPLE_PROMPTS = [
    "Compare the average IMDB rating for each Genre across the whole dataset.",
    "Show how total Revenue (Millions) changed year by year between 2007 and 2016.",
    "Plot Runtime (Minutes) versus Rating for every movie, coloring points by Genre.",
    "Display the cumulative count of movie releases over Year as an area chart.",
    "Build a heatmap showing the number of films for each Genre–Year combination.",
    "What share of total Revenue (Millions) does each Genre contribute? Show as a pie or donut chart.",
    "Display a boxplot of Runtime (Minutes) grouped by Genre to compare runtime distributions.",
]


# =========================
# Session state init
# =========================

if "provider" not in st.session_state:
    # "groq" or "openai"
    st.session_state.provider = "groq"

if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")

if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")

if "df" not in st.session_state:
    st.session_state.df = None

if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

if "selected_model_name" not in st.session_state:
    st.session_state.selected_model_name = ""


# =========================
# Sidebar: controls
# =========================

st.sidebar.header("LLM & Data Settings")

# --- Provider selection ---

provider_label_to_value = {
    "Groq": "groq",
    "OpenAI": "openai",
}
provider_value_to_label = {v: k for k, v in provider_label_to_value.items()}

current_provider_label = provider_value_to_label.get(
    st.session_state.provider, "Groq"
)

selected_provider_label = st.sidebar.selectbox(
    "LLM Provider:",
    options=list(provider_label_to_value.keys()),
    index=list(provider_label_to_value.keys()).index(current_provider_label),
)

st.session_state.provider = provider_label_to_value[selected_provider_label]
provider = st.session_state.provider  # "groq" or "openai"


# --- Model selection per provider ---

groq_model_options = {
    "Llama 3.3 70B (Groq, Recommended)": "llama-3.3-70b-versatile",
    "Llama 3.1 8B (Groq, Fast)": "llama-3.1-8b-instant",
}

openai_model_options = {
    # 你可以按需调整这些默认模型名
    "gpt-4o-mini (OpenAI, Recommended)": "gpt-4o-mini",
    "gpt-4o (OpenAI, Better quality)": "gpt-4o",
}

if provider == "groq":
    model_label = st.sidebar.selectbox(
        "Groq Model:",
        options=list(groq_model_options.keys()),
        index=0,
    )
    selected_model_name = groq_model_options[model_label]
else:
    model_label = st.sidebar.selectbox(
        "OpenAI Model:",
        options=list(openai_model_options.keys()),
        index=0,
    )
    selected_model_name = openai_model_options[model_label]

st.session_state.selected_model_name = selected_model_name


# --- API key per provider ---

if provider == "groq":
    api_key_input = st.sidebar.text_input(
        "Groq API Key:",
        type="password",
        value=st.session_state.groq_api_key,
    )
    st.session_state.groq_api_key = api_key_input
    current_api_key = st.session_state.groq_api_key
else:
    api_key_input = st.sidebar.text_input(
        "OpenAI API Key:",
        type="password",
        value=st.session_state.openai_api_key,
    )
    st.session_state.openai_api_key = api_key_input
    current_api_key = st.session_state.openai_api_key

st.sidebar.markdown("---")

# --- Data upload / sample ---

uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

if st.sidebar.button("Load Sample IMDB Data"):
    try:
        st.session_state.df = pd.read_csv("imdb_sample.csv")
        st.sidebar.success("Sample data loaded!")
    except FileNotFoundError:
        st.sidebar.error("Sample file not found (imdb_sample.csv)")

if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.sidebar.success(f"Uploaded: {uploaded_file.name}")

# Dataset info
if st.session_state.df is not None:
    st.sidebar.markdown("### Dataset Info")
    st.sidebar.write(f"Rows: {len(st.session_state.df)}")
    st.sidebar.write(f"Columns: {len(st.session_state.df.columns)}")

    with st.sidebar.expander("View Columns"):
        st.write(list(st.session_state.df.columns))

st.sidebar.markdown("---")

# Clear helpers
if st.sidebar.button("Clear Data"):
    st.session_state.df = None
    st.session_state.pipeline_result = None
    st.session_state.user_query = ""
    st.rerun()


# =========================
# Main layout
# =========================

# 提示当前 provider
st.caption(f"Current provider: **{provider_label_to_value.keys().__iter__().__next__() if False else selected_provider_label}**")

if not current_api_key:
    st.info(f"Please enter your {selected_provider_label} API key in the sidebar to start.")
elif st.session_state.df is None:
    st.info("Please upload a CSV file or load the sample IMDB data to start.")
else:
    # Data preview + stats
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Dataset Preview")
        st.dataframe(st.session_state.df.head(), use_container_width=True)

    with col2:
        st.subheader("Quick Stats")
        try:
            st.write(st.session_state.df.describe())
        except Exception:
            st.write("No numeric columns available for describe().")

    st.markdown("---")

    # User question → Prompt-to-Vis
    st.subheader("Ask for a Chart")
    st.markdown("**Sample prompts** — click to autofill the query box.")
    for idx, prompt_text in enumerate(SAMPLE_PROMPTS):
        if st.button(prompt_text, key=f"sample_prompt_{idx}"):
            st.session_state.user_query = prompt_text
            st.rerun()

    st.markdown("---")

    user_query = st.text_input(
        "Describe the chart you want (e.g., 'Compare average rating by genre over time' or 'Create a bar chart of movie genres'):",
        value=st.session_state.user_query,
    )
    st.session_state.user_query = user_query

    run_clicked = st.button("Run Prompt-to-Vis Pipeline")

    if run_clicked and user_query.strip():
        with st.spinner(f"Running Prompt-to-Vis pipeline via {selected_provider_label}..."):
            try:
                result = run_pipeline(
                    df=st.session_state.df,
                    user_query=user_query,
                    provider=provider,  # "groq" or "openai"
                    model_name=st.session_state.selected_model_name,
                    api_key=current_api_key,
                    dataset_name=getattr(uploaded_file, "name", "uploaded_dataset")
                    if uploaded_file is not None
                    else "sample_dataset",
                )
                st.session_state.pipeline_result = result
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.session_state.pipeline_result = None

    # Show results if available
    if st.session_state.pipeline_result is not None:
        result = st.session_state.pipeline_result

        st.subheader("Recommended Chart")

        spec = result["spec"]
        if spec:
            # data 由 Streamlit 绑定，spec 中不包含 "data"
            st.vega_lite_chart(
                st.session_state.df,
                spec,
                use_container_width=True,
            )
        else:
            st.warning("No Vega-Lite spec was produced by the pipeline.")

        # Pipeline internals
        with st.expander("View Pipeline State (Step Outputs)"):
            state: PipelineState = result["state"]
            st.json(state.model_dump(mode="json", exclude={"final_spec"}))

    # TODO[ui]:
    #   - Refactor this monolithic app into reusable components under src/frontend/components/
    #   - Add a multi-step panel with JSON editors per step.
    #   - Allow re-running from an edited step (using a future run_pipeline_from_step()).
    #   - This will likely require a LangChain/LangGraph-based orchestrator in the backend.
