# GitHub Copilot Instructions

These instructions define how GitHub Copilot should behave in this repository.  
They override Copilot’s default behavior and enforce architecture, structure, and coding rules for this project.

Copilot should follow these instructions for **all chat requests, inline code completions, refactors, and code generation tasks** in this workspace.

---

# 1. Project Context

This repository implements a **transparent Prompt-to-Vis pipeline**:

- **Frontend**: Streamlit
- **Backend**: LangChain + LangGraph pipeline
- **LLM Integration**: OpenAI / Groq (pluggable LLM providers)
- **Prompts**: Stored in `docs/06_prompts.md`
- **Data Models**: Pydantic schemas
- **Spec Rendering**: Vega-Lite via `spec_builder.py`

Copilot must preserve this architecture at all times.

---

# 2. Global Rules (Copilot MUST follow these)

## 2.1 Structural Safety (Default Behavior)
- Do NOT create new top-level folders.
- Do NOT move files outside their designated modules.
- Do NOT introduce new frameworks or architectural layers.
- **Exception:**  
  If the user explicitly writes:  
  _"This is an intentional architecture change. You may modify the project structure."_  
  then Copilot may suggest structural refactors.

## 2.2 Responsibility Separation
- **Streamlit = UI only**  
- **Pipeline = business logic**  
- **LLM clients = API wrappers only**  
- **Vega-Lite layer = visualization spec translation only**

## 2.3 Use Pydantic Schemas
All structured data MUST use Pydantic models defined in:
```
src/shared/schemas.py
```
No loose dictionaries.

## 2.4 Never Embed Long Prompt Strings in Code
- Prompts MUST be stored in `docs/06_prompts.md`
- Code must load prompts using:
```
src/backend/llm/prompt_loader.py
```

## 2.5 LLM Calls Must Go Through LLM Clients
Only these files may make direct API calls:
- `openai_client.py`
- `groq_client.py`

Pipeline nodes MUST use:
```python
llm_client.invoke(prompt)
```

## 2.6 Vega-Lite Only
Copilot must NOT generate:
- Matplotlib  
- Seaborn  
- Plotly  
- ECharts  

Only Vega-Lite / Altair is allowed.

## 2.7 Error Handling
- Do not crash the app.
- Surface human-readable errors.
- Validate JSON output from the LLM.
- Attempt auto-repair for malformed JSON when possible.

---

# 3. File-Specific Rules

## 3.1 `src/frontend/**`
- UI logic only  
- No business logic  
- Use backend APIs (`run_pipeline`)  
- Components must remain modular

## 3.2 `src/backend/pipeline/**`
- Use LangGraph to define the 6-step workflow
- Each step is a node with well-defined schema inputs/outputs
- Steps must not call LLMs directly
- Pure logic only; load prompts via prompt_loader

## 3.3 `src/backend/llm/**`
- Maintain:
  - `BaseLLMClient`
  - `OpenAIClient`
  - `GroqClient`
- Handle secrets via environment or Streamlit secrets
- Ensure consistent `invoke(prompt)` behavior
- No UI imports allowed

## 3.4 `src/backend/vega/spec_builder.py`
- Convert structured outputs → Vega-Lite spec
- Validate encodings & field names
- No Streamlit or LLM imports

## 3.5 `docs/**`
- Serve as reference for Copilot
- Copilot must NOT modify docs unless explicitly instructed

---

# 4. Coding Style Rules

## 4.1 Python
- Use type hints everywhere
- Use Pydantic for structured data
- Keep functions small, modular, and readable

## 4.2 Streamlit
- Use sidebar for provider/model/API key selection
- Use expanders for verbose JSON or debug info
- Keep UI layout consistent

## 4.3 Testing (Optional but Recommended)
Copilot may generate tests using:
```
pytest
```
Focus on:
- Pipeline step correctness
- LLM client mocking
- Vega-Lite spec validation

---

# 5. Copilot Agent Behavior

This repository defines conceptual roles in `AGENTS.md`:

- System Architect Agent
- Backend Pipeline Engineer Agent
- LLM Integration Engineer Agent
- Vega-Lite Spec Engineer Agent
- Streamlit Frontend Engineer Agent

Copilot should infer which role applies based on the file being edited. For example:

- Editing `workflow.py` → Backend Pipeline Engineer  
- Editing `openai_client.py` → LLM Integration Engineer  
- Editing `spec_builder.py` → Vega-Lite Spec Engineer  
- Editing `app.py` → Streamlit Frontend Engineer  

Each role has its own coding rules defined in `AGENTS.md`.

---

# 6. “Do Not Do” List (Strict)

Copilot MUST NOT:

- Generate code using non-Vega-Lite charting libraries  
- Introduce Django, Flask, FastAPI, or unnecessary frameworks  
- Add new files outside of permitted directories  
- Duplicate prompt logic in Python files  
- Skip or combine pipeline steps  
- Modify architecture without explicit permission  
- Ignore schema definitions  
- Produce silent failures  

---

# 7. Summary for Copilot

Your priorities:

1. Follow these instructions  
2. Follow AGENTS.md  
3. Follow docs in `/docs`  
4. Match existing coding style  
5. Preserve architecture and modularity  

**Your goal is to generate clean, maintainable, modular code aligned with this repository’s structure and goals.**

---

# End of Copilot Instructions
