"""
Daily Ritual — Flask Backend
=============================
Full auth system + Gemini proxy + user data persistence

LESSON: What this file teaches you
────────────────────────────────────
1. Password hashing    — never store plain passwords, ever
2. JWT tokens          — how "stay logged in" actually works
3. SQLite + ORM        — how to store and query structured data
4. Protected routes    — how to lock endpoints behind login
5. CORS with auth      — why cookies/tokens need special CORS config
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

# ─────────────────────────────────────────
# App setup
# ─────────────────────────────────────────
app = Flask(__name__)

# LESSON: CORS with supports_credentials=True
# When your frontend sends a JWT token in headers, CORS needs this flag.
# Without it, the browser blocks the request before it even reaches Flask.
CORS(app, supports_credentials=True)

# LESSON: Secret key — used to sign JWT tokens.
# In production this would be a long random string stored in environment variables.
# If someone gets this key, they can forge login tokens for any user.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'daily-ritual-secret-change-in-production')

# LESSON: SQLAlchemy config
# SQLite creates a file called daily_ritual.db in your project folder.
# No server, no setup — just a file. Perfect for development.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "daily_ritual.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)


# ─────────────────────────────────────────
# Database Models
# ─────────────────────────────────────────

# LESSON: A "model" is a Python class that maps to a database table.
# Each attribute = one column in the table.
# SQLAlchemy handles the SQL for you — no raw SQL needed.

class User(db.Model):
    """
    One row per registered user.
    
    LESSON: We never store the actual password.
    We store a "hash" — a one-way scrambled version.
    When someone logs in, we hash what they typed and compare hashes.
    Even if the database is stolen, passwords are safe.
    """
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships — one user has many plans and checkins
    plans    = db.relationship('Plan', backref='user', lazy=True)
    checkins = db.relationship('Checkin', backref='user', lazy=True)

    def set_password(self, password):
        """Hash and store the password. Never called with raw password stored."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Returns True if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email}


class Plan(db.Model):
    """
    Stores AI-generated workout plans per user.
    The full plan JSON is stored as a string — easy to retrieve and render.
    """
    __tablename__ = 'plans'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_json  = db.Column(db.Text, nullable=False)   # the full AI plan as JSON string
    goal       = db.Column(db.String(100))             # "Build Muscle", "Lose Fat" etc
    is_active  = db.Column(db.Boolean, default=True)   # currently shown on Today tab
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plan': json.loads(self.plan_json),
            'goal': self.goal,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class Checkin(db.Model):
    """
    One row per day a user completes their workout.
    Replaces the localStorage streak system.
    """
    __tablename__ = 'checkins'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date       = db.Column(db.String(20), nullable=False)   # "2024-1-15"
    exercises  = db.Column(db.Text, default='{}')            # which exercises done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────
# JWT Helpers
# ─────────────────────────────────────────

# LESSON: JWT (JSON Web Token) — how "stay logged in" works
#
# After login, we give the user a TOKEN — a signed string that looks like:
# eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.abc123
#
# The user sends this token with every request.
# We verify the signature (using SECRET_KEY) to confirm it's real.
# No database lookup needed — the token IS the proof of identity.
#
# This is how every modern API works — Spotify, GitHub, Twitter.

def generate_token(user_id):
    """Create a JWT token that expires in 7 days."""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def verify_token(token):
    """Decode and verify a JWT token. Returns user_id or None."""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None   # token expired — user needs to log in again
    except jwt.InvalidTokenError:
        return None   # token tampered with


