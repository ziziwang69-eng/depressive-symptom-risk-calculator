from __future__ import annotations

import hashlib
from pathlib import Path

import streamlit as st

from input_schema import (
    EDUCATION,
    LIFE_SATISFACTION,
    LIVING_CHILDREN,
    MEMORY,
    SELF_RATED_HEALTH,
    SEX,
    VISION,
    YES_NO,
)
from prediction_engine import InputValidationError, load_bundle, predict_from_user_inputs


APP_DIR = Path(__file__).resolve().parent
STYLE_PATH = APP_DIR / "assets" / "style.css"


st.set_page_config(
    page_title="Two-year risk of incident depressive symptoms",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def get_bundle():
    return load_bundle()


def option(
    label: str,
    values: list[int],
    default: int,
    key: str,
    labels: dict[int, str] | None = None,
    help_text: str | None = None,
) -> int:
    return int(
        st.selectbox(
            label,
            values,
            index=values.index(int(default)),
            format_func=(lambda value: labels[value]) if labels else (lambda value: str(value)),
            key=key,
            help=help_text,
        )
    )


def result_html(probability: float | None) -> str:
    if probability is None:
        needle = ""
        value = "—"
        helper = '<div class="result-helper">Enter the predictor values and select <b>Calculate probability</b>.</div>'
        aria_value = "No probability calculated"
    else:
        bounded_probability = min(1.0, max(0.0, float(probability)))
        rotation = bounded_probability * 180.0
        needle = (
            f'<div class="gauge-needle" style="transform: rotate({rotation:.6f}deg);"></div>'
            '<div class="gauge-hub"></div>'
        )
        value = f"{bounded_probability * 100.0:.1f}%"
        helper = '<div class="result-label">Incident depressive symptoms</div>'
        aria_value = f"Estimated two-year probability {bounded_probability * 100.0:.1f} percent"

    return f"""
    <div class="result-card" role="region" aria-label="{aria_value}">
      <div class="gauge-wrap" role="img" aria-label="Probability gauge from zero to one">
        <div class="gauge-dial">
          <div class="gauge-arc"><div class="gauge-cutout"></div></div>
          {needle}
        </div>
        <span class="gauge-zero">0</span>
        <span class="gauge-one">1</span>
      </div>
      <div class="result-eyebrow">Estimated 2-year probability</div>
      <div class="result-value">{value}</div>
      {helper}
    </div>
    """


bundle = get_bundle()
style = STYLE_PATH.read_text(encoding="utf-8")
st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)

example_mode = str(st.query_params.get("example", "0")) == "1"
example = bundle["illustrative_profile"]
defaults = example["model_values"]

st.markdown('<h1 class="app-title">Two-year risk of incident depressive symptoms</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Estimate the 2-year probability of incident depressive symptoms among adults aged 55 years or older.</div>',
    unsafe_allow_html=True,
)

input_column, result_column = st.columns([2.45, 1.0], gap="large")

