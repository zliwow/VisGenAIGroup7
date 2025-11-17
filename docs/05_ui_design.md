# 05. UI Design  
**Streamlit Interface for Transparent Prompt-to-Vis Pipeline**  
_Group 7 – VisGenAI_

This document defines the user interface layout, interaction flow, and responsibilities of the Streamlit frontend.  
It describes how users interact with the system, how pipeline results are displayed, and how edits trigger backend re-execution.

This document is the **source of truth** for all UI implementation.

---

## 1. Goals of the UI

The Streamlit UI must provide:

- A simple interface for users (CSV + Query → Chart)  
- Full transparency into the 6-step reasoning process  
- Editable intermediate steps via JSON  
- Easy selection of LLM provider and model  
- Clear explanation of errors and pipeline failures  
- Consistent layout between reruns  

The goal is a **clean, modular, transparent, and educational** UI.

---

## 2. Overall Layout

The Streamlit app follows a two-panel layout:

```
┌───────────────────────────────┬────────────────────────────────────────────┐
│           Sidebar             │                Main Area                   │
└───────────────────────────────┴────────────────────────────────────────────┘
```

- **Sidebar**: configuration and inputs (provider, model, API key, data, query).  
- **Main Area**: dataset preview, pipeline steps, chart, and raw Vega-Lite JSON.

---

## 3. Sidebar Layout

The sidebar contains all configuration inputs.

### 3.1 LLM Provider & Model Section

Controls:

- Provider (radio / selectbox)
  - `OpenAI`
  - `Groq`
- Model (selectbox, options depend on provider)
  - For OpenAI: e.g., `gpt-4o`, `gpt-5` (or course-allowed models)
  - For Groq: e.g., `mixtral-8x7b`, `llama-3.1-70b`, etc.

API Key handling:

- Prefer reading from `st.secrets`.
- If no key found, show an input field:
  - “Enter your API key (not stored permanently).”

State variables:

```python
st.session_state["llm_provider"]
st.session_state["llm_model"]
st.session_state["api_key"]
```

---

### 3.2 Data Input Section

Components:

- CSV uploader: `st.file_uploader("Upload CSV", type=["csv"])`
- After upload:
  - Load into Pandas DataFrame.
  - Infer column types and build `DatasetInfo`.
  - Store in session state:
    ```python
    st.session_state["dataset"]
    st.session_state["dataset_info"]
    ```

Sidebar also shows:

- Basic dataset stats (row/column counts).
- Optional checkbox: “Show data preview in main area.”

---

### 3.3 User Query Section

Components:

- Text area:
  - “Describe the chart you want to create…”
- Example queries (help text under the input).
- “Run Pipeline” button.

Behavior:

- Button is disabled until dataset and query are both available.
- On click, calls a backend function such as:
  ```python
  run_pipeline(dataset, query, provider, model)
  ```
- Response is stored into:
  ```python
  st.session_state["pipeline_state"]
  st.session_state["final_spec"]
  ```

---

## 4. Main Area Layout

The main area is organized into vertically stacked sections:

1. Dataset preview  
2. Current query & configuration summary  
3. Pipeline status and step panels  
4. Final chart display  
5. Raw Vega-Lite JSON  

### 4.1 Dataset Preview

- Optional based on sidebar checkbox.
- Uses `st.dataframe` to show:
  - First N rows.
  - Column names and inferred types.

### 4.2 Query & Configuration Summary

Display:

- Current query text.
- Selected provider and model.
- Short explanation:  
  “The pipeline will use the above model to reason across 6 steps and produce a Vega-Lite chart.”

---

## 5. Step-by-Step Pipeline Panels

Each pipeline step is displayed using a consistent pattern.

### 5.1 Layout Pattern

For step N:

- Title: `Step N — <Step Name>`
- Expandable panel (`st.expander`):
  - Human-readable summary (from the LLM reasoning field).
  - Non-editable JSON view (pretty-printed).
  - “Edit JSON” toggle.
  - When editing:
    - Text area with editable JSON.
    - “Apply Changes & Re-run from Step N” button.

Example structure:

```python
with st.expander("Step 3 — Aggregation & Transformation", expanded=True):
    st.markdown(step3.reasoning)

    st.json(step3.dict())  # non-editable view

    if st.checkbox("Edit Step 3 JSON", key="edit_step3"):
        raw = st.text_area("Step 3 JSON", json.dumps(step3.dict(), indent=2))
        if st.button("Apply Changes & Re-run from Step 3"):
            # validate and trigger re-run
```

---

### 5.2 Back-End Interaction When Editing

When the user edits a step:

1. UI reads JSON from textarea.
2. Backend validates JSON using the corresponding Pydantic model:
   ```python
   edited = Step3Output.parse_raw(raw_json)
   ```
3. If validation fails:
   - Show an error message inside the panel.
   - Do not re-run.