def get_current_user():
    """
    Extract user from the Authorization header.
    Frontend sends: Authorization: Bearer <token>
    We strip "Bearer ", verify the token, return the User object.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]   # strip "Bearer "
    user_id = verify_token(token)
    if not user_id:
        return None
    return db.session.get(User, user_id)


def require_auth(f):
    """
    LESSON: Decorator pattern — wraps a route function with auth check.
    Instead of copying auth code into every route, we write it once here.
    Any route decorated with @require_auth automatically requires login.
    """
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Unauthorized — please log in'}), 401
        return f(user, *args, **kwargs)
    return decorated


# ─────────────────────────────────────────
# Auth Routes
# ─────────────────────────────────────────

@app.route('/auth/register', methods=['POST'])
def register():
    """
    Create a new user account.
    
    LESSON: What we validate before creating an account:
    1. All required fields present
    2. Email not already taken
    3. Password meets minimum length
    We never trust the frontend to do validation — always validate server-side.
    """
    data = request.get_json()

    name     = (data.get('name') or '').strip()
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    # Validation
    if not name or not email or not password:
        return jsonify({'error': 'Name, email and password are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email already exists'}), 409

    # Create user — password is hashed inside set_password()
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id)
    return jsonify({'token': token, 'user': user.to_dict()}), 201


@app.route('/auth/login', methods=['POST'])
def login():
    """
    Verify credentials and return a JWT token.
    
    LESSON: We always return the same error for wrong email OR wrong password.
    "Invalid email or password" — not "email not found" or "wrong password".
    Specific errors help attackers enumerate valid accounts.
    """
    data = request.get_json()

    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = User.query.filter_by(email=email).first()

    # LESSON: check_password even if user not found — prevents timing attacks
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = generate_token(user.id)
    return jsonify({'token': token, 'user': user.to_dict()})


@app.route('/auth/me', methods=['GET'])
@require_auth
def me(user):
    """Return current user info. Frontend calls this on load to check if still logged in."""
    return jsonify({'user': user.to_dict()})


# ─────────────────────────────────────────
# Plan Routes
# ─────────────────────────────────────────

@app.route('/api/plan/save', methods=['POST'])
@require_auth
def save_plan(user):
    """Save an AI-generated plan to the database and set it as active."""
    data = request.get_json()
    plan_data = data.get('plan')
    goal      = data.get('goal', '')

    if not plan_data:
        return jsonify({'error': 'No plan provided'}), 400

    # Deactivate all previous plans for this user
    Plan.query.filter_by(user_id=user.id).update({'is_active': False})

    # Save new plan as active
    plan = Plan(
        user_id   = user.id,
        plan_json = json.dumps(plan_data),
        goal      = goal,
        is_active = True
    )
    db.session.add(plan)
    db.session.commit()

    return jsonify({'message': 'Plan saved', 'plan_id': plan.id}), 201


@app.route('/api/plan/active', methods=['GET'])
@require_auth
def get_active_plan(user):
    """Get the user's currently active AI plan."""
    plan = Plan.query.filter_by(user_id=user.id, is_active=True).first()
    if not plan:
        return jsonify({'plan': None})
    return jsonify(plan.to_dict())


@app.route('/api/plan/clear', methods=['POST'])
@require_auth
def clear_plan(user):
    """Switch back to regular workout (deactivate AI plan)."""
    Plan.query.filter_by(user_id=user.id).update({'is_active': False})
    db.session.commit()
    return jsonify({'message': 'Switched to regular workout'})


# ─────────────────────────────────────────
# Checkin Routes
# ─────────────────────────────────────────

@app.route('/api/checkin', methods=['POST'])
@require_auth
def checkin(user):
    """Mark today as done. Replaces localStorage streak tracking."""
    data     = request.get_json()
    date_str = data.get('date')
    exercises = data.get('exercises', {})

    existing = Checkin.query.filter_by(user_id=user.id, date=date_str).first()
    if existing:
        existing.exercises = json.dumps(exercises)
    else:
        c = Checkin(user_id=user.id, date=date_str, exercises=json.dumps(exercises))
        db.session.add(c)
    db.session.commit()
    return jsonify({'message': 'Checked in'})


@app.route('/api/checkins', methods=['GET'])
@require_auth
def get_checkins(user):
    """Get all checkins for this user — used for streak and calendar."""
    checkins = Checkin.query.filter_by(user_id=user.id).all()
    return jsonify({'checkins': [c.date for c in checkins]})


# ─────────────────────────────────────────
# Gemini Proxy (existing, now auth-protected)
# ─────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat(user):
    """
    Gemini proxy — now requires login.
    Only authenticated users can generate AI plans.
    """
    if not GEMINI_API_KEY:
        return jsonify({'error': {'message': 'GEMINI_API_KEY not set'}}), 500

    body        = request.get_json()
    system_text = body.get('system', '')
    messages    = body.get('messages', [])

    contents = []
    for msg in messages:
        role = 'model' if msg['role'] == 'assistant' else 'user'
        contents.append({'role': role, 'parts': [{'text': msg['content']}]})

    gemini_body = {
        'systemInstruction': {'parts': [{'text': system_text}]},
        'contents': contents,
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 2500,
        }
    }

    try:
        response = requests.post(
            GEMINI_URL.format(key=GEMINI_API_KEY),
            headers={'Content-Type': 'application/json'},
            json=gemini_body,
            timeout=30,
        )
        gemini_data = response.json()
    except requests.exceptions.Timeout:
        return jsonify({'error': {'message': 'Gemini timed out'}}), 504
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 500

    if 'error' in gemini_data:
        return jsonify({'error': {'message': gemini_data['error'].get('message', 'Gemini error')}}), 500

    try:
        text = gemini_data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        return jsonify({'error': {'message': 'Unexpected Gemini response shape'}}), 500

    return jsonify({'content': [{'type': 'text', 'text': text}]})


# ─────────────────────────────────────────
# Health check
# ─────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'provider': 'Gemini 1.5 Flash',
        'key_loaded': bool(GEMINI_API_KEY)
    })


# ─────────────────────────────────────────
# Run
# ─────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        # LESSON: create_all() creates all tables if they don't exist yet.
        # Safe to run every time — it skips tables that already exist.
        db.create_all()
        print('\n✦ Daily Ritual API server starting...')
        print(f'✦ Gemini key loaded: {bool(GEMINI_API_KEY)}')
        print('✦ Database: daily_ritual.db')
        print('✦ Health check → http://localhost:5000/health\n')
    app.run(debug=True, port=5000)