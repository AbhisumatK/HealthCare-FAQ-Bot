import os
import json
from typing import List, Dict, Any
import numpy as np

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings as ChromaSettings  # type: ignore
    _CHROMA_AVAILABLE = True
except Exception:
    chromadb = None
    ChromaSettings = None
    _CHROMA_AVAILABLE = False

from ..models import Fact
from ..settings import settings


_client = None
_collection = None


class SimpleCollection:
    """Pure-Python fallback collection using cosine similarity on embeddings.
    Persisted to data/simple_index.json for portability.
    """

    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                    self.data = raw if isinstance(raw, dict) else {}
            except Exception:
                self.data = {}

    def _persist(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh)

    def upsert(self, ids, embeddings, metadatas, documents):
        for i, _id in enumerate(ids):
            self.data[_id] = {
                "embedding": embeddings[i],
                "metadata": metadatas[i],
                "document": documents[i],
            }
        self._persist()

    def delete(self, where=None):
        self.data = {}
        self._persist()

    def count(self):
        return len(self.data)

    def query(self, query_embeddings, n_results=4):
        q = np.array(query_embeddings[0], dtype=float)
        if not self.data:
            return {"ids": [[]], "metadatas": [[]]}
        ids = list(self.data.keys())
        embs = np.array([self.data[i]["embedding"] for i in ids], dtype=float)
        # cosine similarity
        embs_norm = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9)
        q_norm = q / (np.linalg.norm(q) + 1e-9)
        sims = embs_norm @ q_norm
        top_idx = sims.argsort()[::-1][:n_results]
        top_ids = [ids[i] for i in top_idx]
        top_mds = [self.data[i]["metadata"] for i in top_idx]
        return {"ids": [top_ids], "metadatas": [top_mds]}


def _get_client():
    global _client
    if not _CHROMA_AVAILABLE:
        return None
    if _client is None:
        os.makedirs(settings.persist_dir, exist_ok=True)
        _client = chromadb.Client(ChromaSettings(persist_directory=settings.persist_dir))
    return _client


def get_or_create_collection():
    global _collection
    if _collection is not None:
        return _collection
    if _CHROMA_AVAILABLE:
        client = _get_client()
        try:
            _collection = client.get_collection("medical_facts")
        except Exception:
            _collection = client.create_collection(name="medical_facts")
    else:
        # Fallback to simple index file
        _collection = SimpleCollection(path=os.path.join("data", "simple_index.json"))
    return _collection


def load_facts_from_json() -> List[Fact]:
    if not os.path.exists(settings.facts_path):
        return []
    with open(settings.facts_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Fact(**item) for item in data]