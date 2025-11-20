# src/backend/pipeline/steps.py

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

from src.shared.schemas import (
    DatasetInfo,
    PipelineState,
    Step1Output,
    Step2Output,
    Step3Output,
    Step4Output,
    Step5Output,
    Step6Output,
)
from src.backend.llm.base_client import BaseLLMClient
from src.backend.llm.prompt_loader import load_step_prompt


# =========================
# Helpers
# =========================


@dataclass
class PromptContext:
    dataset_schema: str
    dataset_sample: str


class SafeFormatDict(dict):
    """
    A dict for str.format_map that leaves {MISSING_KEY} as-is instead of raising KeyError.
    """

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def build_dataset_schema_str(dataset_info: DatasetInfo) -> str:
    """
    Convert DatasetInfo into a human-readable schema string used in prompts.

    Example:

        - title: IMDB movies
        - fields:
          - title (categorical)
          - year (temporal)
          - rating (quantitative)
    """
    lines = []

    if dataset_info.name:
        lines.append(f"Dataset name: {dataset_info.name}")

    lines.append(f"Rows: {dataset_info.n_rows}")
    lines.append(f"Columns: {dataset_info.n_columns}")
    lines.append("Fields:")

    for field in dataset_info.fields:
        lines.append(f"- {field.name} ({field.inferred_type})")

    return "\n".join(lines)


def build_dataset_sample_str(df: pd.DataFrame, max_rows: int = 3) -> str:
    """
    A small sample of the data as plain text.

    TODO[pipeline]:
      - If needed, truncate very wide tables more aggressively.
    """
    head = df.head(max_rows)
    return head.to_string(index=False)


def _strip_code_fences(raw: str) -> str:
    """
    Remove wrapping ``` ``` or ```json ``` fences if present.
    """
    text = raw.strip()
    pattern = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", flags=re.DOTALL | re.IGNORECASE)
    match = pattern.match(text)
    if match:
        return match.group(1).strip()
    return text


def _extract_json_payload(raw: str) -> str:
    """
    Strip fences and trim any text before/after the first JSON object/array.
    """
    text = _strip_code_fences(raw)

    # Trim leading text until first { or [
    start_idx = None
    for idx, ch in enumerate(text):
        if ch in "{[":
            start_idx = idx
            break
    if start_idx is not None:
        text = text[start_idx:]

    # Trim trailing text after last } or ]
    end_idx = None
    for idx in range(len(text) - 1, -1, -1):
        if text[idx] in "}]":
            end_idx = idx + 1
            break
    if end_idx is not None:
        text = text[:end_idx]

    return text.strip()


def _parse_json_to_model(raw: str, model_cls):
    """
    Parse LLM output as JSON into a Pydantic model and surface friendlier errors.
    """
    if raw is None or not raw.strip():
        raise ValueError(f"{model_cls.__name__}: empty response from LLM.")

    cleaned = _extract_json_payload(raw)
    if not cleaned:
        raise ValueError(f"{model_cls.__name__}: no JSON object found in response.")

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        snippet = cleaned.strip()
        if len(snippet) > 500:
            snippet = snippet[:500] + "...<truncated>"
        raise ValueError(
            f"{model_cls.__name__}: invalid JSON ({exc.msg} at line {exc.lineno}, column {exc.colno}). "
            f"Raw output snippet: {snippet}"
        ) from exc

    return model_cls.model_validate(data)


def _build_common_context(state: PipelineState, ctx: PromptContext) -> Dict[str, Any]:
    """
    Common placeholders shared by most steps.
    """
    return {
        "USER_QUERY": state.user_query,
        "DATASET_SCHEMA": ctx.dataset_schema,
        "DATASET_SAMPLE": ctx.dataset_sample,
    }


def _get_output_format(step: str) -> str:
    """
    Provide a structured JSON example for the {OUTPUT_FORMAT} placeholder.
    Mirrors docs/06_prompts.md expectations.
    """
    try:
        return STEP_OUTPUT_FORMATS[step]
    except KeyError as exc:
        raise ValueError(f"No output format registered for {step}") from exc


