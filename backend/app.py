from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
from datetime import datetime, timedelta
from typing import Literal, Dict
import logging
import os
import hashlib
import re
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv
from backend.database import SessionLocal, Info, init_db
from backend.claude_api import ask_claude, clear_cache, cleanup_cache
from chatgpt_api import ask_openai

load_dotenv()

logging.basicConfig(filename='logs/chat_logs.txt', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(docs_url=None, redoc_url=None)

templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="/app/frontend/static"), name="static")

security = HTTPBearer()
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

rate_limit_storage: Dict[str, Dict] = {}

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
                    "source": "security_filter"
                }
        
        message_hash = hashlib.md5(msg.message.encode()).hexdigest()
        
        response = ask_claude(msg.message)
        
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
                "source": "security_filter"
            }
        
        logging.info(f"User: {msg.message[:100]}{'...' if len(msg.message) > 100 else ''}")
        logging.info(f"Claude: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        return {"response": response, "source": "claude"}
    except HTTPException:
        raise
    except Exception as e:
        log_security_event("CHAT_ERROR", str(e), request)
        logging.error(f"Chat error: {str(e)}")
        try:
            response = ask_openai(msg.message)
            return {"response": response, "source": "openai"}
        except Exception as openai_error:
            logging.error(f"OpenAI fallback error: {str(openai_error)}")
            raise HTTPException(status_code=500, detail="AI services temporarily unavailable")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/admin/info/add")
async def add_info(request: Request, data: InfoCreate, _: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    try:
        with get_db_session() as db:
            existing = db.query(Info).filter(
                Info.category == data.category,
                Info.key == data.key
            ).first()
            
            if existing:
                raise HTTPException(status_code=409, detail="Record with this category and key already exists")
            
            clear_cache()
            db.add(Info(category=data.category, key=data.key, value=data.value))
            
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        log_security_event("ADMIN_ADD_ERROR", str(e), request)
        raise HTTPException(status_code=500, detail="Failed to add record")

@app.get("/admin/info")
async def list_info(_: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    try:
        with get_db_session() as db:
            results = db.query(Info).all()
            return [{"id": r.id, "category": r.category, "key": r.key, "value": r.value} for r in results]
    except Exception as e:
        logging.error(f"List info error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve records")

@app.delete("/admin/info/{info_id}")
async def delete_info(info_id: int, request: Request, _: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    try:
        with get_db_session() as db:
            record = db.query(Info).filter(Info.id == info_id).first()
            if not record:
                raise HTTPException(status_code=404, detail="Record not found")
            
            clear_cache()
            db.delete(record)
            
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        log_security_event("ADMIN_DELETE_ERROR", str(e), request)
        raise HTTPException(status_code=500, detail="Failed to delete record")

@app.put("/admin/info/{info_id}")
async def update_info(info_id: int, request: Request, data: InfoCreate, _: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    try:
        with get_db_session() as db:
            record = db.query(Info).filter(Info.id == info_id).first()
            if not record:
                raise HTTPException(status_code=404, detail="Record not found")
            
            clear_cache()
            record.category = data.category
            record.key = data.key
            record.value = data.value
            
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        log_security_event("ADMIN_UPDATE_ERROR", str(e), request)
        raise HTTPException(status_code=500, detail="Failed to update record")

@app.post("/admin/cache/clear")
async def clear_cache_endpoint(_: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    clear_cache()
    return {"status": "cache cleared"}

@app.post("/admin/cache/cleanup")
async def cleanup_cache_endpoint(_: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    cleanup_cache()
    return {"status": "cache cleanup completed"}

@app.get("/admin/stats")
async def get_stats(_: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    return {
        "rate_limit_entries": len(rate_limit_storage),
        "timestamp": datetime.now()
    }