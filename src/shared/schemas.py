# src/shared/schemas.py
# NOTE:
# This module defines the shared data contracts between:
# - LLM prompts (docs/06_prompts.md)
# - Pipeline steps (src/backend/pipeline/steps.py)
# - Frontend state (src/frontend/*)
#
# Treat these models as STABLE contracts.
# If you need to change them, update docs/04_pipeline_design.md
# and docs/06_prompts.md first.


from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field


# =========================
# Dataset metadata
# =========================

class DatasetField(BaseModel):
    """Metadata about a single column in the dataset."""

    name: str
    inferred_type: Literal["quantitative", "categorical", "temporal", "unknown"]
    description: Optional[str] = None
    example_values: Optional[List[Any]] = None
    is_integer: Optional[bool] = None  # True for integer-valued quantitative fields


class DatasetInfo(BaseModel):
    """
    Schema summary used in prompts.
    This is intentionally minimal and can be extended later if needed.
    """

    name: Optional[str] = None
    n_rows: Optional[int] = None
    n_columns: Optional[int] = None

    # Column-level information
    fields: List[DatasetField] = Field(default_factory=list)


# =========================
# Helper specs for steps
# =========================

class AggregationSpec(BaseModel):
    """
    Used in Step 3.
    Matches the JSON examples in docs/06_prompts.md:

    {
      "column": "IMDB Rating",
      "operation": "mean"
    }
    """

    column: str
    operation: str  # e.g. "sum", "mean", "count", ...


class FilterSpec(BaseModel):
    """
    Used in Step 3.
    Matches examples like:

    {
      "column": "Year",
      "operator": ">=",
      "value": 2000
    }
    """

    column: str
    operator: str  # e.g. "==", "!=", ">", ">=", "<", "<=", "in", "not in"
    value: Any


class EncodingSpec(BaseModel):
    """
    Used in Step 5.
    Matches Vega-Lite encoding structure, but kept generic.

    Example from docs/06_prompts.md:

    "x": {"field": "Major Genre", "type": "nominal"},
    "y": {"field": "IMDB Rating", "aggregate": "mean", "type": "quantitative"},
    "color": {"field": "Major Genre", "type": "nominal", "legend": true}
    """

    field: str
    type: Literal["quantitative", "temporal", "ordinal", "nominal"]

    # Optional Vega-Lite properties (subset, kept flexible)
    aggregate: Optional[str] = None
    bin: Optional[bool] = None
    timeUnit: Optional[str] = None

    legend: Optional[Any] = None
    sort: Optional[Any] = None
    scale: Optional[Dict[str, Any]] = None
    axis: Optional[Dict[str, Any]] = None
    tooltip: Optional[Any] = None


EncodingValue = Union[
    EncodingSpec,
    List[EncodingSpec],
    Dict[str, Any],
    List[Dict[str, Any]],
]


# =========================
# Step outputs
# =========================

class Step1Output(BaseModel):
    """
    Step 1 — Column Understanding & Selection

    Expected JSON (docs/06_prompts.md):

    {
      "selected_columns": ["colA", "colB"],
      "column_roles": {
        "colA": "categorical",
        "colB": "quantitative"
      },
      "reasoning": "..."
    }
    """

    selected_columns: List[str]
    column_roles: Dict[str, Literal["quantitative", "categorical", "temporal"]]
    reasoning: str


class Step2Output(BaseModel):
    """
    Step 2 — Analytical Intent Classification

    Expected JSON:

    {
      "intent": "trend",
      "target_columns": ["date", "sales"],
      "reasoning": "..."
    }
    """

    intent: Literal["compare", "trend", "distribution", "correlation", "rank"]
    target_columns: List[str]
    reasoning: str


class Step3Output(BaseModel):
    """
    Step 3 — Aggregation & Transformation

    Expected JSON:

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
    """

    aggregations: List[AggregationSpec] = Field(default_factory=list)
    filters: List[FilterSpec] = Field(default_factory=list)
    group_by: List[str] = Field(default_factory=list)
    reasoning: str


class Step4Output(BaseModel):
    """
    Step 4 — Visualization Type Recommendation

    Expected JSON:

    {
      "mark_type": "bar",
      "justification": "..."
    }
    """

    mark_type: Literal["bar", "line", "point", "area", "rect", "arc", "boxplot"]
    justification: str


class Step5Output(BaseModel):
    """
    Step 5 — Encoding Assignment

    Expected JSON in docs/06_prompts.md:

    {
      "encodings": {
        "x": {"field": "Major Genre", "type": "nominal"},
        "y": {"field": "IMDB Rating", "aggregate": "mean", "type": "quantitative"},
        "color": {"field": "Major Genre", "type": "nominal", "legend": true}
      },
      "reasoning": "..."
    }

    Note: 04_pipeline_design.md 里只写了 encodings，这里采用 superset 方案，加上 reasoning。
    """

    encodings: Dict[str, EncodingValue]
    reasoning: str


class Step6Output(BaseModel):
    """
    Step 6 — Vega-Lite Draft Spec Generation

    Expected JSON:

    {
      "vl_spec_draft": { ... },
      "warnings": []
    }
    """

    vl_spec_draft: Dict[str, Any]
    warnings: Optional[List[str]] = None


# =========================
# Global pipeline state
# =========================

class PipelineState(BaseModel):
    """
    Unified pipeline state passed between LangGraph nodes.
    Mirrors 04_pipeline_design.md.
    """

    dataset_info: DatasetInfo
    user_query: str

    step1: Optional[Step1Output] = None
    step2: Optional[Step2Output] = None
    step3: Optional[Step3Output] = None
    step4: Optional[Step4Output] = None
    step5: Optional[Step5Output] = None
    step6: Optional[Step6Output] = None

    # Filled by spec_builder
    final_spec: Optional[Dict[str, Any]] = None
