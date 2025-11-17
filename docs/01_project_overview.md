# 01. Project Overview  
**VisGenAI Group 7 – Transparent Prompt-to-Vis Pipelines**

This document provides a high-level overview of the project:

- What problem we are solving  
- Our proposed solution and design principles  
- The main components of the system  
- How to navigate the rest of the documentation in `docs/`  

It is intended as an entry point for instructors, TAs, new contributors, and future developers.

---

## 1. Project Context

This project is part of **CS7295 – Data Visualization & Generative AI** at Northeastern University.

Recent systems such as **ChartGPT** show that Large Language Models (LLMs) can translate natural language into visualizations. However, most existing systems behave like black boxes:

- Users see only the *final chart*, not the steps behind it.  
- When something is incorrect, it is unclear *which step went wrong*.  
- There is no way to *debug or correct intermediate reasoning*.

Our project addresses this by building a **transparent, stepwise Prompt-to-Vis pipeline** that exposes the reasoning chain from *natural language → visualization*.

---

## 2. Problem Statement

Given:

- A tabular dataset (CSV)  
- A natural language question  

We aim to generate a meaningful, valid **Vega-Lite** visualization.

Challenges:

1. The mapping from question → visualization requires multiple decisions:
   - Column selection  
   - Analytical intent  
   - Aggregations & filters  
   - Chart type  
   - Encodings  
2. Existing systems hide this chain inside a single LLM call.  
3. Users cannot inspect, adjust, or re-run individual steps.  

---

## 3. Our Solution: A Transparent 6-Step Pipeline

We implement a **6-step, LLM-driven reasoning pipeline** using LangChain + LangGraph, where each step produces structured, Pydantic-validated JSON.

1. **Column Understanding & Selection**  
2. **Analytical Intent Classification**  
3. **Aggregation & Transformation**  
4. **Visualization Type Recommendation**  
5. **Encoding Assignment**  
6. **Vega-Lite Draft Generation**

Key ideas:

- Each step is **modular**, **inspectable**, and **editable**.  
- The full state lives inside a shared `PipelineState` model.  
- Editing any step re-runs only the necessary downstream steps.  
- A deterministic **Vega-Lite builder** produces the final chart.  

---

## 4. Core Features

- 🧩 **Decomposed Reasoning** (6-step pipeline)  
- 🪟 **Transparency** (all step outputs visible)  
- ✏️ **Editability** (override JSON and re-run)  
- 🎛 **Choice of LLM Provider** (OpenAI or Groq)  
- 📊 **Interactive Vega-Lite Rendering**  
- 🧱 **LLM-friendly architecture** for Copilot / ChatGPT  

---

## 5. High-Level Architecture Summary

The system consists of:

- **Streamlit frontend** (`src/frontend/`)  
  - User interface, CSV upload, pipeline output display  

- **Backend reasoning engine** (`src/backend/pipeline/`)  
  - LangGraph workflow for executing Steps 1–6  

- **LLM integration** (`src/backend/llm/`)  
  - OpenAI/Groq unified client  
  - Prompt loading from `docs/06_prompts.md`  

- **Vega-Lite builder** (`src/backend/vega/spec_builder.py`)  
  - Deterministic construction of final chart spec  

- **Shared schemas** (`src/shared/schemas.py`)  
  - Strict data contracts across all modules  

Detailed architecture is documented in `docs/03_architecture.md`.

---

## 6. Technology Stack

### Frontend
- Streamlit  
- Altair (Vega-Lite wrapper)

### Backend
- Python  
- LangChain / LangGraph  
- Pydantic  
- Requests for HTTP client  

### Visualization
- Vega-Lite (JSON grammar)  
- Executed in browser via Altair

### LLM Providers
- OpenAI  
- Groq  

---

## 7. How to Navigate This Repo

For **running the app**:
- See `README.md` → Quick Start

For **understanding project requirements**:
- `docs/02_requirements.md`

For **understanding architecture**:
- `docs/03_architecture.md`

For **understanding the pipeline**:
- `docs/04_pipeline_design.md`

For **editing the frontend**:
- `docs/05_ui_design.md`

For **editing prompts**:
- `docs/06_prompts.md`

For **AI-based coding**:
- `AGENTS.md`  
- `.github/copilot-instructions.md`

---

## 8. Limitations

- Prototype scope: tabular CSV only  
- Single-view Vega-Lite charts only  
- Prompts optimized for clarity vs robustness  
- Requires LLM API keys (OpenAI/Groq)

Future work:
- Multi-view dashboards  
- Dataset profiling  
- More complex Vega-Lite patterns  
- Additional LLM providers  

---

## 9. Glossary

**Prompt-to-Vis** — Mapping natural language to visualizations  
**Transparent Pipeline** — Intermediate decisions exposed to user  
**Vega-Lite** — Declarative JSON visualization grammar  
**Altair** — Python wrapper for Vega-Lite  
**LangGraph** — Graph-based orchestration for LLM workflows  

---

_This overview describes the conceptual foundation of the project.  
For detailed implementation, refer to `docs/02–06` and `src/`._