STEP_OUTPUT_FORMATS: Dict[str, str] = {
    "step1": json.dumps(
        {
            "selected_columns": ["column_a", "column_b"],
            "column_roles": {
                "column_a": "categorical",
                "column_b": "quantitative",
            },
            "reasoning": "Explain why each column matters.",
        },
        indent=2,
    ),
    "step2": json.dumps(
        {
            "intent": "trend",
            "target_columns": ["date", "value"],
            "reasoning": "Explain how the intent was determined.",
        },
        indent=2,
    ),
    "step3": json.dumps(
        {
            "aggregations": [{"column": "Rating", "operation": "mean"}],
            "filters": [{"column": "Year", "operator": ">=", "value": 2000}],
            "group_by": ["Genre"],
            "reasoning": "Explain filters/aggregations.",
        },
        indent=2,
    ),
    "step4": json.dumps(
        {
            "mark_type": "bar",
            "justification": "Explain why this mark suits the intent.",
        },
        indent=2,
    ),
    "step5": json.dumps(
        {
            "encodings": {
                "x": {"field": "Genre", "type": "nominal"},
                "y": {
                    "field": "Rating",
                    "aggregate": "mean",
                    "type": "quantitative",
                },
                "color": {"field": "Year", "type": "temporal"},
                "tooltip": [
                    {"field": "Genre", "type": "nominal"},
                    {
                        "field": "Rating",
                        "aggregate": "mean",
                        "type": "quantitative",
                    },
                ],
            },
            "reasoning": "Explain encoding assignments.",
        },
        indent=2,
    ),
    "step6": json.dumps(
        {
            "vl_spec_draft": {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "mark": "bar",
                "encoding": {},
                "data": {"name": "DATA_PLACEHOLDER"},
            },
            "warnings": [],
        },
        indent=2,
    ),
}


# =========================
# Step functions
# =========================


def run_step1(
    state: PipelineState,
    df: pd.DataFrame,
    llm_client: BaseLLMClient,
) -> PipelineState:
    """
    Step 1 — Column Understanding & Selection.
    """
    ctx = PromptContext(
        dataset_schema=build_dataset_schema_str(state.dataset_info),
        dataset_sample=build_dataset_sample_str(df),
    )

    template = load_step_prompt("step1")

    context = _build_common_context(state, ctx)
    context["OUTPUT_FORMAT"] = _get_output_format("step1")

    prompt = template.format_map(SafeFormatDict(context))

    raw = llm_client.generate(prompt)
    result = _parse_json_to_model(raw, Step1Output)

    state.step1 = result
    return state


def run_step2(
    state: PipelineState,
    df: pd.DataFrame,
    llm_client: BaseLLMClient,
) -> PipelineState:
    """
    Step 2 — Analytical Intent Classification.
    """
    ctx = PromptContext(
        dataset_schema=build_dataset_schema_str(state.dataset_info),
        dataset_sample=build_dataset_sample_str(df),
    )

    template = load_step_prompt("step2")

    context = _build_common_context(state, ctx)
    context["STEP1_OUTPUT"] = (
        state.step1.model_dump_json(indent=2) if state.step1 is not None else ""
    )
    context["OUTPUT_FORMAT"] = _get_output_format("step2")

    prompt = template.format_map(SafeFormatDict(context))

    raw = llm_client.generate(prompt)
    result = _parse_json_to_model(raw, Step2Output)

    state.step2 = result
    return state


def run_step3(
    state: PipelineState,
    df: pd.DataFrame,
    llm_client: BaseLLMClient,
) -> PipelineState:
    """
    Step 3 — Aggregation & Transformation.
    """
    ctx = PromptContext(
        dataset_schema=build_dataset_schema_str(state.dataset_info),
        dataset_sample=build_dataset_sample_str(df),
    )

    template = load_step_prompt("step3")

    context = _build_common_context(state, ctx)
    context["STEP1_OUTPUT"] = (
        state.step1.model_dump_json(indent=2) if state.step1 is not None else ""
    )
    context["STEP2_OUTPUT"] = (
        state.step2.model_dump_json(indent=2) if state.step2 is not None else ""
    )
    context["OUTPUT_FORMAT"] = _get_output_format("step3")

    prompt = template.format_map(SafeFormatDict(context))

    raw = llm_client.generate(prompt)
    result = _parse_json_to_model(raw, Step3Output)

    state.step3 = result
    return state


