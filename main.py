"""
Daily Ritual — FastAPI Backend (SQLModel + PostgreSQL Modernized)
================================================================
Full auth system + Gemini proxy + user data persistence

SQLMODEL vs TRADITIONAL SQLALCHEMY LESSON:
──────────────────────────────────────────
1. Single Source of Truth: In SQLAlchemy, you define a DB model (Base) AND a Pydantic model (BaseModel)
   for every entity. In SQLModel, `class User(SQLModel, table=True)` creates BOTH the database table AND
   the Pydantic validation schema in a single unified definition.
2. Standard Python Types & Fields: SQLModel replaces `Column(String(100))` with Python type annotations
   `name: str` and `Field(unique=True, index=True)`.
3. Unified Querying API: SQLModel uses `session.exec(select(Model).where(...))` which bridges standard
   SQLAlchemy 2.0 select statements with Pydantic type safety and IDE autocompletion.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session, select
from werkzeug.security import generate_password_hash, check_password_hash

# ─────────────────────────────────────────
# Environment Safeguards & Configuration
# ─────────────────────────────────────────
load_dotenv()

# LESSON: Strict Security & DB Requirement
# Fail loudly if required environment variables are missing (no silent fallback).
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: 'SECRET_KEY' environment variable is missing! "
        "Please specify SECRET_KEY in your environment or .env file before running the application."
    )

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "CRITICAL DATABASE ERROR: 'DATABASE_URL' environment variable is missing! "
        "Please specify a valid PostgreSQL connection string (e.g. from Render Postgres) "
        "in your environment or .env file before starting the application."
    )

# Render provides connection strings starting with 'postgres://', which SQLAlchemy/SQLModel requires to be 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)

# ─────────────────────────────────────────
# SQLModel Database Engine & Session Generator
# ─────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    """Yield a SQLModel session per request, ensuring automatic cleanup."""
    with Session(engine) as session:
        yield session


# ─────────────────────────────────────────
# SQLModel Entities (Unified DB Tables + Validation)
# ─────────────────────────────────────────

class User(SQLModel, table=True):
    """
    User entity mapping to 'users' table in PostgreSQL.
    Serves as both DB model and Pydantic validation schema.
    """
    __tablename__ = 'users'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    plans: List["Plan"] = Relationship(back_populates="user")
    checkins: List["Checkin"] = Relationship(back_populates="user")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email}


class Plan(SQLModel, table=True):
    """Stores AI-generated workout plans per user in 'plans' table."""
    __tablename__ = 'plans'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    plan_json: str = Field(nullable=False)
    goal: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="plans")

    def to_dict(self):
        return {
            'id': self.id,
            'plan': json.loads(self.plan_json),
            'goal': self.goal,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class Checkin(SQLModel, table=True):
    """Stores daily exercise checkins in 'checkins' table."""
    __tablename__ = 'checkins'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    date: str = Field(nullable=False)
    exercises: str = Field(default='{}')
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="checkins")


# ─────────────────────────────────────────
# Request Data Transfer Objects (Input Schemas)
# ─────────────────────────────────────────

class RegisterRequest(SQLModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)

class LoginRequest(SQLModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)

class PlanSaveRequest(SQLModel):
    plan: Any
    goal: Optional[str] = ""

class CheckinRequest(SQLModel):
    date: str
    exercises: Optional[Dict[str, Any]] = {}

class ChatMessage(SQLModel):
    role: str
    content: str

class ChatRequest(SQLModel):
    system: Optional[str] = ""
    messages: List[ChatMessage] = []


# ─────────────────────────────────────────
# FastAPI App & Security Initialization
# ─────────────────────────────────────────
app = FastAPI(
    title="Daily Ritual API",
    description="FastAPI + SQLModel + PostgreSQL Backend for Daily Ritual",
    version="3.0.0"
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security_scheme = HTTPBearer(auto_error=False)


@app.on_event("startup")
def on_startup():
    """Create database tables on application startup."""
    SQLModel.metadata.create_all(engine)


# ─────────────────────────────────────────
# Auth Helpers & FastAPI Dependency Injection
# ─────────────────────────────────────────

def generate_token(user_id: int) -> str:
    """Generate 7-day JWT token."""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def verify_token(token: str) -> Optional[int]:
    """Verify JWT token signature and return user_id."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload.get('user_id')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    session: Session = Depends(get_session)
) -> User:
    """Dependency injecting authenticated User object via Authorization header."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized — please log in"
        )
    
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized — please log in"
        )
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized — please log in"
        )
    
    return user


# ─────────────────────────────────────────
# Auth Routes
# ─────────────────────────────────────────

@app.post('/auth/register', status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_session)):
    name = payload.name.strip()
    email = payload.email.strip().lower()
    password = payload.password

    if not name or not email or not password:
        return JSONResponse(status_code=400, content={'error': 'Name, email and password are required'})
    if len(password) < 6:
        return JSONResponse(status_code=400, content={'error': 'Password must be at least 6 characters'})
    
    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        return JSONResponse(status_code=409, content={'error': 'An account with this email already exists'})

    user = User(name=name, email=email, password_hash="")
    user.set_password(password)
    session.add(user)
    session.commit()
    session.refresh(user)

    token = generate_token(user.id)
    return {'token': token, 'user': user.to_dict()}


@app.post('/auth/login')
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    email = payload.email.strip().lower()
    password = payload.password

    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not user.check_password(password):
        return JSONResponse(status_code=401, content={'error': 'Invalid email or password'})

    token = generate_token(user.id)
    return {'token': token, 'user': user.to_dict()}


@app.get('/auth/me')
def me(current_user: User = Depends(get_current_user)):
    return {'user': current_user.to_dict()}


# ─────────────────────────────────────────
# Plan Routes
# ─────────────────────────────────────────

@app.post('/api/plan/save', status_code=status.HTTP_201_CREATED)
def save_plan(
    payload: PlanSaveRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not payload.plan:
        return JSONResponse(status_code=400, content={'error': 'No plan provided'})

    # Deactivate existing active plans using SQLModel select
    existing_plans = session.exec(select(Plan).where(Plan.user_id == current_user.id, Plan.is_active == True)).all()
    for p in existing_plans:
        p.is_active = False
        session.add(p)

    # Save new active plan
    plan = Plan(
        user_id=current_user.id,
        plan_json=json.dumps(payload.plan),
        goal=payload.goal or "",
        is_active=True
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)

    return {'message': 'Plan saved', 'plan_id': plan.id}


@app.get('/api/plan/active')
def get_active_plan(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    plan = session.exec(select(Plan).where(Plan.user_id == current_user.id, Plan.is_active == True)).first()
    if not plan:
        return {'plan': None}
    return plan.to_dict()


@app.post('/api/plan/clear')
def clear_plan(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    plans = session.exec(select(Plan).where(Plan.user_id == current_user.id)).all()
    for p in plans:
        p.is_active = False
        session.add(p)
    session.commit()
    return {'message': 'Switched to regular workout'}


# ─────────────────────────────────────────
# Checkin Routes
# ─────────────────────────────────────────

@app.post('/api/checkin')
def checkin(
    payload: CheckinRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    date_str = payload.date
    exercises = payload.exercises or {}

    existing = session.exec(
        select(Checkin).where(Checkin.user_id == current_user.id, Checkin.date == date_str)
    ).first()

    if existing:
        existing.exercises = json.dumps(exercises)
        session.add(existing)
    else:
        c = Checkin(user_id=current_user.id, date=date_str, exercises=json.dumps(exercises))
        session.add(c)
    
    session.commit()
    return {'message': 'Checked in'}


@app.get('/api/checkins')
def get_checkins(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    checkins = session.exec(select(Checkin).where(Checkin.user_id == current_user.id)).all()
    return {'checkins': [c.date for c in checkins]}


# ─────────────────────────────────────────
# Async Gemini Proxy Route
# ─────────────────────────────────────────

@app.post('/api/chat')
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    if not GEMINI_API_KEY:
        return JSONResponse(status_code=500, content={'error': {'message': 'GEMINI_API_KEY not set'}})

    contents = []
    for msg in payload.messages:
        role = 'model' if msg.role == 'assistant' else 'user'
        contents.append({'role': role, 'parts': [{'text': msg.content}]})

    gemini_body = {
        'systemInstruction': {'parts': [{'text': payload.system or ""}]},
        'contents': contents,
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 2500,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GEMINI_URL.format(key=GEMINI_API_KEY),
                headers={'Content-Type': 'application/json'},
                json=gemini_body,
            )
            gemini_data = response.json()
    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content={'error': {'message': 'Gemini timed out'}})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': {'message': str(e)}})

    if 'error' in gemini_data:
        return JSONResponse(status_code=500, content={'error': {'message': gemini_data['error'].get('message', 'Gemini error')}})

    try:
        text = gemini_data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        return JSONResponse(status_code=500, content={'error': {'message': 'Unexpected Gemini response shape'}})

    return {'content': [{'type': 'text', 'text': text}]}


# ─────────────────────────────────────────
# Health Check Route
# ─────────────────────────────────────────

@app.get('/health')
def health():
    return {
        'status': 'ok',
        'provider': 'Gemini 1.5 Flash',
        'key_loaded': bool(GEMINI_API_KEY)
    }


# ─────────────────────────────────────────
# Server Runner
# ─────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    print("\n✦ Daily Ritual FastAPI + SQLModel server starting...")
    print(f"✦ Gemini key loaded: {bool(GEMINI_API_KEY)}")
    print(f"✦ Health check → http://localhost:{port}/health")
    print(f"✦ Interactive API Docs → http://localhost:{port}/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
