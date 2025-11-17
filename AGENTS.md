# AGENTS.md

This document defines how AI coding assistants (GitHub Copilot, Codex, ChatGPT, etc.) should behave when generating or modifying code in this repository.

It specifies:

- The **architecture** of the project  
- The **roles** (agents) and their responsibilities  
- **File ownership** and coding rules  
- How agents should cooperate to keep the codebase modular and maintainable  

AI tools should treat this document as a **source of truth** when assisting with vibe coding.

---

## 1. Project Architecture Summary

The project implements a **transparent Prompt-to-Vis pipeline**:

- **Frontend**: Streamlit app for:
  - CSV upload and data preview
  - LLM provider/model selection (OpenAI / Groq)
  - Running the 6-step pipeline
  - Viewing and editing intermediate reasoning
  - Rendering Vega-Lite charts

- **Backend Pipeline**: LangChain + LangGraph
  - 6-step reasoning pipeline (column selection → Vega-Lite spec)
  - Each step is a LangGraph node
  - Shared state object for intermediate step outputs

- **LLM Layer**:
  - Multiple providers (OpenAI, Groq)
  - Unified client interface via `BaseLLMClient`
  - Prompt templates defined in `docs/06_prompts.md`
  - `prompt_loader.py` loads prompts from docs

- **Data Models**:
  - Pydantic models in `src/shared/schemas.py`
  - Define structure for pipeline state, step outputs, and Vega-Lite spec inputs

- **Vega-Lite Rendering**:
  - `spec_builder.py` converts structured pipeline results into Vega-Lite specifications
  - Streamlit renders charts via Altair

---

## 2. Agents Overview

The following “agents” are conceptual roles that AI coding assistants should adopt, depending on what part of the code they are working on.

### 2.1 System Architect Agent

**Responsibilities:**

- Maintain consistency between implementation and design docs:
  - `docs/02_requirements.md`
  - `docs/03_architecture.md`
  - `docs/04_pipeline_design.md`
  - `docs/05_ui_design.md`
  - `docs/06_prompts.md`
- Preserve the project folder structure and avoid ad-hoc file placement.
- Ensure clear boundaries between:
  - Frontend (`src/frontend/**`)
  - Pipeline (`src/backend/pipeline/**`)
  - LLM layer (`src/backend/llm/**`)
  - Vega-Lite layer (`src/backend/vega/**`)
  - Shared schemas (`src/shared/schemas.py`)

**Behavior:**

- Before adding a new module or changing architecture, update the relevant doc under `docs/`.
- Avoid mixing responsibilities (e.g., no pipeline logic inside `app.py`).

---

### 2.2 Backend Pipeline Engineer Agent

**Scope:**
- `src/backend/pipeline/steps.py`
- `src/backend/pipeline/workflow.py`
- `src/shared/schemas.py`

**Responsibilities:**

- Implement the 6-step reasoning pipeline using **LangGraph**.
- Reference the pipeline design in `docs/04_pipeline_design.md`.
- Define and maintain Pydantic models for pipeline state, step outputs, and shared structures.
- Ensure each step is a pure function/node that uses shared state.
- Do NOT call LLM APIs directly (use the LLM layer).

---

### 2.3 LLM Integration Engineer Agent

**Scope:**
- `src/backend/llm/base_client.py`
- `src/backend/llm/openai_client.py`
- `src/backend/llm/groq_client.py`
- `src/backend/llm/prompt_loader.py`
- `docs/06_prompts.md`

**Responsibilities:**

- Maintain a unified LLM interface (`BaseLLMClient`).
- Implement provider-specific clients (OpenAI + Groq).
- Manage prompt templates in `docs/06_prompts.md`.
- Implement `prompt_loader.py` to load prompts cleanly.
- Enforce JSON-only outputs aligned with `schemas.py`.

---

### 2.4 Vega-Lite Spec Engineer Agent

**Scope:**
- `src/backend/vega/spec_builder.py`

**Responsibilities:**

- Convert structured pipeline results into Vega-Lite specifications.
- Validate field names, grammar, and encoding channels.
- Provide clear errors without calling LLMs.
- Keep responsibilities limited to mapping → Vega-Lite JSON.

---

### 2.5 Streamlit Frontend Engineer Agent

**Scope:**
- `src/frontend/app.py`
- `src/frontend/components/*`

**Responsibilities:**

- Build the Streamlit UI:
  - Sidebar controls (provider, model, API key)
  - CSV upload
  - Prompt input
  - Step-by-step display + editing
  - Chart preview
- Keep UI modular and avoid pipeline logic in UI code.
- Use backend functions (`run_pipeline`) rather than calling LLMs directly.

---

## 3. Global Coding Rules

1. **Respect project structure.**
2. **Each file must have a single responsibility.**
3. **All pipeline data must use Pydantic schemas.**
4. **Never hardcode secrets.**
5. **Prompt templates must live in `docs/06_prompts.md`.**
6. **Catch errors and avoid app-wide crashes.**
7. **Update docs first when changing architecture/pipeline design.**

---

## 4. Interaction Rules Between Agents

- System Architect ensures structural consistency.
- Backend Pipeline Engineer consumes LLM client + prompts, but does not implement them.
- LLM Integration Engineer manages prompt templates + provider clients.
- Vega-Lite Spec Engineer depends on pipeline outputs defined in `schemas.py`.
- Streamlit Engineer only interacts with backend API, not raw pipeline nodes.

---

## 5. File Ownership Map

**System Architect**
- `AGENTS.md`
- All `docs/*.md`

**Backend Pipeline Engineer**
- `src/backend/pipeline/*`
- `src/shared/schemas.py`

**LLM Integration Engineer**
- `src/backend/llm/*`
- `docs/06_prompts.md`

**Vega-Lite Spec Engineer**
- `src/backend/vega/spec_builder.py`

**Streamlit Frontend Engineer**
- `src/frontend/app.py`
- `src/frontend/components/*`

---

## 6. Do Not Do List

AI assistants must NOT:

- Introduce new JS frameworks (React/Vue)
- Add backend frameworks (Django/FastAPI)
- Bypass the 6-step pipeline
- Hardcode API keys
- Mix UI with business logic
- Modify folder structure without updating docs
- Silently ignore pipeline/LLM/output errors

---

_This AGENTS.md is a living document. Update it when architecture evolves._
