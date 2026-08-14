from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping


MODEL_BUNDLE_PATH = Path(__file__).resolve().parent / "model_bundle" / "lr_m2_20_models.json"


class InputValidationError(ValueError):
    """Raised when a value is outside the locked model's applicability domain."""


def load_bundle(path: Path | str = MODEL_BUNDLE_PATH) -> dict[str, Any]:
    bundle_path = Path(path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    if bundle.get("bundle_version") != "1.0.0":
        raise RuntimeError("Unsupported model bundle version.")
    if len(bundle.get("models", [])) != 20:
        raise RuntimeError("The locked model bundle must contain exactly 20 models.")
    if bundle.get("aggregation") != "arithmetic mean of 20 predicted probabilities":
        raise RuntimeError("Unexpected multiple-imputation aggregation rule.")
    return bundle


def cesd_burden(instrument: str, score: int) -> float:
    if instrument == "CES-D-10":
        if score not in range(0, 10):
            raise InputValidationError(
                "CES-D-10 must be between 0 and 9 for this baseline screen-negative cohort."
            )
        return score / 9.0
    if instrument == "CES-D-8":
        if score not in range(0, 3):
            raise InputValidationError(
                "CES-D-8 must be between 0 and 2 for this baseline screen-negative cohort."
            )
        return score / 2.0
    raise InputValidationError("CES-D instrument must be CES-D-10 or CES-D-8.")


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp_negative = math.exp(-value)
        return 1.0 / (1.0 + exp_negative)
    exp_positive = math.exp(value)
    return exp_positive / (1.0 + exp_positive)


def validate_model_inputs(
    bundle: Mapping[str, Any], values: Mapping[str, float | int]
) -> dict[str, float]:
    schema = bundle["input_schema"]
    required = set(bundle["feature_order"])
    supplied = set(values)
    if supplied != required:
        missing = sorted(required - supplied)
        extra = sorted(supplied - required)
        raise InputValidationError(f"Input fields differ from the locked schema; missing={missing}, extra={extra}.")

    clean: dict[str, float] = {}
    for feature in bundle["feature_order"]:
        raw = values[feature]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise InputValidationError(f"{feature} must be numeric.")
        value = float(raw)
        if not math.isfinite(value):
            raise InputValidationError(f"{feature} must be finite.")
        allowed = [float(item) for item in schema[feature]["allowed_values"]]
        if value not in allowed:
            raise InputValidationError(
                f"{feature}={value:g} is outside the allowed values {allowed}."
            )
        clean[feature] = value
    return clean


def predict_probability(
    values: Mapping[str, float | int],
    bundle: Mapping[str, Any] | None = None,
) -> float:
    locked = load_bundle() if bundle is None else dict(bundle)
    clean = validate_model_inputs(locked, values)
    continuous = locked["continuous_order"]
    binary = locked["binary_order"]
    model_order = continuous + binary
    probabilities: list[float] = []

    for model in locked["models"]:
        transformed: list[float] = []
        for feature, mean, scale in zip(
            continuous,
            model["continuous_mean"],
            model["continuous_scale"],
            strict=True,
        ):
            if scale <= 0:
                raise RuntimeError(f"Non-positive scale for {feature}.")
            transformed.append((clean[feature] - float(mean)) / float(scale))
        transformed.extend(clean[feature] for feature in binary)
        if len(transformed) != len(model_order):
            raise RuntimeError("Transformed input length differs from the locked model order.")
        linear_predictor = float(model["intercept"]) + sum(
            float(coefficient) * value
            for coefficient, value in zip(model["coefficients"], transformed, strict=True)
        )
        probabilities.append(_sigmoid(linear_predictor))

    probability = sum(probabilities) / len(probabilities)
    if not 0.0 <= probability <= 1.0:
        raise RuntimeError("The calculated probability is outside [0, 1].")
    return probability


def predict_from_user_inputs(
    instrument: str,
    score: int,
    other_values: Mapping[str, float | int],
    bundle: Mapping[str, Any] | None = None,
) -> float:
    values = dict(other_values)
    values["Baseline subthreshold CES-D burden"] = cesd_burden(instrument, score)
    return predict_probability(values, bundle=bundle)
