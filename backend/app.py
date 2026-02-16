from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

from .models import AskRequest, AskResponse, VerifyRequest, VerifyResponse, Fact
from .settings import settings
from .services.store import get_or_create_collection, load_facts_from_json
from .services.retrieval import semantic_search, ensure_indexed
from .services.context_builder import build_minimal_context
from .services.generator import generate_answer
from .services.verifier import verify_answer
from .services.safety import apply_safety

app = FastAPI(title="Token-Efficient Medical FAQ System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def on_startup():
    collection = get_or_create_collection()
    facts = load_facts_from_json()
    ensure_indexed(collection, facts)


@app.get("/facts", response_model=List[Fact])
def get_facts():
    return load_facts_from_json()


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    collection = get_or_create_collection()
    # retrieve minimal set of facts
    top_k = req.top_k if req.top_k and 1 <= req.top_k <= 8 else 4
    retrieved = semantic_search(collection, req.query, top_k=top_k)
    if not retrieved:
        # No facts found – return safe generic guidance
        safe_ans = "I couldn’t find specific information. For general concerns, consider rest, hydration, and consult a medical professional if symptoms persist or worsen. This is informational, not medical advice."
        return AskResponse(answer=safe_ans, facts_used=[], retrieved_facts=[], verified=False, tokens_used={"prompt": 0, "completion": 0})

    context = build_minimal_context(retrieved)
    # Generate answer using provided facts only
    gen = generate_answer(req.query, context, retrieved)

    # Self-verification and automatic rewrite if needed
    verified, final_answer = verify_answer(gen["answer"], gen["facts_used"], retrieved)

    # Safety layer: emergency detection + disclaimer
    final_answer, flags = apply_safety(req.query, final_answer)

    return AskResponse(
        answer=final_answer,
        facts_used=gen["facts_used"],
        retrieved_facts=retrieved,
        verified=verified and not flags.get("override", False),
        tokens_used=gen.get("tokens_used", {"prompt": 0, "completion": 0})
    )


@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    if not req.answer:
        raise HTTPException(status_code=400, detail="Answer is required")
    collection = get_or_create_collection()
    # Load facts map from JSON for deterministic content
    facts = load_facts_from_json()
    id_to_fact: Dict[str, Fact] = {f.id: f for f in facts}
    subset = [id_to_fact[i] for i in req.facts_used if i in id_to_fact]
    verified, rewritten = verify_answer(req.answer, req.facts_used, subset)
    return VerifyResponse(verified=verified, answer=rewritten)