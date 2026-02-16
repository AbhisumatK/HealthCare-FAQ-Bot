import os
import json
from typing import List

from backend.models import Fact
from backend.services.store import get_or_create_collection
from backend.services.embeddings import embed_texts
from backend.settings import settings


def normalize_fact(f: Fact) -> Fact:
    # Basic normalization: strip whitespace and lower-case common fields
    return Fact(
        id=f.id.strip(),
        symptom=f.symptom.strip(),
        cause=f.cause.strip(),
        treatment=f.treatment.strip(),
        precaution=f.precaution.strip(),
    )


def load_facts(path: str) -> List[Fact]:
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    facts = [normalize_fact(Fact(**item)) for item in raw]
    # Remove obvious duplicates by (symptom, cause, treatment, precaution)
    seen = set()
    uniq = []
    for f in facts:
        key = (f.symptom.lower(), f.cause.lower(), f.treatment.lower(), f.precaution.lower())
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


def build_index(facts: List[Fact]):
    collection = get_or_create_collection()
    ids = [f.id for f in facts]
    docs = [
        f"Symptom: {f.symptom}\nCause: {f.cause}\nTreatment: {f.treatment}\nPrecaution: {f.precaution}"
        for f in facts
    ]
    metas = [
        {
            "symptom": f.symptom,
            "cause": f.cause,
            "treatment": f.treatment,
            "precaution": f.precaution,
        }
        for f in facts
    ]
    embs = embed_texts(docs)
    # Upsert will overwrite existing IDs; skip unconditional delete for compatibility
    collection.upsert(ids=ids, embeddings=embs, metadatas=metas, documents=docs)


def main():
    os.makedirs(os.path.dirname(settings.facts_path), exist_ok=True)
    if not os.path.exists(settings.facts_path):
        raise SystemExit(f"Missing facts file at {settings.facts_path}")
    facts = load_facts(settings.facts_path)
    build_index(facts)
    print(f"Indexed {len(facts)} facts into Chroma at {settings.persist_dir}")


if __name__ == "__main__":
    main()