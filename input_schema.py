from __future__ import annotations


YES_NO = {0: "No", 1: "Yes"}
SEX = {0: "Male", 1: "Female"}
EDUCATION = {
    0: "Below high school",
    1: "High school, vocational education, or some college",
    2: "College or above",
}
SELF_RATED_HEALTH = {
    1: "Very good or excellent",
    2: "Good",
    3: "Fair",
    4: "Poor or very poor",
}
VISION = {
    1: "Excellent",
    2: "Very good",
    3: "Good",
    4: "Fair",
    5: "Poor or blind",
}
MEMORY = {
    1: "Excellent",
    2: "Very good",
    3: "Good",
    4: "Fair",
    5: "Poor",
}
LIFE_SATISFACTION = {
    1: "Not at all satisfied",
    2: "Not very satisfied",
    3: "Somewhat satisfied",
    4: "Very satisfied",
    5: "Completely satisfied",
}
LIVING_CHILDREN = {0: "0", 1: "1", 2: "2", 3: "3 or more"}


GROUPS = {
    "Depressive burden and physical health": [
        "Baseline subthreshold CES-D burden",
        "Mobility difficulty count",
        "ADL difficulty count",
        "IADL difficulty count",
        "Pain",
        "Self-rated health",
    ],
    "Sensory and cognitive function": [
        "Self-rated distance vision",
        "Self-rated near vision",
        "Self-rated memory",
        "Immediate word recall",
        "Delayed word recall",
        "Serial 7s score",
    ],
    "Sociodemographic and psychosocial factors": [
        "Sex",
        "Education level",
        "Life satisfaction",
        "Internet use",
        "Number of living children",
    ],
}
