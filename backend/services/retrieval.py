from typing import List, Dict

from ..models import Fact
from .embeddings import embed_text, embed_texts


def ensure_indexed(collection, facts: List[Fact]):
    # Check existing IDs to avoid duplicate upserts
    existing_count = 0
    try:
        existing_count = collection.count()
    except Exception:
        existing_count = 0
    if existing_count and existing_count >= len(facts):
        return

    ids = [f.id for f in facts]
    metadatas = [
        {
            "symptom": f.symptom,
            "cause": f.cause,
            "treatment": f.treatment,
            "precaution": f.precaution,
        }
        for f in facts
    ]
    documents = [
        f"Symptom: {f.symptom}\nCause: {f.cause}\nTreatment: {f.treatment}\nPrecaution: {f.precaution}"
        for f in facts
    ]
    embeddings = embed_texts(documents)
    collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)


def semantic_search(collection, query: str, top_k: int = 4) -> List[Fact]:
    q_emb = embed_text(query)
    results = collection.query(query_embeddings=[q_emb], n_results=top_k)
    out: List[Fact] = []
    for i, _id in enumerate(results.get("ids", [[]])[0]):
        md = results["metadatas"][0][i]
        out.append(
            Fact(
                id=_id,
                symptom=md.get("symptom", ""),
                cause=md.get("cause", ""),
                treatment=md.get("treatment", ""),
                precaution=md.get("precaution", ""),
            )
        )
    return out