from typing import List, Dict
from ..models import Fact


def build_minimal_context(facts: List[Fact]) -> Dict[str, List[str]]:
    # Deduplicate and limit lengths for token efficiency
    symptoms = []
    causes = []
    treatments = []
    precautions = []
    for f in facts:
        if f.symptom and f.symptom not in symptoms:
            symptoms.append(f.symptom)
        if f.cause and f.cause not in causes:
            causes.append(f.cause)
        if f.treatment and f.treatment not in treatments:
            treatments.append(f.treatment)
        if f.precaution and f.precaution not in precautions:
            precautions.append(f.precaution)
    # Keep minimal necessary elements
    return {
        "symptoms": symptoms[:5],
        "possible_causes": causes[:5],
        "general_treatments": treatments[:5],
        "precautions": precautions[:5],
    }