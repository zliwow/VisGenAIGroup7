# src/backend/llm/prompt_loader.py

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Literal


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_PATH = PROJECT_ROOT / "docs" / "06_prompts.md"


StepName = Literal["step1", "step2", "step3", "step4", "step5", "step6"]


@lru_cache(maxsize=1)
def _read_prompts_file() -> str:
    """Read the full 06_prompts.md content (cached)."""
    return PROMPTS_PATH.read_text(encoding="utf-8")


def _extract_step_section(raw: str, step_number: int) -> str:
    """
    Get the markdown section for a given step, e.g. between:

        # Step 1 — ...
        ...
        # Step 2 — ...

    If it is the last step, slice until end of file.
    """
    # Pattern like "# Step 1" (allow extra text after the number)
    pattern = rf"^#\s*Step\s+{step_number}\b.*$"
    matches = list(re.finditer(pattern, raw, flags=re.MULTILINE))
    if not matches:
        raise ValueError(f"Could not find header for Step {step_number} in 06_prompts.md")

    start = matches[0].start()

    # Find next "# Step {n+1}" header (if any) to bound the section
    next_pattern = rf"^#\s*Step\s+{step_number + 1}\b.*$"
    next_match = re.search(next_pattern, raw[start + 1 :], flags=re.MULTILINE)
    if next_match:
        end = start + 1 + next_match.start()
    else:
        end = len(raw)

    return raw[start:end]


def _extract_text_block(section: str) -> str:
    """
    Extract the first ```text ... ``` code block from a section.

    The prompts are written as:

        ## Prompt Template
        ```text
        ...
        ```
    """
    code_block_pattern = r"```text(.*?)```"
    match = re.search(code_block_pattern, section, flags=re.DOTALL)
    if not match:
        raise ValueError("No ```text``` block found in step section.")
    # Strip leading/trailing whitespace
    return match.group(1).strip()


def load_step_prompt(step: StepName) -> str:
    """
    Load the prompt template for a given step.

    Example:
        prompt = load_step_prompt("step1")
        prompt = prompt.format(
            USER_QUERY=user_query,
            DATASET_SCHEMA=schema_str,
            DATASET_SAMPLE=sample_str,
            OUTPUT_FORMAT=output_format_json_str,
            STEP1_OUTPUT=step1_json_str,
            ...
        )

        TODO:
      - Optionally validate required placeholders per step
        (e.g., ensure {USER_QUERY}, {DATASET_SCHEMA} exist for step1).
    """
    raw = _read_prompts_file()

    # Convert "step1" -> 1, etc.
    step_number = int(step.replace("step", ""))
    section = _extract_step_section(raw, step_number)
    template = _extract_text_block(section)
    return template
