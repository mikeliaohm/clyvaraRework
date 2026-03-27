import json
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import openai_client, SYSTEM_USER_ID
from database import get_db, ChatMessage, UserSession
from deps import get_current_user

router = APIRouter()

# ── System prompt ─────────────────────────────────────────────
with open("systemprompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

SESSIONS: Dict[str, Optional[str]] = {}

PRIORITY_WORDS = {
    "login", "log in", "signin", "sign in", "sign-in",
    "logout", "sign out", "register", "sign up",
    "profile", "account", "menu", "pricing", "help", "docs", "dashboard",
}


# ── Schemas ───────────────────────────────────────────────────

class ChatIn(BaseModel):
    message: str
    thread_id: Optional[str] = None
    page_context: Optional[Dict[str, Any]] = None


class ChatOut(BaseModel):
    reply: str
    thread_id: str


# ── Page-context helpers ──────────────────────────────────────

def _safe_text(x: Optional[str]) -> str:
    return x.strip() if isinstance(x, str) else ""


def summarize_context_on_server(ctx: dict, limit: int = 24) -> dict:
    if not isinstance(ctx, dict):
        return {}

    url = _safe_text(ctx.get("url"))
    title = _safe_text(ctx.get("title"))
    headings = ctx.get("headings") or []
    elements = ctx.get("elements") or []

    clean_headings = []
    for h in headings[:8]:
        if isinstance(h, dict):
            clean_headings.append({"tag": _safe_text(h.get("tag")), "text": _safe_text(h.get("text"))[:120]})

    prioritized: list = []
    for el in elements:
        if not isinstance(el, dict):
            continue
        text = _safe_text(el.get("text") or el.get("ariaLabel"))
        if any(w in text.lower() for w in PRIORITY_WORDS) or _safe_text(el.get("dataQa")):
            prioritized.append({
                "tag": _safe_text(el.get("tag")),
                "text": text[:80],
                "ariaLabel": _safe_text(el.get("ariaLabel"))[:80],
                "href": _safe_text(el.get("href"))[:200],
                "id": _safe_text(el.get("id"))[:80],
                "dataQa": _safe_text(el.get("dataQa"))[:80],
                "region": _safe_text(el.get("region"))[:20],
            })
            if len(prioritized) >= limit:
                break

    if not prioritized:
        for el in elements[:limit]:
            if not isinstance(el, dict):
                continue
            prioritized.append({
                "tag": _safe_text(el.get("tag")),
                "text": _safe_text(el.get("text"))[:80],
                "ariaLabel": _safe_text(el.get("ariaLabel"))[:80],
                "href": _safe_text(el.get("href"))[:200],
                "id": _safe_text(el.get("id"))[:80],
                "dataQa": _safe_text(el.get("dataQa"))[:80],
                "region": _safe_text(el.get("region"))[:20],
            })

    return {"url": url, "title": title, "headings": clean_headings, "elements": prioritized}


def build_page_context_message(ctx: Optional[dict]) -> Optional[dict]:
    if not ctx:
        return None
    summary = summarize_context_on_server(ctx)
    if not summary:
        return None
    return {"role": "system", "content": "PAGE_CONTEXT:\n" + json.dumps(summary, ensure_ascii=False)}


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/api/chat-messages")
def create_chat_message(
    session_id: str,
    message_type: str,
    message_content: Dict,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
    response_time_ms: Optional[int] = None,
    message_length: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    message = ChatMessage(
        session_id=session_id,
        message_type=message_type,
        message_content=message_content,
        thread_id=thread_id,
        user_id=current_user["user_id"],
        response_time_ms=response_time_ms,
        message_length=message_length,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"message": "Chat message created", "id": message.id}


@router.post("/chat", response_model=ChatOut)
def chat(
    payload: ChatIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not configured")

    thread_id = payload.thread_id or str(uuid4())
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. You can answer questions about medical topics, general knowledge, current events, and provide practical information. Be helpful and informative in your responses."}
    ]
    messages.append({"role": "user", "content": payload.message})

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=500
        )
        reply = response.choices[0].message.content

        try:
            existing_session = db.query(UserSession).filter(UserSession.session_id == thread_id).first()
            if not existing_session:
                db.add(UserSession(session_id=thread_id, user_id=current_user["user_id"], is_active=True))
                db.commit()

            db.add(ChatMessage(
                session_id=thread_id,
                message_type="user",
                message_content={"message": payload.message},
                user_id=current_user["user_id"],
                response_time_ms=100,
                message_length=len(payload.message),
            ))
            db.commit()
        except Exception as db_error:
            print(f"Database storage error: {db_error}")

        return ChatOut(reply=reply, thread_id=thread_id)

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "invalid_api_key" in error_msg.lower():
            raise HTTPException(status_code=500, detail="Chat error: Invalid OpenAI API key.")
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            raise HTTPException(status_code=500, detail="Chat error: API key access denied (403).")
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            raise HTTPException(status_code=500, detail="Chat error: Rate limit exceeded.")
        else:
            raise HTTPException(status_code=500, detail=f"Chat error: {error_msg}")


@router.post("/chat-test", response_model=ChatOut)
def chat_test(payload: ChatIn, db: Session = Depends(get_db)):
    """Test chat endpoint without authentication"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not configured")

    thread_id = payload.thread_id or str(uuid4())
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": payload.message},
    ]

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=500
        )
        return ChatOut(reply=response.choices[0].message.content, thread_id=thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/chat-rag", response_model=ChatOut)
def chat_with_rag(
    payload: ChatIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chat with RAG: searches user's materials and system materials for context."""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not configured")

    thread_id = payload.thread_id or str(uuid4())
    relevant_context = ""

    try:
        from rag.embedder import get_embedder
        from rag.pipeline import search_chunks

        embedder = get_embedder()
        results = search_chunks(
            query=payload.message,
            user_id=current_user["user_id"],
            db=db,
            embedder=embedder,
            top_k=5,
        )

        if results:
            relevant_context = "\n\nRelevant information from available materials:\n"
            for i, r in enumerate(results, 1):
                title = r.get("document_title", "Unknown")
                content = r.get("content", "")[:500]
                relevant_context += f"\n{i}. From {title}:\n{content}...\n"

    except Exception as e:
        print(f"RAG search error: {e}")

    system_prompt = f"""You are a helpful AI assistant for Clyvara, a medical education platform.

{relevant_context}

When referencing information from uploaded materials, mention the source file name."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload.message},
    ]

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=500
        )
        reply = response.choices[0].message.content

        try:
            existing_session = db.query(UserSession).filter(UserSession.session_id == thread_id).first()
            if not existing_session:
                db.add(UserSession(session_id=thread_id, user_id=current_user["user_id"], is_active=True))
                db.commit()

            db.add(ChatMessage(
                session_id=thread_id,
                message_type="user",
                message_content={"message": payload.message},
                user_id=current_user["user_id"],
                response_time_ms=100,
                message_length=len(payload.message),
            ))
            db.commit()
        except Exception as db_error:
            print(f"Database storage error: {db_error}")

        return ChatOut(reply=reply, thread_id=thread_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