def run_step4(
    state: PipelineState,
    df: pd.DataFrame,
    llm_client: BaseLLMClient,
) -> PipelineState:
    """
    Step 4 — Visualization Type Recommendation.
    """
    ctx = PromptContext(
        dataset_schema=build_dataset_schema_str(state.dataset_info),
        dataset_sample=build_dataset_sample_str(df),
    )

    template = load_step_prompt("step4")

    context = _build_common_context(state, ctx)
    context["STEP1_OUTPUT"] = (
        state.step1.model_dump_json(indent=2) if state.step1 is not None else ""
    )
    context["STEP2_OUTPUT"] = (
        state.step2.model_dump_json(indent=2) if state.step2 is not None else ""
    )
    context["STEP3_OUTPUT"] = (
        state.step3.model_dump_json(indent=2) if state.step3 is not None else ""
    )
    context["OUTPUT_FORMAT"] = _get_output_format("step4")

    prompt = template.format_map(SafeFormatDict(context))

    raw = llm_client.generate(prompt)
    result = _parse_json_to_model(raw, Step4Output)

    state.step4 = result
    return state


def run_step5(
    state: PipelineState,
    df: pd.DataFrame,
    llm_client: BaseLLMClient,
) -> PipelineState:
    """
    Step 5 — Encoding Assignment.
    """
    ctx = PromptContext(
        dataset_schema=build_dataset_schema_str(state.dataset_info),
        dataset_sample=build_dataset_sample_str(df),
    )

    template = load_step_prompt("step5")

    context = _build_common_context(state, ctx)
    context["STEP1_OUTPUT"] = (
        state.step1.model_dump_json(indent=2) if state.step1 is not None else ""
    )
    context["STEP2_OUTPUT"] = (
        state.step2.model_dump_json(indent=2) if state.step2 is not None else ""
    )
    context["STEP3_OUTPUT"] = (
        state.step3.model_dump_json(indent=2) if state.step3 is not None else ""
    )
    context["STEP4_OUTPUT"] = (
        state.step4.model_dump_json(indent=2) if state.step4 is not None else ""
    )
    context["OUTPUT_FORMAT"] = _get_output_format("step5")

    prompt = template.format_map(SafeFormatDict(context))

    raw = llm_client.generate(prompt)
    result = _parse_json_to_model(raw, Step5Output)

    state.step5 = result
    return state


def run_step6(
    state: PipelineState,
    df: pd.DataFrame,
    llm_client: BaseLLMClient,
) -> PipelineState:
    """
    Step 6 — Vega-Lite Draft Spec Generation.
    """
    ctx = PromptContext(
        dataset_schema=build_dataset_schema_str(state.dataset_info),
        dataset_sample=build_dataset_sample_str(df),
    )

    template = load_step_prompt("step6")

    context = _build_common_context(state, ctx)
    context["STEP1_OUTPUT"] = (
        state.step1.model_dump_json(indent=2) if state.step1 is not None else ""
    )
    context["STEP2_OUTPUT"] = (
        state.step2.model_dump_json(indent=2) if state.step2 is not None else ""
    )
    context["STEP3_OUTPUT"] = (
        state.step3.model_dump_json(indent=2) if state.step3 is not None else ""
    )
    context["STEP4_OUTPUT"] = (
        state.step4.model_dump_json(indent=2) if state.step4 is not None else ""
    )
    context["STEP5_OUTPUT"] = (
        state.step5.model_dump_json(indent=2) if state.step5 is not None else ""
    )
    context["OUTPUT_FORMAT"] = _get_output_format("step6")

    prompt = template.format_map(SafeFormatDict(context))

    raw = llm_client.generate(prompt)
    result = _parse_json_to_model(raw, Step6Output)

    state.step6 = result
    return state
