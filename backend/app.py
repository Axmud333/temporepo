# app.py - Enhanced with conversation memory
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
from datetime import datetime, timedelta
from typing import Literal, Dict, List, Optional
import logging
import os
import hashlib
import re
import uuid
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.database import SessionLocal, Info, init_db
from backend.claude_api import ask_claude_with_context, clear_cache, cleanup_cache
from chatgpt_api import ask_openai
from email_service import send_feedback_email

load_dotenv()

logging.basicConfig(filename='logs/chat_logs.txt', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(docs_url=None, redoc_url=None)

templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="/app/frontend/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

rate_limit_storage: Dict[str, Dict] = {}

# NEW: Conversation memory storage
# Format: {session_id: {"messages": [{"role": "user/assistant", "content": "...", "timestamp": datetime}], "last_active": datetime}}
conversation_memory: Dict[str, Dict] = {}
MAX_CONVERSATION_HISTORY = 10  # Keep last 10 messages per session
CONVERSATION_TIMEOUT = 3600  # 1 hour timeout

def cleanup_old_conversations():
    """Remove expired conversations to prevent memory bloat"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in conversation_memory.items():
        if current_time - session_data["last_active"] > timedelta(seconds=CONVERSATION_TIMEOUT):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del conversation_memory[session_id]
    
    if expired_sessions:
        logging.info(f"Cleaned up {len(expired_sessions)} expired conversations")

def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create new one"""
    if session_id and session_id in conversation_memory:
        conversation_memory[session_id]["last_active"] = datetime.now()
        return session_id
    
    new_session_id = str(uuid.uuid4())
    conversation_memory[new_session_id] = {
        "messages": [],
        "last_active": datetime.now()
    }
    return new_session_id

def add_message_to_session(session_id: str, role: str, content: str):
    """Add message to conversation history"""
    if session_id not in conversation_memory:
        conversation_memory[session_id] = {"messages": [], "last_active": datetime.now()}
    
    conversation_memory[session_id]["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })
    
    # Keep only the last N messages to prevent memory bloat
    if len(conversation_memory[session_id]["messages"]) > MAX_CONVERSATION_HISTORY:
        conversation_memory[session_id]["messages"] = conversation_memory[session_id]["messages"][-MAX_CONVERSATION_HISTORY:]
    
    conversation_memory[session_id]["last_active"] = datetime.now()

def get_conversation_context(session_id: str) -> List[Dict]:
    """Get conversation context for Claude API"""
    if session_id not in conversation_memory:
        return []
    
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in conversation_memory[session_id]["messages"]
    ]

def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host

def check_rate_limit(client_ip: str, limit: int = 50, window: int = 3600) -> bool:
    now = datetime.now()
    
    if client_ip not in rate_limit_storage:
        rate_limit_storage[client_ip] = {"count": 1, "window_start": now}
        return True
    
    client_data = rate_limit_storage[client_ip]
    
    if now - client_data["window_start"] > timedelta(seconds=window):
        client_data["count"] = 1
        client_data["window_start"] = now
        return True
    
    if client_data["count"] >= limit:
        return False
    
    client_data["count"] += 1
    return True

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return credentials

def log_security_event(event_type: str, details: str, request: Request):
    client_ip = get_client_ip(request)
    logging.warning(f"SECURITY EVENT - Type: {event_type}, IP: {client_ip}, Details: {details}")

def is_suspicious_query(message: str) -> tuple[bool, str]:
    suspicious_patterns = [
        (r"('|(\\'))", "SQL_QUOTES"),
        (r"(;|\s)(drop|delete|insert|update|alter|create|exec|union|select)\s", "SQL_KEYWORDS"),
        (r"(union\s+(all\s+)?select)", "SQL_UNION"),
        (r"(or\s+.+=.+)", "SQL_OR_CONDITION"),
        (r"(and\s+.+=.+)", "SQL_AND_CONDITION"),
        (r"(--|\/\*|\*\/)", "SQL_COMMENTS"),
        (r"\b(database|table|column|schema|version|postgresql|mysql|sqlite)\b", "INFO_DISCLOSURE"),
        (r"\b(admin|password|user|login|auth|token)\b.*\b(access|show|display|get|list)\b", "PRIVILEGE_REQUEST"),
        (r"\b(show|list|display|execute|run|query)\s+(table|database|schema|structure)", "SYSTEM_QUERY"),
        (r"\bselect\s+.*\bfrom\b", "SELECT_STATEMENT"),
    ]
    
    message_lower = message.lower()
    for pattern, threat_type in suspicious_patterns:
        if re.search(pattern, message_lower):
            return True, threat_type
    
    return False, ""

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    
    @validator('message')
    def validate_message(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        
        sql_patterns = [
            r"('|(\\'))",
            r"(;|\s)(drop|delete|insert|update|alter|create|exec|union|select)\s",
            r"(union\s+(all\s+)?select)",
            r"(or\s+.+=.+)",
            r"(and\s+.+=.+)",
            r"(--|\/\*|\*\/)",
        ]
        
        message_lower = v.lower()
        for pattern in sql_patterns:
            if re.search(pattern, message_lower):
                raise ValueError("Invalid message content")
        
        return v

class InfoCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1, max_length=5000)
    
    @validator('category', 'key', 'value')
    def sanitize_input(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        
        dangerous_patterns = [
            r'(\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|EXEC|EXECUTE|UNION|SELECT)\b)',
            r'(--|;|\*|\/\*|\*\/)',
            r'(\bOR\b.*=.*\b|\bAND\b.*=.*)',
            r"('|(\\'))",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v.upper()):
                raise ValueError(f"Invalid characters detected")
        
        return v.strip()

class FeedbackMessage(BaseModel):
    name: str
    email: str
    category: Literal["feedback", "suggestion", "bug", "feature", "other"]
    subject: str
    message: str

    @validator('name', 'email', 'subject', 'message')
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @validator('email')
    def validate_email_format(cls, v):
        import re
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError("Invalid email format")
        return v

@app.on_event("startup")
async def startup():
    init_db()
    os.makedirs("logs", exist_ok=True)
    logging.info("=== SYSTEM STARTUP COMPLETE ===")

@app.on_event("shutdown")
async def shutdown():
    clear_cache()
    logging.info("=== SYSTEM SHUTDOWN COMPLETE ===")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/chat")
async def chat_api(request: Request, msg: ChatMessage):
    try:
        # Clean up old conversations periodically
        cleanup_old_conversations()
        
        client_ip = get_client_ip(request)
        if not check_rate_limit(client_ip):
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please try again later."
            )
        
        is_suspicious, threat_type = is_suspicious_query(msg.message)
        if is_suspicious:
            log_security_event(f"BLOCKED_{threat_type}", f"Message: {msg.message[:100]}", request)
            
            if threat_type in ["SQL_QUOTES", "SQL_KEYWORDS", "SQL_UNION", "SQL_OR_CONDITION", "SQL_AND_CONDITION", "SQL_COMMENTS"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request format"
                )
            elif threat_type in ["INFO_DISCLOSURE", "PRIVILEGE_REQUEST", "SYSTEM_QUERY", "SELECT_STATEMENT"]:
                return {
                    "response": "I'm an assistant for the University of Sulaimani. I can help you with information about our academic programs, admissions, facilities, and campus life. Please ask me about university-related topics.",
                    "source": "security_filter",
                    "session_id": msg.session_id or str(uuid.uuid4())
                }
        
        # Get or create session
        session_id = get_or_create_session(msg.session_id)
        
        # Get conversation context
        conversation_context = get_conversation_context(session_id)
        
        # Add user message to session
        add_message_to_session(session_id, "user", msg.message)
        
        # Get response with context
        response = ask_claude_with_context(msg.message, conversation_context)
        
        # Add assistant response to session
        add_message_to_session(session_id, "assistant", response)
        
        response_lower = response.lower()
        sensitive_terms = [
            'postgresql', 'database schema', 'table structure', 'sql server',
            'connection string', 'database configuration', 'system information',
            'admin credentials', 'password hash', 'security token'
        ]
        
        if any(term in response_lower for term in sensitive_terms):
            log_security_event("RESPONSE_FILTER", f"Filtered sensitive response for: {msg.message[:50]}", request)
            return {
                "response": "I can help you with University of Sulaimani information including programs, admissions, facilities, and student services. What would you like to know about our university?",
                "source": "security_filter",
                "session_id": session_id
            }
        
        logging.info(f"Session {session_id[:8]} - User: {msg.message}")
        logging.info(f"Session {session_id[:8]} - Claude: {response}")

        
        return {
            "response": response, 
            "source": "claude",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_security_event("CHAT_ERROR", str(e), request)
        logging.error(f"Chat error: {str(e)}")
        try:
            session_id = msg.session_id or str(uuid.uuid4())
            response = ask_openai(msg.message)
            return {
                "response": response, 
                "source": "openai",
                "session_id": session_id
            }
        except Exception as openai_error:
            logging.error(f"OpenAI fallback error: {str(openai_error)}")
            raise HTTPException(status_code=500, detail="AI services temporarily unavailable")

@app.delete("/chat/session/{session_id}")
async def clear_session(session_id: str, request: Request):
    """Clear a specific conversation session"""
    try:
        if session_id in conversation_memory:
            del conversation_memory[session_id]
            logging.info(f"Session {session_id[:8]}... cleared")
            return {"status": "session cleared", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logging.error(f"Clear session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session")

@app.get("/chat/session/{session_id}/history")
async def get_session_history(session_id: str, request: Request):
    """Get conversation history for a session (for debugging/admin)"""
    try:
        if session_id not in conversation_memory:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Only return last 5 messages for brevity
        messages = conversation_memory[session_id]["messages"][-5:]
        return {
            "session_id": session_id,
            "messages": messages,
            "total_messages": len(conversation_memory[session_id]["messages"])
        }
    except Exception as e:
        logging.error(f"Get session history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session history")

# ... (rest of your existing endpoints remain the same)

@app.post("/feedback")
async def submit_feedback(request: Request, feedback: FeedbackMessage):
    try:
        client_ip = get_client_ip(request)
        if not check_rate_limit(client_ip, limit=5, window=3600):
            raise HTTPException(
                status_code=429, 
                detail="Too many feedback submissions. Please try again later."
            )
        
        send_feedback_email(
            name=feedback.name,
            email=feedback.email,
            category=feedback.category,
            subject=feedback.subject,
            message=feedback.message
        )
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Feedback sent successfully."
        })
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Feedback error: {str(e)}")
        return JSONResponse(status_code=500, content={
            "success": False,
            "message": "Unable to send feedback. Please try again later.",
            "error_type": type(e).__name__
        })

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

# ... (all your existing admin endpoints remain the same)

@app.get("/admin/stats")
async def get_stats(_: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    return {
        "rate_limit_entries": len(rate_limit_storage),
        "active_conversations": len(conversation_memory),
        "total_messages": sum(len(session["messages"]) for session in conversation_memory.values()),
        "timestamp": datetime.now()
    }

@app.post("/admin/conversations/cleanup")
async def cleanup_conversations_endpoint(_: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    cleanup_old_conversations()
    return {"status": "conversation cleanup completed", "active_sessions": len(conversation_memory)}