4. If validation succeeds:
   - Update `pipeline_state.step3 = edited`.
   - Clear steps 4–6.
   - Call `run_pipeline_from_step(state, edited_step_index=3)`.
   - Update `st.session_state["pipeline_state"]` and `["final_spec"]`.

This mechanism applies identically to all steps 1–6.

---

## 6. Chart Display

After a successful run (initial or re-run):

### 6.1 Chart Preview

- Use Altair to render the Vega-Lite spec:
  ```python
  chart = alt.Chart.from_dict(final_spec)
  st.altair_chart(chart, use_container_width=True)
  ```

- Provide basic controls:
  - Toggle full-width / fixed-width.
  - Optionally support `st.download_button` to export spec JSON.

### 6.2 Raw Vega-Lite JSON

- Displayed in a dedicated expander:

```python
with st.expander("Final Vega-Lite JSON", expanded=False):
    st.json(final_spec)
```

This gives users direct visibility into the final spec.

---

## 7. Error Handling UI

Errors may occur at several points:

- Invalid LLM JSON output.
- Missing fields required by the schema.
- Unsupported chart types or encodings.
- Vega-Lite spec validation or Altair rendering errors.

### 7.1 Error Message Pattern

Use a reusable component (e.g., `components/error_box.py`) to display:

```text
❌ Error at Step N
Message: <human-readable message>
Details: [expand to view raw LLM output or exception traceback]
```

Implementation idea:

```python
st.error(f"Error at Step {step_index}: {error_message}")
with st.expander("Details"):
    st.code(raw_output_or_traceback, language="text")
```

Errors should:

- Not crash the app.
- Encourage the user to inspect or edit the step.
- Provide enough detail for debugging.

---

## 8. Interaction Flow

### 8.1 Initial Run

1. User uploads CSV.
2. User selects provider and model.
3. User enters query.
4. User clicks “Run Pipeline”.
5. Backend:
   - Initializes `PipelineState`.
   - Executes LangGraph steps 1→6.
   - Calls `spec_builder.build_spec`.
6. Frontend:
   - Shows step panels.
   - Renders chart.
   - Shows raw Vega-Lite JSON.

### 8.2 Editing a Step

1. User opens a step panel.
2. User toggles “Edit JSON”.
3. User modifies JSON.
4. User clicks “Apply Changes & Re-run from Step N”.
5. Backend:
   - Validates JSON as `StepNOutput`.
   - Updates state and clears later steps.
   - Re-runs N→6.
   - Rebuilds final spec.
6. Frontend:
   - Updates all downstream step panels.
   - Rerenders chart and JSON.

---

## 9. State Management Strategy

We rely on `st.session_state` to store:

```python
"dataset"          # pandas DataFrame
"dataset_info"     # DatasetInfo Pydantic model
"pipeline_state"   # PipelineState Pydantic model
"final_spec"       # dict (Vega-Lite spec)
"llm_provider"     # "openai" or "groq"
"llm_model"        # selected model name
"api_key"          # if not from secrets
"last_run_time"    # optional: timestamp
```

### Principles:

- All state that must persist across reruns lives in session_state.
- UI reading and writing these keys must handle missing values gracefully.
- When provider/model changes, pipeline_state and final_spec should be reset.

---

## 10. UI Component Structure

Under `src/frontend/components/`, we recommend:

| Component file            | Responsibility                                      |
|---------------------------|-----------------------------------------------------|
| `sidebar_controls.py`     | LLM provider/model/API key + data upload controls  |
| `dataset_viewer.py`       | Table + dataset metadata                            |
| `step_panel.py`           | Generic step panel (view + edit JSON)              |
| `chart_viewer.py`         | Render chart & Vega-Lite JSON                       |
| `error_box.py`            | Consistent error display                            |
| `run_button.py`           | Encapsulated “Run Pipeline” button logic            |

The main `app.py` should orchestrate these components without embedding heavy logic.

---

## 11. Design Principles

The UI design follows these principles:

- **Transparency**: All intermediate reasoning is visible and editable.  
- **Modularity**: UI components are reusable and self-contained.  
- **Robustness**: Errors are surfaced clearly; no silent failures.  
- **Minimalism**: Avoid unnecessary visual clutter; focus on pipeline and chart.  
- **AI-Friendly**: Clear code structure makes it easier for Copilot/ChatGPT to safely generate and refactor code.  

---

## 12. Future UI Enhancements

Potential future improvements:

- Visualization of pipeline as a flow diagram (e.g., graph showing Step 1–6).  
- History of pipeline runs (log of past queries and charts).  
- Theming support (light/dark mode).  
- Export of edited pipeline steps and prompts for research purposes.  
- Advanced controls for Vega-Lite (manual tuning of encodings in UI).  

---

_This UI design document should be kept in sync with the actual Streamlit implementation.  
When major UI behavior changes occur, update this document first, then adjust the code._
