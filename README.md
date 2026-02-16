Token-Efficient Medical FAQ System (Prototype)

Overview
- Answers general medical questions (non-diagnostic) using compressed atomic facts.
- Retrieval → Minimal Context → Answer Generation → Self-Verification → Safe Response.
- Token-efficient prompts leveraging short, structured facts instead of full documents.

Tech Stack
- Backend: FastAPI
- Frontend: Streamlit
- Vector DB: ChromaDB (local persistence in `data/chroma`)
- Embeddings: Sentence Transformers by default (`all-MiniLM-L6-v2`).
- LLM: Pluggable HTTP client. Defaults to local deterministic generator if no API key. Supports ScaleDown API via environment.

Project Structure
- backend/
- compression/
- data/
- frontend/

Quick Start
1) Python 3.10+ recommended.
2) Install dependencies:
   pip install -r requirements.txt
3) Initialize the compressed knowledge base and Chroma index:
   python compression/preprocess.py
4) Start backend:
   uvicorn backend.app:app --reload --port 8000
5) Start frontend:
   streamlit run frontend/app.py

Environment
- Create folder `.env/` and put a file named `.env` inside with the following keys left empty for now:

  SCALEDOWN_API_URL=
  SCALEDOWN_API_KEY=
  EMBEDDING_MODEL=all-MiniLM-L6-v2
  BACKEND_URL=http://localhost:8000

Endpoints
- POST /ask: {"query": "<question>"}
- POST /verify: {"answer": "...", "facts_used": ["FACT_001", ...]}
- GET /facts: Returns compressed facts.

Notes
- This system provides informational guidance only. It never diagnoses or prescribes.
- For red-flag symptoms, it prompts users to seek professional help immediately.