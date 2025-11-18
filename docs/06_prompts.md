# 06. Prompt Templates  
_Group 7 – VisGenAI_  
**Transparent Prompt-to-Vis Pipeline – Stepwise Prompt Templates for LangChain/LangGraph**

This document defines all prompt templates used across the 6-step reasoning pipeline.  
Each template is loaded by `prompt_loader.py` and filled with runtime values before calling LLMs.  
These prompts are the **single source of truth**.

---

# 1. Global Instructions

These global instructions apply to all steps.

### LLM Behavior Rules

You must obey the following:

1. **You must output ONLY valid JSON. No explanations, no comments, no markdown, no backticks.**
2. **The JSON MUST follow the schema provided for each step.**
3. **All strings must be double-quoted.**
4. **Do not include trailing commas.**
5. **Do not return natural-language commentary outside of the `reasoning` field.**
6. **If referencing previous steps, you must respect their decisions and NOT overwrite them.**
7. **If uncertain, make your best guess and explain your reasoning in the `reasoning` or `warnings` field.**

---

# 2. Placeholder Reference

The following placeholders appear in prompts and are filled by the backend at runtime:

| Placeholder | Meaning |
|------------|---------|
| `{USER_QUERY}` | Natural language query from the user |
| `{DATASET_SCHEMA}` | Column names + inferred types |
| `{DATASET_SAMPLE}` | Top N rows of dataset in compact table format |
| `{STEP1_OUTPUT}` | JSON output from Step 1 |
| `{STEP2_OUTPUT}` | JSON output from Step 2 |
| `{STEP3_OUTPUT}` | JSON output from Step 3 |
| `{STEP4_OUTPUT}` | JSON output from Step 4 |
| `{STEP5_OUTPUT}` | JSON output from Step 5 |
| `{OUTPUT_FORMAT}` | JSON schema example (target output structure) |

All uppercase placeholders are replaced by runtime strings before sending to the LLM.

---

# 3. Step-by-Step Prompt Templates

---

# Step 1 — Column Understanding & Selection

## Purpose
Analyze the dataset schema + user query to determine:
- which columns are relevant  
- each column’s semantic role (categorical / quantitative / temporal)

This step does NOT determine chart type, encoding, filters, or aggregations.

## Expected JSON Output
```json
{
  "selected_columns": ["colA", "colB"],
  "column_roles": {
    "colA": "categorical",
    "colB": "quantitative"
  },
  "reasoning": "Explain why each column is selected and how its role was determined."
}
```

## Prompt Template
```text
You are performing **Step 1: Column Understanding & Selection** in a multi-step Prompt-to-Vis pipeline.

Your task:
- Analyze the dataset schema and sample rows.
- Determine which columns are relevant to answering the user query.
- Assign a semantic role to each selected column:
  - "categorical"
  - "quantitative"
  - "temporal"
- Provide your reasoning in the `reasoning` field.

Important rules:
- You MUST output ONLY valid JSON.
- Use the exact schema provided at the end.
- Do NOT include markdown, comments, or additional text.

User query:
{USER_QUERY}

Dataset schema:
{DATASET_SCHEMA}

Sample rows:
{DATASET_SAMPLE}

Output JSON format (you MUST follow this exactly):
{OUTPUT_FORMAT}
```

---

# Step 2 — Analytical Intent Classification

## Purpose
Identify the primary analytical intent behind the user query:

- compare  
- trend  
- distribution  
- correlation  
- rank  

This step does NOT choose chart type or encoding.

## Expected JSON Output
```json
{
  "intent": "trend",
  "target_columns": ["date", "sales"],
  "reasoning": "..."
}
```

## Prompt Template
```text
You are performing **Step 2: Analytical Intent Classification** in a multi-step Prompt-to-Vis pipeline.

Your job:
- Read the user query.
- Analyze the dataset schema and Step 1 output.
- Determine the analytical intent category that best fits the question:
  - "compare"
  - "trend"
  - "distribution"
  - "correlation"
  - "rank"
- Identify which columns the intent focuses on.
- Explain your reasoning in the `reasoning` field.

Important rules:
- You MUST output ONLY valid JSON following the schema.
- Do NOT include markdown, comments, or extra text.
- Respect Step 1 decisions and do NOT contradict them.

User query:
{USER_QUERY}

Dataset schema:
{DATASET_SCHEMA}

Sample rows:
{DATASET_SAMPLE}

Step 1 output:
{STEP1_OUTPUT}

Output JSON format (you MUST follow this exactly):
{OUTPUT_FORMAT}
```

---

# Step 3 — Aggregation & Transformation

## Purpose
Based on the user intent and dataset:

- Identify aggregations (mean, sum, count…)  
- Identify filters  
- Identify group-by fields  
- Identify derived fields (e.g., `year(Date)`)  

This step does NOT choose chart type or encoding.

## Expected JSON Output
```json
{
  "aggregations": [
    {"column": "IMDB Rating", "operation": "mean"}
  ],
  "filters": [
    {"column": "Year", "operator": ">=", "value": 2000}
  ],
  "group_by": ["Major Genre"],
  "reasoning": "..."
}
```

