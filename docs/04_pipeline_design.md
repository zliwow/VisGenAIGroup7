# 04. Pipeline Design  
**Transparent Prompt-to-Vis 6-Step Reasoning Pipeline (LangChain + LangGraph)**  
_Group 7 – VisGenAI_

This document defines the complete multi-step reasoning pipeline, including:  
- The 6-step Prompt-to-Vis process  
- Input/output schemas (Pydantic)  
- LangGraph node structure  
- Pipeline state design  
- Step edit + re-run strategy  
- Error handling  
- Prompt feeding strategy  
- Design rationale  

This document is the **source of truth** for backend pipeline implementation.

---

# 1. Goals of the Pipeline

The Prompt-to-Vis pipeline is designed to:

- Provide **transparent, editable** intermediate reasoning steps  
- Allow users to re-run steps from any point  
- Produce **valid Vega-Lite** JSON  
- Support multiple LLM providers (OpenAI, Groq)  
- Guarantee structured outputs via Pydantic  
- Enable robust and deterministic visualization generation  

The goal is to make the entire reasoning path explainable and correctable.

---

# 2. Pipeline Overview (6 Steps)

The system uses a 6-step design inspired by ChartGPT, extended for transparency, reliability, and modularity.

---

## **Step 1 — Column Understanding & Selection**  
**Purpose:** Identify relevant dataset columns for the user query.

**LLM tasks:**  
- Analyze dataset metadata  
- Interpret user intent  
- Select essential columns  
- Infer column semantic roles  

**Output Schema:**  
```python
selected_columns: List[str]
column_roles: Dict[str, Literal['quantitative','categorical','temporal']]
reasoning: str
```

---

## **Step 2 — Analytical Intent Classification**  
**Purpose:** Determine the analytical task type.

**Examples:**  
- Comparison  
- Trend  
- Distribution  
- Correlation  
- Ranking  

**Output Schema:**  
```python
intent: Literal['compare','trend','distribution','correlation','rank']
target_columns: List[str]
reasoning: str
```

---

## **Step 3 — Aggregation & Transformation**  
**Purpose:** Identify necessary transformations before visualization.

**Examples:**  
- Aggregations (sum, mean, count)  
- Filters (Price < 100, Date > 2020)  
- Group-by  
- Derived fields  

**Output Schema:**  
```python
aggregations: List[AggregationSpec]
filters: List[FilterSpec]
group_by: List[str]
reasoning: str
```

---

## **Step 4 — Visualization Type Recommendation**  
**Purpose:** Suggest the best chart type.

**Examples:**  
- bar  
- line  
- point  
- histogram  
- area  
- heatmap  

**Output Schema:**  
```python
mark_type: Literal['bar','line','point','area','rect','arc','boxplot']
justification: str
```

---

## **Step 5 — Encoding Assignment**  
**Purpose:** Map fields to visual encoding channels.

**Examples:**  
- x, y  
- color  
- size  
- shape  
- tooltip  

**Output Schema:**  
```python
EncodingsValue = Union[
    EncodingSpec,
    List[EncodingSpec],        # e.g., tooltip arrays
    Dict[str, Any],            # passthrough for advanced configs
    List[Dict[str, Any]],
]
encodings: Dict[str, EncodingsValue]
```

Note: Sort directives (e.g., `y desc`) are handled inside encoding specifications, consistent with Vega-Lite grammar. Tooltip arrays (lists of EncodingSpec) are explicitly supported to match Vega-Lite semantics.

---

## **Step 6 — Vega-Lite Draft Spec Generation**  
**Purpose:** Let the LLM produce an initial “draft” Vega-Lite spec.

This draft is **not final**. It is validated and corrected by `spec_builder.py`.

**Output Schema:**  
```python
vl_spec_draft: Dict
warnings: Optional[List[str]]
```

---

# 3. Unified Pipeline State

All intermediate results are stored in a global state:

```python
class PipelineState(BaseModel):
    dataset_info: DatasetInfo
    user_query: str

    step1: Optional[Step1Output]
    step2: Optional[Step2Output]
    step3: Optional[Step3Output]
    step4: Optional[Step4Output]
    step5: Optional[Step5Output]
    step6: Optional[Step6Output]

    final_spec: Optional[Dict]  # Produced by spec_builder
```

This state is passed between LangGraph nodes.

---

# 4. LangGraph Node Design

The pipeline is implemented as a **6-node directed acyclic graph**:

```
Step1 → Step2 → Step3 → Step4 → Step5 → Step6 → spec_builder
```

Each node performs:

1. Read relevant parts of `PipelineState`  
2. Load step-specific prompt using prompt_loader  
3. Call `llm_client.invoke(prompt)`  
4. Parse JSON into a Pydantic model  
5. Update state  

---

## Node Function Signature

```python
def stepX_node(state: PipelineState, llm_client: BaseLLMClient) -> PipelineState:
    ...
```

