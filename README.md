# VisGenAIGroup7 — Transparent Prompt-to-Vis Pipeline Demo

A prototype system that transforms **natural language questions** into a fully **transparent 6-step visualization reasoning pipeline**, and finally into an interpretable **Vega-Lite chart**.

This project is built for **CS7295: Data Visualization & Generative AI** at Northeastern University.

Unlike typical “black-box” Prompt-to-Vis tools, this system exposes and visualizes each reasoning step, allowing users to **edit intermediate results**, **rerun downstream steps**, and understand exactly how a chart is constructed.

---

## ✨ Features

### 🔎 Transparent 6-Step Pipeline

The system decomposes user prompts into six interpretable reasoning steps:

1. **Column Selection**  
2. **Intent Classification**  
3. **Aggregation & Filtering**  
4. **Plot Type Recommendation**  
5. **Encoding Assignment**  
6. **Vega-Lite Spec Generation**

Each step produces:

- Human-readable reasoning  
- Structured JSON output  
- Editable fields  

---

### 🤖 Choose Your LLM Provider

Users can dynamically choose the backend model in the **Streamlit sidebar**:

- **OpenAI API**  
- **Groq API**

Then select from the supported models (e.g., Llama 3.3 70B, Llama 3.1 8B, GPT‑4.x / GPT‑5).

---

### 📊 Automatic Vega-Lite Visualizations

The final pipeline output is transformed into a full **Vega-Lite specification** and rendered directly in Streamlit via Altair.

---

### 🧩 Modular Architecture (For Developers)

- **Frontend**: Streamlit  
- **Backend**: LangChain + LangGraph  
- **Data Models**: Pydantic schemas  
- **Charts**: Vega-Lite  

This structure keeps the codebase clean, modular, and AI-friendly for vibe coding.

---

## 🚀 Quick Start

### 1. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. API Keys

You may use **OpenAI** or **Groq**.

You can provide API keys in one of two ways:

#### Option A — via Streamlit sidebar  
Paste your API key(s) into the sidebar input fields.

#### Option B — using `.streamlit/secrets.toml`

Copy the example file:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

And fill in:

```toml
OPENAI_API_KEY = "your-openai-key"
GROQ_API_KEY = "your-groq-key"
```

---

### 4. Run the app

```bash
streamlit run src/frontend/app.py
```

---

## 🧭 Usage

1. Open the app in your browser.  
2. In the **sidebar**, choose:
   - API Provider (**OpenAI** / **Groq**)  
   - Model  
   - (Optional) API key  
3. Upload a CSV file or load a sample dataset.  
4. Enter a natural language question, such as:
   - “Which movie genres earn the most?”  
   - “Show me revenue over time.”  
5. The system will:
   - Run all **6 transparent reasoning steps**  
   - Display structured reasoning  
   - Allow editing each step  
   - Render a Vega-Lite chart  
6. Modify any step and regenerate downstream steps as needed.

---

## 💡 Example Queries

- “Create a bar chart showing total sales by category.”  
- “Which genre has the highest worldwide gross?”  
- “Plot rating vs budget as a scatter plot.”  
- “Show average revenue per year.”  

---

## 🧱 Project Structure

```text
VisGenAIGroup7/
├─ README.md                # Facing all audience
├─ AGENTS.md                # Facing Copilot/Codex
├─ .github/
│   └─ copilot-instructions.md  # Overall coding structure and context
├─ docs/
│   ├─ 01_project_overview.md   # Question, objective
│   ├─ 02_requirements.md       # Project requirement
│   ├─ 03_architecture.md       # Technical structure
│   ├─ 04_pipeline_design.md    # 6 step Prompt-to-Vis pipeline
│   ├─ 05_ui_design.md          # UI mockups & UI explanation
│   └─ 06_prompts.md            # Step to step LLM prompt sample
├─ src/
│   ├─ frontend/
│   │   ├─ app.py               # Streamlit access
│   │   └─ components/          # TableView / ChartView / StepsPanel 
│   ├─ backend/
│   │   ├─ pipeline/
│   │   │   ├─ steps.py         # 6 step scheme
│   │   │   ├─ workflow.py      # LangChain/LangGraph pipeline
│   │   ├─ llm/
│   │   │   ├─ base_client.py    # define and standardize
│   │   │   ├─ prompt_loader.py  # load prompt from doc
│   │   │   ├─ openai_client.py  # GPT-5
│   │   │   └─ groq_client.py    # Groq API
│   │   └─ vega/
│   │       └─ spec_builder.py  # 把 6 步结果拼成 Vega-Lite spec
│   └─ shared/
│       └─ schemas.py           # Pydantic data modal：StepResult, PipelineState 等
├─ venv                         # virture environment
├─ requirements.txt             # Python reliance
├─ .streamlit/
│   └─ secrets.toml.example     # API key demo
├─ .gitignore
└─ tests/
    └─ test_pipeline.py         # basic testing of pipelines

```

---

## ⚠️ Current Limitations

- Only single-table datasets  
- No automatic data cleaning  
- Limited chart types  
- Not optimized for large datasets  
- LLM output may require manual correction  

---

## 🙏 Acknowledgements

This project builds on concepts from ChartGPT, VisRAG, Transparent Prompt-to-Vis pipelines, and other academic works from CS7295.
