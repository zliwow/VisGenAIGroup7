# 03. System Architecture

This document describes the overall architecture of the **VisGenAI Group 7 Prompt-to-Vis** system.  
It explains the major components, their responsibilities, and how data flows from user input to the final Vega-Lite visualization.

---

## 1. High-Level Overview

The system follows a **clean, layered architecture** with strong separation of concerns.  
The layers are:

### **1. Frontend Layer (Streamlit UI)**  
Handles user interaction and visualization.

### **2. Backend Pipeline Layer (LangChain + LangGraph)**  
Implements the 6-step Prompt-to-Vis reasoning workflow.

### **3. LLM Integration Layer (OpenAI / Groq)**  
Unified interface for different LLM providers.

### **4. Vega-Lite Rendering Layer**  
Builds deterministic Vega-Lite specifications from structured pipeline outputs.

### **5. Shared Model Layer (Pydantic Schemas)**  
Defines strict data contracts between layers.

This structure ensures:

- Strong modularity  
- Easy maintenance  
- Clear team collaboration  
- Perfect synergy with AI-assisted development (Copilot / ChatGPT)  

---

## 2. Directory Structure (Reference Only)

> **The complete directory structure is maintained ONLY in `README.md` (Single Source of Truth).**  
> This document provides conceptual descriptions of modules without duplicating physical paths.

All mentions of “frontend / pipeline / llm / vega / shared” below refer to the modules defined in the README’s directory layout.

---

## 3. Component Responsibilities

### 3.1 Frontend Layer (Streamlit)

Responsibilities:

- Render UI components:
  - CSV upload
  - LLM provider & model selection
  - Query input
  - Step-by-step reasoning panels
  - Final Vega-Lite chart + raw JSON
- Invoke backend pipeline via high-level functions
- Display error messages, intermediate steps, and final visual output

**Key design principle:**  
Frontend must stay **thin**—no business logic, no LLM calls.

---

### 3.2 Backend Pipeline Layer (LangGraph)

Responsibilities:

- Implement the **6-step Prompt-to-Vis pipeline**:
  1. Column Selection  
  2. Intent Classification  
  3. Aggregation & Filtering  
  4. Plot Type Recommendation  
  5. Encoding Assignment  
  6. Vega-Lite Spec Draft Generation  
- Manage a central shared state (`PipelineState`)
- Enforce structured outputs via Pydantic schemas
- Support re-running from any intermediate step
- Handle failures (invalid JSON → fail gracefully)

**Key design principle:**  
Each step is a pure LangGraph node: prompt → LLM → Pydantic → update state.

---

### 3.3 LLM Integration Layer (OpenAI & Groq)

Responsibilities:

- Provide a unified LLM interface (`BaseLLLLMClient`)
- Normalize differences between OpenAI and Groq
- Load prompts from documentation (`docs/06_prompts.md`)
- Handle errors, retries, response cleaning

**Key design principle:**  
Pipeline NEVER calls OpenAI/Groq directly;  
it only calls `llm_client.invoke(prompt)`.

---

### 3.4 Vega-Lite Rendering Layer

Responsibilities:

- Convert pipeline outputs into valid Vega-Lite JSON specs
- Validate encoding channels and grammar
- Provide two outputs:
  - Raw spec JSON
  - Altair chart object for Streamlit rendering

**Key design principle:**  
No AI, no guessing—this layer is deterministic and rule-based.

---

### 3.5 Shared Model Layer (Pydantic)

Responsibilities:

- Define all core data structures:
  - Dataset metadata (column names, types)
  - Pipeline step outputs
  - PipelineState
  - Vega-Lite components
- Enforce consistency and robustness in LLM output parsing

**Key design principle:**  
Pydantic ensures reliable AI → pipeline integration.

---

## 4. End-to-End Data Flow

### **1. User Interaction (Frontend)**  
User uploads CSV and enters a natural language query.

### **2. Pipeline Initialization**  
Frontend passes dataset + query + provider/model to backend.

### **3. LangGraph Execution**  
Each step:
1. Load prompt  
2. Call llm_client.invoke()  
3. Parse JSON  
4. Update pipeline state  

### **4. Vega-Lite Spec Build**  
Using final pipeline state, deterministic builder constructs chart spec.

### **5. Frontend Visualization**  
Streamlit renders:
- Step outputs  
- Vega-Lite chart  
- Raw JSON  

### **6. Step Editing**  
If user edits a step, pipeline re-runs from that step onward.

---

## 5. Interaction Sequence (Textual)

**Frontend → Backend → Pipeline → LLM → Pipeline → Vega → Frontend**

Example (simplified):

1. frontend: `run_pipeline(dataset, query, provider, model)`
2. backend: initialize `PipelineState`
3. pipeline step 1:
   - load prompt
   - `llm_client.invoke(prompt)`
   - update state
4. repeat for steps 2–6
5. backend: call `spec_builder.build_spec(state)`
6. frontend: render chart + step outputs

---

## 6. Architectural Principles

The architecture follows several design rules:

### ✔ Loose coupling  
Each layer is independent.

### ✔ High cohesion  
Each module has a single responsibility.

### ✔ Transparency  
6-step reasoning pipeline is exposed to the user.

### ✔ Explainability  
Users can edit intermediate steps.

### ✔ Extendability  
New LLM providers can be plugged in easily.

### ✔ Stability  
Vega-Lite builder ensures deterministic output.

### ✔ AI-Friendly  
Clear boundaries allow Copilot / ChatGPT to generate code safely.

---

## 7. Future Extensions

Possible future additions:

- Support for more LLM providers
- Multi-view visualizations
- Advanced spec validation (constraints, rules)
- Dataset profiling and auto-summary
- Visualization recommendation beyond Vega-Lite (e.g., multi-view dashboards)

---

_This architecture document should be kept in sync with implementation.  
When major changes occur in code, update this document first._

