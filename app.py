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


def option(label: str, values: list[int], default: int, key: str, labels: dict[int, str] | None = None, help_text: str | None = None) -> int:
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


def section_heading(text: str) -> None:
    st.markdown(
        f'<div class="section-title">{text}</div><div class="section-rule"></div>',
        unsafe_allow_html=True,
    )


def result_html(probability: float | None, example_mode: bool) -> str:
    if probability is None:
        return """
        <div class="result-card">
          <div class="result-eyebrow">Individual estimate</div>
          <div class="result-placeholder">Complete the 17 predictor fields and select <b>Calculate probability</b>.</div>
          <div class="model-meta">L2-penalized logistic regression<br>17 predictors · 20-imputation probability ensemble<br>CHARLS development · HRS external validation</div>
        </div>
        """
    percentage = probability * 100.0
    badge = '<div class="example-badge">Illustrative profile · not a real participant</div>' if example_mode else ""
    return f"""
    <div class="result-card">
      <div class="result-eyebrow">Estimated 2-year probability</div>
      {badge}
      <div class="result-value">{percentage:.1f}%</div>
      <div class="result-label">Incident depressive symptoms</div>
      <div class="risk-track">
        <div class="risk-track-fill" style="width:{percentage:.3f}%"></div>
        <div class="risk-track-marker" style="left:{percentage:.3f}%"></div>
      </div>
      <div class="risk-scale"><span>0%</span><span>100%</span></div>
      <div class="result-copy">This is a continuous model estimate of becoming CES-D threshold-positive within 2 years. It is not a diagnosis and does not assign a clinical risk category.</div>
      <div class="model-meta">L2-penalized logistic regression<br>17 predictors · 20-imputation probability ensemble<br>CHARLS development · HRS external validation</div>
    </div>
    """


bundle = get_bundle()
style = STYLE_PATH.read_text(encoding="utf-8")
st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)

example_mode = str(st.query_params.get("example", "0")) == "1"
example = bundle["illustrative_profile"]
defaults = example["model_values"]

st.markdown('<div class="app-kicker">Externally validated prediction model</div>', unsafe_allow_html=True)
st.markdown('<h1 class="app-title">Two-year risk of incident depressive symptoms</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">A research-use calculator for adults aged 55 years or older who are CES-D screen-negative at baseline.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="eligibility-note"><b>Applicability:</b> use only for baseline CES-D-10 scores of 0–9 or CES-D-8 scores of 0–2. Scores above these ranges fall outside the study cohort.</div>',
    unsafe_allow_html=True,
)

column_physical, column_cognitive, column_social, column_result = st.columns(
    [1.07, 1.0, 1.08, 0.9], gap="medium"
)

with column_physical:
    with st.container(border=True):
        section_heading("Depressive burden and physical health")
        instrument = st.selectbox(
            "Baseline CES-D instrument",
            ["CES-D-10", "CES-D-8"],
            index=0 if example["cesd_instrument"] == "CES-D-10" else 1,
            key="cesd_instrument",
        )
        score_values = list(range(0, 10)) if instrument == "CES-D-10" else list(range(0, 3))
        score_default = int(example["cesd_score"]) if instrument == "CES-D-10" else min(1, max(score_values))
        cesd_score = option(
            "Baseline CES-D total score",
            score_values,
            score_default,
            key=f"score_{instrument}",
            help_text="Only baseline screen-negative scores are accepted.",
        )
        mobility = option("Mobility difficulties (0–6)", list(range(0, 7)), int(defaults["Mobility difficulty count"]), "mobility")
        adl = option("ADL difficulties (0–5)", list(range(0, 6)), int(defaults["ADL difficulty count"]), "adl")
        iadl = option("IADL difficulties (0–4)", list(range(0, 5)), int(defaults["IADL difficulty count"]), "iadl")
        pain = option("Troubled with pain", [0, 1], int(defaults["Pain"]), "pain", YES_NO)
        self_health = option("Self-rated health", list(range(1, 5)), int(defaults["Self-rated health"]), "self_health", SELF_RATED_HEALTH)

with column_cognitive:
    with st.container(border=True):
        section_heading("Sensory and cognitive function")
        distance_vision = option("Distance vision", list(range(1, 6)), int(defaults["Self-rated distance vision"]), "distance_vision", VISION)
        near_vision = option("Near vision", list(range(1, 6)), int(defaults["Self-rated near vision"]), "near_vision", VISION)
        memory = option("Self-rated memory", list(range(1, 6)), int(defaults["Self-rated memory"]), "memory", MEMORY)
        immediate = option("Immediate word recall (0–10)", list(range(0, 11)), int(defaults["Immediate word recall"]), "immediate")
        delayed = option("Delayed word recall (0–10)", list(range(0, 11)), int(defaults["Delayed word recall"]), "delayed")
        serial7 = option("Serial 7s score (0–5)", list(range(0, 6)), int(defaults["Serial 7s score"]), "serial7")

with column_social:
    with st.container(border=True):
        section_heading("Sociodemographic and psychosocial factors")
        sex = option("Sex", [0, 1], int(defaults["Sex"]), "sex", SEX)
        education = option("Education level", list(range(0, 3)), int(defaults["Education level"]), "education", EDUCATION)
        satisfaction = option("Life satisfaction", list(range(1, 6)), int(defaults["Life satisfaction"]), "satisfaction", LIFE_SATISFACTION)
        internet = option("Internet use", [0, 1], int(defaults["Internet use"]), "internet", YES_NO)
        children = option("Number of living children", list(range(0, 4)), int(defaults["Number of living children"]), "children", LIVING_CHILDREN)

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
fingerprint = hashlib.sha256(repr((instrument, cesd_score, sorted(other_values.items()))).encode("utf-8")).hexdigest()

with column_result:
    calculate = st.button("Calculate probability", key="calculate", type="primary", use_container_width=True)
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
            st.error(str(error))
    if example_mode:
        probability = float(example["expected_probability"])
    elif st.session_state.get("calculated_fingerprint") == fingerprint:
        probability = float(st.session_state["calculated_probability"])
    else:
        probability = None
    st.markdown(result_html(probability, example_mode), unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note"><b>Research use only.</b> The estimate is derived from a CHARLS development model and externally evaluated in HRS. No entered values are intentionally stored by this application. The result should not replace clinical assessment.</div>',
    unsafe_allow_html=True,
)
