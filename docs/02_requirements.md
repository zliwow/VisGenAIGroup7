# Project Requirements

## 1. Problem Statement

Most LLM-driven Prompt-to-Visualization systems operate as **black boxes**.  
Users cannot inspect the intermediate reasoning that transforms a natural language query into a visualization, nor can they adjust individual reasoning steps.

This lack of transparency limits:
- **Trust** in the model’s decision-making  
- **Correctability** when results are wrong  
- **Learning value** for students or analysts

Our system aims to create a **transparent Prompt-to-Vis pipeline**, where users can view—and optionally edit—each intermediate reasoning stage before a chart is generated.

---

## 2. Project Goals

The project is a prototype that enables:

### **G1. Transparent reasoning**
Expose the full 6-step reasoning pipeline from natural language → Vega-Lite chart.

### **G2. Interactivity**
Allow users to modify intermediate step outputs and re-run downstream steps.

### **G3. Multiple L L M Backends**
Support at least two providers:
- OpenAI API
- Groq API

### **G4. Modular architecture**
A clean separation of:
- Streamlit frontend
- LangChain/LangGraph pipeline backend
- Pydantic schemas for structured data
- Vega-Lite rendering layer

### **G5. Minimal friction for users**
Single page UI that works with CSV uploads or sample data.

---

## 3. User Stories

### **US-01 — Pipeline Transparency**
“As a beginner, I want to see how the system interprets my query step by step so I can understand why a particular chart is generated.”

### **US-02 — Editable Reasoning**
“As a data analyst, I want to adjust aggregation, filters, or encodings manually so that I can refine the chart according to my needs.”

### **US-03 — Easy Setup**
“As a user, I want to enter my API key and upload a CSV without installing complex tools.”

### **US-04 — Model Flexibility**
“As a power user, I want to choose between Groq and OpenAI models for experimentation.”

---

## 4. Functional Requirements

### **4.1 Data Input**
- FR-01: Users can upload a CSV file.
- FR-02: System automatically extracts the table schema (column names & inferred types).
- FR-03: Users can preview the dataset in a table component.

### **4.2 L L M Provider & Model Selection**
- FR-04: Users can select the API provider (OpenAI / Groq).
- FR-05: Users can pick from available models from that provider.
- FR-06: API keys can be provided via Streamlit sidebar or `.streamlit/secrets.toml`.

### **4.3 Six-Step Reasoning Pipeline**
The backend must execute the following steps in sequence:

1. Column Selection  
2. Intent Classification  
3. Aggregation & Filtering  
4. Plot Type Recommendation  
5. Encoding Assignment  
6. Vega-Lite Spec Generation  

Concrete requirements:

- FR-07: Each step must output structured JSON.
- FR-08: Each step must include a short natural-language “reason/explanation”.
- FR-09: Steps must be implemented as LangGraph nodes.
- FR-10: Steps must store outputs in a centralized state object.

### **4.4 Editing & Re-running**
- FR-11: Users must be able to edit outputs from any intermediate step.
- FR-12: Editing step N must trigger recomputation of steps N+1 ... 6.
- FR-13: The system must maintain state consistency after edits.

### **4.5 Vega-Lite Chart Rendering**
- FR-14: Convert final pipeline output into a valid Vega-Lite specification.
- FR-15: Render the chart using Altair in Streamlit.
- FR-16: Display the raw Vega-Lite JSON in an expandable panel.

### **4.6 Error Handling**
- FR-17: When L L M output is invalid / malformed JSON, provide a warning.
- FR-18: System may attempt auto-repair or re-ask the model.
- FR-19: Invalid user edits must be validated before regeneration.

---

## 5. Non-Functional Requirements (NFR)

### **5.1 Usability**
- NFR-01: System must run entirely via Streamlit web UI.
- NFR-02: UI must be single-page and intuitive.
- NFR-03: No installation beyond Python dependencies.

### **5.2 Maintainability**
- NFR-04: Code must follow the folder structure defined in the project.
- NFR-05: All pipeline step outputs must use Pydantic schemas.
- NFR-06: No business logic inside Streamlit views.

### **5.3 Reliability**
- NFR-07: Errors must not break the entire app.
- NFR-08: Invalid JSON from L L M calls must be caught and surfaced.

### **5.4 Performance**
- NFR-09: Use LangChain caching when possible.
- NFR-10: Response time should remain under **5 seconds** for typical queries on Groq/OpenAI.

---

## 6. Out of Scope

These items are **explicitly excluded**:

- Multi-table joins  
- Automatic data cleaning or data imputation  
- Multi-view dashboards  
- Predictive analytics or ML features  
- Complex data transformations (pivot, melt, window functions)  
- Support for more than one chart at once  
- Authentication, user accounts, database persistence  

---

## 7. Final Deliverables

The prototype must deliver:

- A working Streamlit app  
- Fully functional 6-step LangGraph pipeline  
- Vega-Lite visualization  
- Editable reasoning steps  
- Clean architecture aligned with docs  
- Clear code organization supportive of vibe coding  
