import orjson
from fastapi import FastAPI
from pydantic import BaseModel
from agents.sql_agent import run_agent
from helpers.logging import setup_logging
from helpers.config import load_config
from db.session import SessionLocal
from db.models import ChatMessage
from typing import List

logger = setup_logging()
cfg = load_config()

class ChatIn(BaseModel):
    session_id: str
    message: str

class ChatOut(BaseModel):
    ok: bool
    sql: str | None = None
    markdown: str | None = None
    needs_clarification: bool | None = None
    message: str | None = None
    error: str | None = None

app = FastAPI(title="AI SQL Agent", version="1.0.0")

@app.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn):
    return run_agent(body.session_id, body.message)

class Msg(BaseModel):
    role: str
    content: str

@app.get("/api/history/{session_id}", response_model=List[Msg])
def history(session_id: str):
    if not cfg.chat_history["enabled"]:
        return []
    with SessionLocal() as s:
        rows = (
            s.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
            .all()
        )
    return [Msg(role=r.role, content=r.content) for r in rows]

@app.get("/")
def root():
    return {"name": "AI SQL Agent", "status": "ok"}
