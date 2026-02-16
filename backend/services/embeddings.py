from functools import lru_cache
from typing import List

import numpy as np

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _ST_AVAILABLE = True
except Exception:
    SentenceTransformer = None
    _ST_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import HashingVectorizer
    _SKLEARN_AVAILABLE = True
except Exception:
    HashingVectorizer = None
    _SKLEARN_AVAILABLE = False

from ..settings import settings


@lru_cache(maxsize=1)
def _load_model():
    if _ST_AVAILABLE:
        model_name = settings.embedding_model
        return SentenceTransformer(model_name)
    if _SKLEARN_AVAILABLE:
        return HashingVectorizer(n_features=512, alternate_sign=False, norm='l2')
    raise RuntimeError("No embedding backend available. Install sentence-transformers or scikit-learn.")


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = _load_model()
    if _ST_AVAILABLE and isinstance(model, SentenceTransformer):
        embs = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embs.tolist() if isinstance(embs, np.ndarray) else [e.tolist() for e in embs]
    # Fallback: HashingVectorizer
    mat = model.transform(texts)
    # Convert sparse to dense and l2 normalize
    if hasattr(mat, 'toarray'):
        arr = mat.toarray()
    else:
        arr = np.asarray(mat)
    norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9
    arr = arr / norms
    return arr.tolist()


def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]