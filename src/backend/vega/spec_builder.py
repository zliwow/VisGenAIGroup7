# src/backend/vega/spec_builder.py

from __future__ import annotations

from typing import Any, Dict, Optional

from src.shared.schemas import PipelineState, EncodingSpec, EncodingValue, DatasetField


def _encoding_to_dict(enc: EncodingSpec) -> Dict[str, Any]:
    """
    Convert EncodingSpec (Pydantic) to a Vega-Lite encoding dict.
    """
    return enc.model_dump(exclude_none=True)


def _encoding_value_to_object(value: EncodingValue) -> Any:
    """
    Normalize EncodingValue union into primitives Vega-Lite accepts.
    """
    if isinstance(value, EncodingSpec):
        return _encoding_to_dict(value)

    if isinstance(value, list):
        # List of EncodingSpec -> convert element-wise
        converted = []
        for item in value:
            if isinstance(item, EncodingSpec):
                converted.append(_encoding_to_dict(item))
            else:
                converted.append(item)
        return converted

    return value


def _get_field_metadata(state: PipelineState, field_name: str) -> Optional[DatasetField]:
    """
    Look up field metadata by name from the dataset info.
    """
    for field in state.dataset_info.fields:
        if field.name == field_name:
            return field
    return None


def _apply_integer_formatting(encoding: Dict[str, Any], state: PipelineState) -> None:
    """
    Apply integer formatting (format: "d") to encodings for integer-valued fields.
    Prevents integer fields from being incorrectly treated as temporal.
    Modifies the encoding dict in place.
    """
    for enc_value in encoding.values():
        if isinstance(enc_value, dict) and "field" in enc_value:
            field_name = enc_value["field"]
            field_meta = _get_field_metadata(state, field_name)

            if field_meta and field_meta.is_integer:
                # Force type to quantitative (not temporal) for integer fields
                # This prevents Year fields from being interpreted as timestamps
                if enc_value.get("type") == "temporal":
                    enc_value["type"] = "quantitative"

                # Add axis formatting for integer display (no decimal places)
                if "axis" not in enc_value:
                    enc_value["axis"] = {}
                if isinstance(enc_value["axis"], dict) and "format" not in enc_value["axis"]:
                    enc_value["axis"]["format"] = "d"

        # Handle tooltip arrays
        elif isinstance(enc_value, list):
            for item in enc_value:
                if isinstance(item, dict) and "field" in item:
                    field_name = item["field"]
                    field_meta = _get_field_metadata(state, field_name)

                    if field_meta and field_meta.is_integer:
                        # Force quantitative type
                        if item.get("type") == "temporal":
                            item["type"] = "quantitative"

                        if "format" not in item:
                            item["format"] = "d"


def _build_fallback_spec(state: PipelineState) -> Dict[str, Any]:
    """
    Fallback Vega-Lite spec if step4/step5 are missing.

    Simple heuristic:
      - Use first field on x; second on y if possible.
      - Use 'bar' if one categorical + one quantitative; else 'point'.
    """
    fields = state.dataset_info.fields
    if len(fields) == 0:
        return {}

    x_field = fields[0]
    y_field = fields[1] if len(fields) > 1 else None

    mark = "bar"
    if y_field and x_field.inferred_type == "categorical" and y_field.inferred_type == "quantitative":
        mark = "bar"
    else:
        mark = "point"

    encoding: Dict[str, Any] = {
        "x": {"field": x_field.name, "type": x_field.inferred_type},
    }
    if y_field:
        encoding["y"] = {"field": y_field.name, "type": y_field.inferred_type}

    # Apply integer formatting
    _apply_integer_formatting(encoding, state)

    return {
        "mark": mark,
        "encoding": encoding,
    }


def build_spec(state: PipelineState) -> Dict[str, Any]:
    """
    Build a Vega-Lite spec from the pipeline state.

    Minimal version:
      - Prefer Step4 (mark_type) + Step5 (encodings).
      - Fall back to a very simple spec if they are missing.
    """
    if state.step4 is not None and state.step5 is not None:
        encoding = {
            channel: _encoding_value_to_object(spec)
            for channel, spec in state.step5.encodings.items()
        }

        # Apply integer formatting to preserve integer display (e.g., 2016 not 2016.0)
        _apply_integer_formatting(encoding, state)

        spec: Dict[str, Any] = {
            "mark": state.step4.mark_type,
            "encoding": encoding,
        }

        # TODO[vega]:
        #   - Integrate Step3 (aggregations/filters) into Vega-Lite transforms.
        #   - Optionally merge Step6 (vl_spec_draft) with this builder.
        return spec

    # Fallback
    return _build_fallback_spec(state)
