from typing import Dict, Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db, ChatMessage, UserInteraction, UserSession
from deps import get_current_user
from material_cache import get_cache_stats

router = APIRouter()


@router.get("/")
def root():
    return {"message": "Clyvara Backend API", "status": "running"}


@router.get("/health")
def health_check():
    from database import test_connection
    return {
        "status": "healthy",
        "database": "connected" if test_connection() else "disconnected",
    }


@router.get("/api/cache/stats")
def get_cache_stats_endpoint():
    try:
        return {"success": True, "cache_stats": get_cache_stats()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/tables")
def list_tables(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT table_name, table_schema
            FROM information_schema.tables
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
        """))
        tables = [{"schema": row[1], "table": row[0]} for row in result]
        return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


@router.post("/api/ensure-tables")
def ensure_tables():
    try:
        from database import init_db, get_engine
        from sqlalchemy import inspect
        success = init_db()
        if success:
            engine = get_engine()
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            return {
                "success": True,
                "message": "All tables ensured/created successfully",
                "profiles_table_exists": "profiles" in tables,
                "tables": tables,
            }
        return {"success": False, "message": "Failed to create tables"}
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@router.post("/api/test-auth")
def test_authentication_flow(
    test_user_id: str = "550e8400-e29b-41d4-a716-446655440000",
    test_email: str = "test@example.com",
    db: Session = Depends(get_db),
):
    try:
        test_session = UserSession(session_id="test-session-123", user_id=test_user_id, is_active=True)
        db.add(test_session)
        db.commit()

        test_message = ChatMessage(
            session_id="test-session-123",
            message_type="test",
            message_content={"test": "Supabase → AWS connection working!"},
            user_id=test_user_id,
            response_time_ms=100,
            message_length=50,
        )
        db.add(test_message)
        db.commit()
        db.refresh(test_message)

        stored = db.query(ChatMessage).filter(ChatMessage.user_id == test_user_id).first()
        return {
            "status": "success",
            "message": "Supabase → AWS connection working!",
            "supabase_user_id": test_user_id,
            "aws_stored_data": {
                "message_id": str(stored.id),
                "user_id": stored.user_id,
                "content": stored.message_content,
                "timestamp": stored.timestamp.isoformat(),
            },
        }
    except Exception as e:
        return {"error": f"Connection test failed: {str(e)}"}


@router.get("/api/user-data/{user_id}")
def get_user_data(user_id: str, db: Session = Depends(get_db)):
    try:
        messages = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).all()
        interactions = db.query(UserInteraction).filter(UserInteraction.user_id == user_id).all()
        return {
            "supabase_user_id": user_id,
            "chat_messages": [
                {"id": str(m.id), "content": m.message_content, "timestamp": m.timestamp.isoformat()}
                for m in messages
            ],
            "user_interactions": [
                {"id": str(i.id), "type": i.interaction_type, "timestamp": i.timestamp.isoformat()}
                for i in interactions
            ],
            "total_messages": len(messages),
            "total_interactions": len(interactions),
        }
    except Exception as e:
        return {"error": f"Failed to get user data: {str(e)}"}


@router.get("/api/all-users-with-data")
def get_all_users_with_data(db: Session = Depends(get_db)):
    try:
        chat_user_ids = [
            str(u[0])
            for u in db.query(ChatMessage.user_id).filter(ChatMessage.user_id.isnot(None)).distinct().all()
            if u[0] is not None
        ]
        interaction_user_ids = [
            str(u[0])
            for u in db.query(UserInteraction.user_id).filter(UserInteraction.user_id.isnot(None)).distinct().all()
            if u[0] is not None
        ]
        all_user_ids = list(set(chat_user_ids + interaction_user_ids))

        user_data = [
            {
                "supabase_user_id": uid,
                "total_messages": db.query(ChatMessage).filter(ChatMessage.user_id == uid).count(),
                "total_interactions": db.query(UserInteraction).filter(UserInteraction.user_id == uid).count(),
                "has_data": True,
            }
            for uid in all_user_ids
        ]
        return {
            "users_with_data": user_data,
            "total_users": len(user_data),
            "summary": {
                "users_with_chat_messages": len([u for u in user_data if u["total_messages"] > 0]),
                "users_with_interactions": len([u for u in user_data if u["total_interactions"] > 0]),
            },
        }
    except Exception as e:
        return {"error": f"Failed to get user data: {str(e)}"}


@router.get("/api/recent-chat-messages")
def get_recent_chat_messages(db: Session = Depends(get_db)):
    try:
        messages = db.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        return {
            "recent_messages": [
                {
                    "id": str(m.id),
                    "user_id": str(m.user_id),
                    "message_content": m.message_content,
                    "timestamp": m.timestamp.isoformat(),
                    "session_id": m.session_id,
                }
                for m in messages
            ],
            "total_messages": len(messages),
        }
    except Exception as e:
        return {"error": f"Failed to get chat messages: {str(e)}"}


@router.get("/api/debug-user")
def debug_user(current_user: dict = Depends(get_current_user)):
    return {
        "user_info": current_user,
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
    }


@router.post("/items")
async def create_item(item: Dict):
    print("Received from POST:", item)
    return {"json data": item}


# ── Chat-messages & sessions (data access) ───────────────────

@router.get("/api/chat-messages")
def get_chat_messages(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(ChatMessage)
        if session_id:
            query = query.filter(ChatMessage.session_id == session_id)
        if user_id:
            query = query.filter(ChatMessage.user_id == user_id)
        messages = query.order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        return {
            "messages": [
                {
                    "id": str(m.id),
                    "session_id": m.session_id,
                    "message_type": m.message_type,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "user_id": str(m.user_id) if m.user_id else None,
                }
                for m in messages
            ]
        }
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


@router.get("/api/user-sessions")
def get_user_sessions(
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(UserSession)
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        if is_active is not None:
            query = query.filter(UserSession.is_active == is_active)
        sessions = query.order_by(UserSession.created_at.desc()).limit(limit).all()
        return {
            "sessions": [
                {
                    "id": str(s.id),
                    "session_id": s.session_id,
                    "user_id": str(s.user_id) if s.user_id else None,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "is_active": s.is_active,
                }
                for s in sessions
            ]
        }
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


@router.get("/api/user-interactions")
def get_user_interactions(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    interaction_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(UserInteraction)
        if user_id:
            query = query.filter(UserInteraction.user_id == user_id)
        if session_id:
            query = query.filter(UserInteraction.session_id == session_id)
        if interaction_type:
            query = query.filter(UserInteraction.interaction_type == interaction_type)
        interactions = query.order_by(UserInteraction.timestamp.desc()).limit(limit).all()
        return {
            "interactions": [
                {
                    "id": str(i.id),
                    "session_id": i.session_id,
                    "user_id": str(i.user_id) if i.user_id else None,
                    "interaction_type": i.interaction_type,
                    "timestamp": i.timestamp.isoformat() if i.timestamp else None,
                }
                for i in interactions
            ]
        }
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}
