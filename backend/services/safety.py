from typing import Tuple, Dict
import re


EMERGENCY_PATTERNS = [
    r"chest pain",
    r"shortness of breath",
    r"severe bleeding",
    r"stroke",
    r"numbness on one side",
    r"fainting",
    r"unresponsive",
    r"suicidal|self-harm",
]


DISCLAIMER = (
    "This information is educational and not a diagnosis, prescription, or a substitute for professional care."
)


def detect_emergency(text: str) -> bool:
    t = text.lower()
    return any(re.search(pat, t) for pat in EMERGENCY_PATTERNS)


def apply_safety(query: str, answer: str) -> Tuple[str, Dict[str, bool]]:
    flags = {"emergency": False, "override": False}
    if detect_emergency(query):
        flags["emergency"] = True
        urgent = (
            "If you or someone is experiencing potential emergency symptoms (e.g., chest pain, severe difficulty breathing, signs of stroke), "
            "seek immediate medical care or call local emergency services. "
        )
        answer = urgent + " " + answer
    # Always append disclaimer
    if not answer.strip().endswith(DISCLAIMER):
        answer = answer.strip() + " " + DISCLAIMER
    return answer, flags