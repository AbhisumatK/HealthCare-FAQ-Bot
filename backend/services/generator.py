from typing import Dict, List
import os
import requests
import json

from ..settings import settings
from ..models import Fact


def _compose_prompt(user_query: str, context: Dict[str, List[str]]) -> str:
    return (
        "You are a medical information assistant. Answer the user's question using ONLY the provided facts. "
        "Do not diagnose or prescribe. Keep a calm, informational tone. "
        "If facts are insufficient, say so briefly.\n\n"
        f"User question: {user_query}\n\n"
        "Structured facts (minimal):\n"
        f"Symptoms: {', '.join(context.get('symptoms', []))}\n"
        f"Possible causes: {', '.join(context.get('possible_causes', []))}\n"
        f"General treatments: {', '.join(context.get('general_treatments', []))}\n"
        f"Precautions: {', '.join(context.get('precautions', []))}\n\n"
        "Constraints:\n- Use only the facts above.\n- Avoid personalization.\n- Avoid diagnosis.\n- Keep it concise.\n"
        "Respond in JSON with keys 'answer' and 'facts_used' (list of Fact IDs if available)."
    )


def _compress_prompt_scaledown(context_text: str, prompt_text: str):
    url = settings.scaledown_compress_url.strip()
    key = settings.scaledown_api_key.strip()
    if not url or not key:
        return None
    headers = {
        "x-api-key": key,
        "Content-Type": "application/json",
    }
    payload = {
        "context": context_text,
        "prompt": prompt_text,
        "scaledown": {"rate": "auto"},
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    r.raise_for_status()
    return r.json()


def _deterministic_answer(context: Dict[str, List[str]], facts: List[Fact], token_hint: Dict[str, int] | None = None) -> Dict:
    # Compose a conservative, purely fact-based answer without LLM
    parts = []
    if context.get("possible_causes"):
        parts.append(
            "Based on the provided information, possible general causes include: "
            + ", ".join(context["possible_causes"]) + "."
        )
    if context.get("general_treatments"):
        parts.append(
            "General self-care measures often include: "
            + ", ".join(context["general_treatments"]) + "."
        )
    if context.get("precautions"):
        parts.append(
            "Consider these precautions: " + ", ".join(context["precautions"]) + "."
        )
    if not parts:
        parts.append("I do not have sufficient information from the facts to answer specifically.")
    answer = " ".join(parts) + " This is informational only and not medical advice."
    tokens_used = token_hint or {"prompt": 0, "completion": len(answer)}
    return {"answer": answer, "facts_used": [f.id for f in facts], "tokens_used": tokens_used}


def generate_answer(user_query: str, context: Dict[str, List[str]], facts: List[Fact]) -> Dict:
    prompt = _compose_prompt(user_query, context)
    # Compress prompt via ScaleDown (token-efficient) if configured
    tokens_hint = None
    try:
        context_text = (
            f"Symptoms: {', '.join(context.get('symptoms', []))}. "
            f"Causes: {', '.join(context.get('possible_causes', []))}. "
            f"Treatments: {', '.join(context.get('general_treatments', []))}. "
            f"Precautions: {', '.join(context.get('precautions', []))}."
        )
        comp = _compress_prompt_scaledown(context_text, user_query)
        if comp and isinstance(comp, dict) and comp.get("successful"):
            tokens_hint = {
                "prompt": int(comp.get("compressed_prompt_tokens", 0)),
                "completion": 0,
            }
    except Exception:
        pass

    # Generation: keep deterministic (fact-grounded) to avoid diagnosing without a model
    return _deterministic_answer(context, facts, token_hint=tokens_hint)