LangGraph orchestrates the sequential execution.

---

# 5. Node Definitions By Step

Each pipeline step follows:

### **Input:**  
- Subset of `PipelineState`  
- Selected LLM provider + model  

### **Processing:**  
- Fill prompt template with placeholders  
- Invoke LLM  
- Validate JSON → Pydantic model  

### **Output:**  
- Update `PipelineState`  

---

# 6. Re-Run From Intermediate Steps

Users may edit any pipeline step.  
This triggers:

```
Re-run from edited step N → propagate to step 6
```

### Process:

1. Frontend sends edited JSON  
2. Backend replaces `pipeline_state.stepN`  
3. Steps N+1 … 6 are cleared  
4. The backend recomputes steps sequentially  
5. New `final_spec` is generated  

This design enables fully editable and explainable reasoning.

---

# 7. Prompt Feeding Strategy

Each step loads prompts via:

```python
prompt = prompt_loader.load_prompt("step1")
```

### Placeholder filling example:
```python
filled_prompt = prompt.format(
    user_query = state.user_query,
    columns = dataset.columns,
    previous_steps = state.step1.json(),
)
```

Prompts **must not** appear in Python files.  
Only `docs/06_prompts.md` stores prompt text.

---

# 8. Error Handling

### If JSON is malformed:
- Try regex extraction  
- Try partial validation  
- If still invalid → return structured error  

### If required fields are missing:
Return error payload:

```json
{
  "error": {
     "message": "...",
     "step": 3,
     "raw_output": "<LLM output>"
  }
}
```

### If Vega-Lite spec fails:
Handled by Vega-Lite builder layer.

---

# 9. Final Vega-Lite Spec Generation

After Step 6:

```
final_spec = spec_builder.build_spec(pipeline_state)
```

The builder:

- Uses encodings from Step 5  
- Uses mark from Step 4  
- Corrects incorrect LLM output  
- Produces clean Vega-Lite JSON  

**Returned to frontend:**

```python
{
  "pipeline_state": ...,
  "vegalite_spec": ...
}
```

---

# 10. Pipeline Execution API

Backend exposes two top-level functions:

### **Full run**
```python
run_pipeline(dataset, user_query, provider, model)
```

### **Partial re-run**
```python
run_pipeline_from_step(state, edited_step_index)
```

Frontend interacts only with these high-level APIs.

---

# 11. Why This Design Works

### ✔ Transparent  
Every reasoning step is visible and editable.

### ✔ Robust  
JSON outputs validated with Pydantic.

### ✔ Modular  
Each step is isolated and testable.

### ✔ Extensible  
Plug-and-play LLM providers.

### ✔ Deterministic Visualization  
Spec builder ensures correctness.

### ✔ AI-Friendly  
Strong architecture boundaries = safe vibe coding.

---

# 12. Future Extensions

- Add Step 0: dataset profiling  
- Add Step 7: narrative explanation  
- Add branching pipelines (geospatial, multi-view)  
- Add auto-correction and fallback strategies  
- Add persistent pipeline history  

---

_This pipeline design document must stay synchronized with the implementation.  
Any major change to pipeline structure must update this file first._

---

# 13. Why Altair / Vega-Lite Is Used

The LLM does not process full datasets or compute aggregations. Instead, it produces **rules** describing how the visualization should be constructed (e.g., which fields to aggregate, group-by keys, encodings, and chart type).

Execution flow:

1. **LLM produces structured transformation rules** (Steps 1–6).
2. `spec_builder.py` converts these rules into **Vega-Lite JSON**.
3. Streamlit uses **Altair**, a Python wrapper for Vega-Lite, to render charts.
4. Vega-Lite executes data transformations (mean, sum, count, sort, filters) in the browser.

Reasons for this design:

- Vega-Lite is **declarative** and maps naturally to LLM-generated rules.
- Altair offers a clean Python API while preserving full Vega-Lite expressiveness.
- Full dataset never goes into the LLM—preserves privacy and avoids token explosion.
- Deterministic rendering via Vega-Lite ensures correctness and reproducibility.

# 14. Future Evolution: JSON-Editable Steps & LangGraph Orchestration

In the current implementation, the 6-step Prompt-to-Vis pipeline is executed
as a simple sequential Python workflow:

1 → 2 → 3 → 4 → 5 → 6

This is sufficient for our MVP and for the course requirements.

However, once we introduce JSON-editable step panels in the UI
(e.g., the user edits the output of Step 3 and wants to re-run the pipeline
from Step 3 onward), we plan to evolve the backend into a LangGraph-based
orchestrator:

- Each Step (1–6) becomes a node in the graph.
- `PipelineState` is used as the shared state object between nodes.
- The graph allows us to re-run the pipeline starting from an arbitrary node
  (e.g., "step3") without recomputing earlier steps.

This evolution is deliberately postponed until the JSON-editable UI is in place,
so that we can keep the MVP backend as simple and debuggable as possible.
