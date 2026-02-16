from typing import List, Tuple
import re

from ..models import Fact


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def verify_answer(answer: str, fact_ids: List[str], facts_subset: List[Fact]) -> Tuple[bool, str]:
    # Simple rule-based verifier: ensure only content in provided facts is referenced
    # Collect allowed tokens from facts
    allowed_chunks = []
    for f in facts_subset:
        for field in (f.symptom, f.cause, f.treatment, f.precaution):
            allowed_chunks.extend([c.strip() for c in field.split(",")])
            allowed_chunks.append(field)

    normalized_answer = _normalize(answer)
    # If the answer contains any word sequences not in allowed facts, flag it
    # Simple heuristic: check mentions of key medical nouns by presence in allowed chunks
    suspicious = []
    key_terms = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", normalized_answer)
    for t in set(key_terms):
        if len(t) < 4:
            continue
        present = any(t in _normalize(chunk) for chunk in allowed_chunks)
        if not present and t not in {"the", "and", "with", "from", "that", "only", "this", "informational", "medical", "advice"}:
            suspicious.append(t)

    if suspicious:
        # Rewrite to only list facts exactly
        causes = ", ".join(sorted(set([f.cause for f in facts_subset if f.cause])))
        treatments = ", ".join(sorted(set([f.treatment for f in facts_subset if f.treatment])))
        precautions = ", ".join(sorted(set([f.precaution for f in facts_subset if f.precaution])))
        rewritten_parts = []
        if causes:
            rewritten_parts.append(f"Possible general causes: {causes}.")
        if treatments:
            rewritten_parts.append(f"General self-care measures: {treatments}.")
        if precautions:
            rewritten_parts.append(f"Precautions: {precautions}.")
        rewritten = " ".join(rewritten_parts) or "Information is insufficient based on provided facts."
        rewritten += " This is informational only and not medical advice."
        return False, rewritten

    return True, answer