with input_column:
    with st.container(border=True):
        left_column, right_column = st.columns(2, gap="medium")

        with left_column:
            instrument = st.selectbox(
                "Baseline CES-D instrument",
                ["CES-D-10", "CES-D-8"],
                index=0 if example["cesd_instrument"] == "CES-D-10" else 1,
                key="cesd_instrument",
            )
            mobility = option(
                "Mobility difficulties",
                list(range(0, 7)),
                int(defaults["Mobility difficulty count"]),
                "mobility",
            )
            iadl = option(
                "IADL difficulties",
                list(range(0, 5)),
                int(defaults["IADL difficulty count"]),
                "iadl",
            )
            self_health = option(
                "Self-rated health",
                list(range(1, 5)),
                int(defaults["Self-rated health"]),
                "self_health",
                SELF_RATED_HEALTH,
            )
            near_vision = option(
                "Near vision",
                list(range(1, 6)),
                int(defaults["Self-rated near vision"]),
                "near_vision",
                VISION,
            )
            immediate = option(
                "Immediate word recall",
                list(range(0, 11)),
                int(defaults["Immediate word recall"]),
                "immediate",
            )
            serial7 = option(
                "Serial 7s score",
                list(range(0, 6)),
                int(defaults["Serial 7s score"]),
                "serial7",
            )
            education = option(
                "Education level",
                list(range(0, 3)),
                int(defaults["Education level"]),
                "education",
                EDUCATION,
            )
            internet = option(
                "Internet use",
                [0, 1],
                int(defaults["Internet use"]),
                "internet",
                YES_NO,
            )

        with right_column:
            score_values = list(range(0, 10)) if instrument == "CES-D-10" else list(range(0, 3))
            score_default = int(example["cesd_score"]) if instrument == "CES-D-10" else min(1, max(score_values))
            cesd_score = option(
                "Baseline CES-D score",
                score_values,
                score_default,
                key=f"score_{instrument}",
                help_text="Accepted baseline scores: CES-D-10, 0–9; CES-D-8, 0–2.",
            )
            adl = option(
                "ADL difficulties",
                list(range(0, 6)),
                int(defaults["ADL difficulty count"]),
                "adl",
            )
            pain = option("Pain", [0, 1], int(defaults["Pain"]), "pain", YES_NO)
            distance_vision = option(
                "Distance vision",
                list(range(1, 6)),
                int(defaults["Self-rated distance vision"]),
                "distance_vision",
                VISION,
            )
            memory = option(
                "Self-rated memory",
                list(range(1, 6)),
                int(defaults["Self-rated memory"]),
                "memory",
                MEMORY,
            )
            delayed = option(
                "Delayed word recall",
                list(range(0, 11)),
                int(defaults["Delayed word recall"]),
                "delayed",
            )
            sex = option("Sex", [0, 1], int(defaults["Sex"]), "sex", SEX)
            satisfaction = option(
                "Life satisfaction",
                list(range(1, 6)),
                int(defaults["Life satisfaction"]),
                "satisfaction",
                LIFE_SATISFACTION,
            )
            children = option(
                "Number of living children",
                list(range(0, 4)),
                int(defaults["Number of living children"]),
                "children",
                LIVING_CHILDREN,
            )

        other_values = {
            "Mobility difficulty count": mobility,
            "Sex": sex,
            "Self-rated distance vision": distance_vision,
            "Pain": pain,
            "Life satisfaction": satisfaction,
            "Number of living children": children,
            "Self-rated health": self_health,
            "Delayed word recall": delayed,
            "Immediate word recall": immediate,
            "IADL difficulty count": iadl,
            "Self-rated near vision": near_vision,
            "Serial 7s score": serial7,
            "Internet use": internet,
            "Education level": education,
            "ADL difficulty count": adl,
            "Self-rated memory": memory,
        }
        fingerprint = hashlib.sha256(
            repr((instrument, cesd_score, sorted(other_values.items()))).encode("utf-8")
        ).hexdigest()
        calculate = st.button(
            "Calculate probability",
            key="calculate",
            type="primary",
            use_container_width=True,
        )

calculation_error: str | None = None
if calculate:
    try:
        st.session_state["calculated_probability"] = predict_from_user_inputs(
            instrument,
            cesd_score,
            other_values,
            bundle=bundle,
        )
        st.session_state["calculated_fingerprint"] = fingerprint
    except InputValidationError as error:
        calculation_error = str(error)
        st.session_state.pop("calculated_fingerprint", None)

if example_mode:
    probability = float(example["expected_probability"])
elif st.session_state.get("calculated_fingerprint") == fingerprint:
    probability = float(st.session_state["calculated_probability"])
else:
    probability = None

with result_column:
    if calculation_error:
        st.error(calculation_error)
    st.markdown(result_html(probability), unsafe_allow_html=True)
