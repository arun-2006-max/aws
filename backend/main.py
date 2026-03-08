"""
AI Builder Copilot – FastAPI Backend
Powered by OpenRouter AI, SQLite, and ChromaDB
Serves the React frontend as static files = single URL deployment
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
import pathlib

from models import (
    ChatRequest, ChatResponse,
    DebugRequest, DebugResponse,
    LearningAnalysisResponse,
    ProgressResponse,
    FeedbackRequest,
    LoginRequest, LoginResponse,
)
from services.openrouter_service import OpenRouterService
from services.db_service import DBService
from services.chroma_service import ChromaService

app = FastAPI(
    title="AI Builder Copilot API",
    description="Personalized learning & development AI assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons initialised once on startup
_ai: OpenRouterService = None
_db: DBService = None
_chroma: ChromaService = None

@app.on_event("startup")
async def startup():
    global _ai, _db, _chroma
    _ai = OpenRouterService()
    _db = DBService()
    _chroma = ChromaService()

def get_ai() -> OpenRouterService:
    return _ai

def get_db() -> DBService:
    return _db

def get_chroma() -> ChromaService:
    return _chroma

# ── Auth helpers ─────────────────────────────────────────────────────
def get_user_id(authorization: str = Header(default="")) -> str:
    """Extract user_id from Bearer token (simple JWT-less token for demo)."""
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        # Token format: user_id:email (base64 encoded in production)
        # For simplicity: token IS the user_id
        return token or "anonymous"
    return "anonymous"

# ── Auth ──────────────────────────────────────────────────────────────
@app.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: DBService = Depends(get_db)):
    """Simple login — creates user if not exists, returns a token."""
    user = db.get_or_create_user(req.email)
    # Token is just user_id for this demo (use JWT in production)
    return LoginResponse(
        token=user["user_id"],
        user_id=user["user_id"],
        email=user["email"],
    )

# ── Chat ──────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user_id: str = Depends(get_user_id),
    ai: OpenRouterService = Depends(get_ai),
    db: DBService = Depends(get_db),
    chroma: ChromaService = Depends(get_chroma),
):
    import time
    start = time.time()

    # RAG: find relevant docs
    sources = chroma.search(req.query, n_results=3)
    context = "\n\n".join([s["content"] for s in sources]) if sources else ""

    # Build prompt
    system = (
        "You are AI Builder Copilot, a personalized learning and development assistant. "
        "You help students and developers learn faster and build smarter. "
        "Be concise, use code examples where helpful, and use markdown formatting."
    )
    if context:
        system += f"\n\nRelevant context from knowledge base:\n{context}"

    # Choose model based on query complexity
    model = "openai/gpt-4o" if len(req.query) > 150 or any(
        w in req.query.lower() for w in ["debug", "architecture", "design", "explain", "compare"]
    ) else "openai/gpt-4o-mini"

    result = await ai.chat(
        prompt=req.query,
        system_prompt=system,
        model=model,
    )

    latency_ms = int((time.time() - start) * 1000)

    # Log interaction
    db.log_interaction(user_id, req.query, result["response"], model, latency_ms)

    return ChatResponse(
        response=result["response"],
        model=model,
        sources=[{"source_key": s.get("source", ""), "score": s.get("score", 0)} for s in sources],
        latency_ms=latency_ms,
        cached=False,
    )

# ── Debug Assistant ───────────────────────────────────────────────────
@app.post("/debug-assistant", response_model=DebugResponse)
async def debug_assistant(
    req: DebugRequest,
    user_id: str = Depends(get_user_id),
    ai: OpenRouterService = Depends(get_ai),
    chroma: ChromaService = Depends(get_chroma),
):
    import time
    start = time.time()

    sources = chroma.search(f"{req.code}\n{req.error}", n_results=2)
    context = "\n".join([s["content"] for s in sources])

    system = (
        "You are an expert software debugger. Analyse the code and error provided. "
        "Return a structured markdown response with these sections:\n"
        "**Root Cause**: What caused the error\n"
        "**Fix**: The corrected code\n"
        "**Explanation**: Why this fixes it\n"
        "**Prevention**: How to avoid this in future"
    )
    if context:
        system += f"\n\nRelevant docs:\n{context}"

    prompt = f"Language: {req.language or 'unknown'}\n\nCode:\n```\n{req.code}\n```\n\nError:\n```\n{req.error}\n```"

    result = await ai.chat(prompt=prompt, system_prompt=system, model="openai/gpt-4o")
    latency_ms = int((time.time() - start) * 1000)

    return DebugResponse(
        debug_analysis=result["response"],
        model="openai/gpt-4o",
        latency_ms=latency_ms,
        sources=[{"source_key": s.get("source", ""), "score": s.get("score", 0)} for s in sources],
    )

# ── Learning Analysis ─────────────────────────────────────────────────
@app.post("/learning-analysis", response_model=LearningAnalysisResponse)
async def learning_analysis(
    user_id: str = Depends(get_user_id),
    ai: OpenRouterService = Depends(get_ai),
    db: DBService = Depends(get_db),
):
    import json, time
    interactions = db.get_recent_interactions(user_id, limit=20)
    if not interactions:
        return LearningAnalysisResponse(
            analysis={"gaps": [], "summary": "Not enough data yet. Ask more questions!"},
            model="openai/gpt-4o-mini",
            interactions_analysed=0,
        )

    history = "\n".join([f"Q: {i['query']}" for i in interactions])
    system = (
        "You are a learning analyst. Identify knowledge gaps from these questions.\n"
        "Return ONLY valid JSON with this schema:\n"
        '{"gaps": [{"topic": "string", "confidence": 0.0-1.0, "suggestions": ["string"]}], "summary": "string"}'
    )
    result = await ai.chat(
        prompt=f"Recent questions:\n{history}\n\nAnalyse gaps:",
        system_prompt=system,
        model="openai/gpt-4o-mini",
    )
    try:
        # Strip markdown code fences if present
        raw = result["response"].strip().strip("```json").strip("```").strip()
        analysis = json.loads(raw)
    except Exception:
        analysis = {"raw_response": result["response"]}

    # Save gaps
    for gap in analysis.get("gaps", []):
        db.save_knowledge_gap(user_id, gap.get("topic", ""), gap.get("confidence", 0.5), gap.get("suggestions", []))

    return LearningAnalysisResponse(
        analysis=analysis,
        model="openai/gpt-4o-mini",
        interactions_analysed=len(interactions),
    )

# ── User Progress ─────────────────────────────────────────────────────
@app.get("/user-progress", response_model=ProgressResponse)
async def user_progress(
    user_id: str = Depends(get_user_id),
    db: DBService = Depends(get_db),
):
    return db.get_user_progress(user_id)

# ── Feedback ──────────────────────────────────────────────────────────
@app.post("/store-feedback")
async def store_feedback(
    req: FeedbackRequest,
    user_id: str = Depends(get_user_id),
    db: DBService = Depends(get_db),
):
    db.store_feedback(user_id, req.interaction_timestamp, req.rating)
    return {"message": "Feedback stored", "rating": req.rating}

# ── Health ────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "AI Builder Copilot API"}

# ── SPA Static Files (must come LAST — after all API routes) ─────────
STATIC_DIR = pathlib.Path(__file__).parent / "build"

if STATIC_DIR.exists():
    # Serve React build assets (JS, CSS, images)
    app.mount("/static", StaticFiles(directory=STATIC_DIR / "static"), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Return index.html for all non-API routes so React Router works."""
        index = STATIC_DIR / "index.html"
        return FileResponse(str(index))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)
