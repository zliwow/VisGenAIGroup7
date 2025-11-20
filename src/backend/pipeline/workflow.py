# src/backend/pipeline/workflow.py

from __future__ import annotations

from typing import Dict, Literal, TypedDict, Optional

import pandas as pd

from src.shared.schemas import DatasetField, DatasetInfo, PipelineState
from src.backend.llm.base_client import BaseLLMClient
from src.backend.llm.openai_client import OpenAIClient
from src.backend.llm.groq_client import GroqClient
from src.backend.pipeline.steps import (
    run_step1,
    run_step2,
    run_step3,
    run_step4,
    run_step5,
    run_step6,
)
from src.backend.vega.spec_builder import build_spec


Provider = Literal["groq", "openai"]  # openai: TODO


class PipelineRunResult(TypedDict):
    state: PipelineState
    spec: Optional[Dict]


def _infer_field_type(dtype) -> str:
    """
    Map pandas dtype to our simplified type space.
    """
    if pd.api.types.is_numeric_dtype(dtype):
        return "quantitative"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "temporal"
    # TODO[pipeline]: add better detection for booleans / categoricals if needed.
    return "categorical"


def build_dataset_info(df: pd.DataFrame, name: Optional[str] = None) -> DatasetInfo:
    """
    Construct DatasetInfo from a pandas DataFrame.
    """
    fields = []
    for col in df.columns:
        inferred = _infer_field_type(df[col].dtype)
        example_values = df[col].dropna().unique()[:3].tolist()

        fields.append(
            DatasetField(
                name=col,
                inferred_type=inferred,
                example_values=example_values,
            )
        )

    return DatasetInfo(
        name=name,
        n_rows=len(df),
        n_columns=len(df.columns),
        fields=fields,
    )


def make_llm_client(provider: Provider, api_key: str, model_name: str) -> BaseLLMClient:
    """
    Factory for LLM clients.
    """
    if provider == "groq":
        return GroqClient(api_key=api_key, model_name=model_name)
    if provider == "openai":
        return OpenAIClient(api_key=api_key, model_name=model_name)
    raise NotImplementedError(f"Provider '{provider}' is not implemented yet.")


def run_pipeline(
    df: pd.DataFrame,
    user_query: str,
    *,
    provider: Provider,
    model_name: str,
    api_key: str,
    dataset_name: Optional[str] = None,
) -> PipelineRunResult:
    """
    Run the full 6-step Prompt-to-Vis pipeline and return both state and final spec.

    Minimal version: always runs steps 1→6 in sequence.
    """
    dataset_info = build_dataset_info(df, name=dataset_name)
    state = PipelineState(dataset_info=dataset_info, user_query=user_query)

    llm_client = make_llm_client(provider=provider, api_key=api_key, model_name=model_name)

    # Sequential execution; no LangChain/LangGraph yet.
    # TODO[pipeline]:
    #   - When we add JSON-editable step panels in the UI,
    #     refactor this sequential execution into a LangGraph / LangChain workflow
    #     so that we can re-run the pipeline starting from an arbitrary step (e.g., from step 3).
    state = run_step1(state, df, llm_client)
    state = run_step2(state, df, llm_client)
    state = run_step3(state, df, llm_client)
    state = run_step4(state, df, llm_client)
    state = run_step5(state, df, llm_client)
    state = run_step6(state, df, llm_client)

    final_spec = build_spec(state)
    state.final_spec = final_spec

    return PipelineRunResult(state=state, spec=final_spec)