## Prompt Template
```text
You are performing **Step 3: Aggregation & Transformation** in the Prompt-to-Vis pipeline.

Your job:
- Based on the user query, dataset schema, and Steps 1–2, determine:
  - What aggregations are required (mean, sum, count, etc.)
  - What filters apply (column comparison rules)
  - What group-by fields are required
  - Whether derived fields are needed (e.g., extract year from date)
- Provide explanations in the `reasoning` field.

Important rules:
- Output ONLY valid JSON.
- Do NOT guess chart type.
- Do NOT assign encodings.
- Do NOT override logic from previous steps.

User query:
{USER_QUERY}

Dataset schema:
{DATASET_SCHEMA}

Sample rows:
{DATASET_SAMPLE}

Previous steps:
Step 1: {STEP1_OUTPUT}
Step 2: {STEP2_OUTPUT}

Output JSON format (you MUST follow this exactly):
{OUTPUT_FORMAT}
```

---

# Step 4 — Visualization Type Recommendation

## Purpose
Recommend the best Vega-Lite mark type based on analytical intent and transformations.

Allowed mark types:
- bar  
- line  
- point  
- area  
- rect  
- arc  
- boxplot  

## Expected JSON Output
```json
{
  "mark_type": "bar",
  "justification": "Bar charts are appropriate for categorical comparison."
}
```

## Prompt Template
```text
You are performing **Step 4: Visualization Type Recommendation** in the Prompt-to-Vis pipeline.

Your job:
- Recommend the best Vega-Lite mark type for the user query.
- Use the analytical intent from Step 2 and transformations from Step 3.
- Provide justification explaining why this mark type is appropriate.

Allowed mark types:
- "bar"
- "line"
- "point"
- "area"
- "rect"
- "arc"
- "boxplot"

Important rules:
- You MUST output ONLY valid JSON.
- Do NOT assign encodings (x, y, color).
- Do NOT contradict Steps 1–3.

Inputs:
User query: {USER_QUERY}
Step 1: {STEP1_OUTPUT}
Step 2: {STEP2_OUTPUT}
Step 3: {STEP3_OUTPUT}

Output JSON format:
{OUTPUT_FORMAT}
```

---

# Step 5 — Encoding Assignment

## Purpose
Assign fields to Vega-Lite encoding channels:

- x  
- y  
- color  
- size  
- tooltip  

Sort directives belong inside encodings.

## Expected JSON Output
```json
{
  "encodings": {
    "x": {"field": "Major Genre", "type": "nominal"},
    "y": {"field": "IMDB Rating", "aggregate": "mean", "type": "quantitative"},
    "color": {"field": "Major Genre", "type": "nominal", "legend": true},
    "tooltip": [
      {"field": "Major Genre", "type": "nominal"},
      {"field": "IMDB Rating", "aggregate": "mean", "type": "quantitative"}
    ]
  },
  "reasoning": "..."
}
```

## Prompt Template
```text
You are performing **Step 5: Encoding Assignment** in the Prompt-to-Vis pipeline.

Your job:
- Assign fields to Vega-Lite encoding channels such as:
  - x, y, color, size, tooltip
- Use the transformations (aggregation, filters, groupby) from Step 3.
- Use the selected mark type from Step 4.
- Only assign encodings allowed by the selected mark type.
- Provide reasoning explaining the chosen encodings.

Important rules:
- Output ONLY valid JSON.
- Do NOT change chart type from Step 4.
- Do NOT change aggregation logic from Step 3.
- Sort instructions must be included INSIDE encoding spec if needed.

Inputs:
Step 1: {STEP1_OUTPUT}
Step 2: {STEP2_OUTPUT}
Step 3: {STEP3_OUTPUT}
Step 4: {STEP4_OUTPUT}

Output JSON format:
{OUTPUT_FORMAT}
```

---

# Step 6 — Vega-Lite Draft Specification

## Purpose
Generate a **raw draft** of the Vega-Lite specification.  
Spec correctness is not required—`spec_builder.py` will fix issues.

## Expected JSON Output
```json
{
  "vl_spec_draft": {
    "mark": "bar",
    "encoding": {
      "x": {"field": "Major Genre", "type": "nominal"},
      "y": {"field": "IMDB Rating", "aggregate": "mean", "type": "quantitative"}
    }
  },
  "warnings": []
}
```

## Prompt Template
```text
You are performing **Step 6: Vega-Lite Draft Generation**.

Your job:
- Generate a raw Vega-Lite specification draft.
- Use all decisions from Steps 1–5 exactly as provided.
- Do NOT compute aggregated data manually; Vega-Lite will handle it.
- If unsure, make your best guess and describe uncertainty in `warnings`.

Important rules:
- Output ONLY valid JSON.
- Vega-Lite draft must contain:
  - "mark"
  - "encoding"
- Optional fields include:
  - "transform"
  - "tooltip"
  - "sort" inside encoding
- Do NOT include sample or derived data.

Inputs:
Step 1: {STEP1_OUTPUT}
Step 2: {STEP2_OUTPUT}
Step 3: {STEP3_OUTPUT}
Step 4: {STEP4_OUTPUT}
Step 5: {STEP5_OUTPUT}

Output JSON:
{OUTPUT_FORMAT}
```

---

_This concludes all prompt templates for the pipeline._
