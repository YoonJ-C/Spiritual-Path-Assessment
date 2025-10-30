"""
Concept: Flask + HTML Integration - Spiritual Path Assessment Tool
This app helps users discover which religious or spiritual path aligns with their 
beliefs, values, lifestyle, and background through an interactive questionnaire.
"""
# cSpell:ignore jsonify werkzeug dotenv puja moksha sikhism jainism shintoism paganism wicca

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import re
import secrets
from dotenv import load_dotenv
from together import Together
from rag_utils import load_religions_from_csv, prepare_religion_rag_context
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, auth, firestore

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Session configuration for production deployment
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Initialize Firebase Admin SDK
try:
    firebase_cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
    if os.path.exists(firebase_cred_path):
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase initialized successfully")
    else:
        print(f"⚠️ Firebase credentials not found at {firebase_cred_path}")
        db = None
except Exception as e:
    print(f"⚠️ Firebase initialization failed: {e}")
    db = None

# Firebase Web Config (for frontend)
FIREBASE_CONFIG = {
    'apiKey': os.getenv('FIREBASE_WEB_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', f"{os.getenv('FIREBASE_PROJECT_ID')}.appspot.com"),
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.getenv('FIREBASE_APP_ID')
}

# File to store user data - defaults to current directory (writable in Docker)
# Keep for backward compatibility during transition
USERS_FILE = os.getenv("USERS_FILE", "users_data.json")

# Together API for chatbot
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=TOGETHER_API_KEY) if TOGETHER_API_KEY else None

# OpenAI for Whisper transcription
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Load detailed religion data at startup
RELIGIONS_CSV = load_religions_from_csv('religions.csv')

# Assessment Questions
QUESTIONS = [
    {
        "id": 1,
        "question": "What is your view on the nature of the divine?",
        "options": {
            "One supreme God who created everything": {"christianity": 3, "islam": 3, "judaism": 3},
            "Multiple gods and goddesses": {"hinduism": 3, "paganism": 3},
            "A universal energy or force": {"buddhism": 2, "taoism": 3, "new_age": 3},
            "No divine being, focus on human potential": {"humanism": 3, "atheism": 3},
            "Uncertain or unknowable": {"agnosticism": 3}
        }
    },
    {
        "id": 2,
        "question": "How do you prefer to connect with spirituality?",
        "options": {
            "Through organized worship and community": {"christianity": 2, "islam": 2, "judaism": 2},
            "Through personal meditation and reflection": {"buddhism": 3, "hinduism": 2, "taoism": 2},
            "Through nature and natural cycles": {"paganism": 3, "indigenous": 3},
            "Through reason and philosophy": {"humanism": 2, "stoicism": 3},
            "I don't feel the need for spiritual connection": {"atheism": 3}
        }
    },
    {
        "id": 3,
        "question": "What is your belief about the afterlife?",
        "options": {
            "Heaven or Hell based on faith/deeds": {"christianity": 3, "islam": 3},
            "Reincarnation until enlightenment": {"hinduism": 3, "buddhism": 3},
            "Ancestral realm or spiritual world": {"indigenous": 2, "paganism": 2},
            "No afterlife, this life is all there is": {"atheism": 3, "humanism": 2},
            "Unsure or open to possibilities": {"agnosticism": 2, "new_age": 2}
        }
    },
    {
        "id": 4,
        "question": "What guides your moral and ethical decisions?",
        "options": {
            "Sacred texts and religious teachings": {"christianity": 3, "islam": 3, "judaism": 3},
            "Universal principles of compassion and mindfulness": {"buddhism": 3, "jainism": 3},
            "Harmony with nature and balance": {"taoism": 3, "indigenous": 2},
            "Reason, empathy, and human rights": {"humanism": 3, "secularism": 3},
            "Personal intuition and inner wisdom": {"new_age": 2, "spiritualism": 3}
        }
    },
    {
        "id": 5,
        "question": "What role does ritual or practice play in your life?",
        "options": {
            "Regular prayer and worship are essential": {"islam": 3, "christianity": 2, "judaism": 2},
            "Daily meditation or mindfulness practice": {"buddhism": 3, "hinduism": 2, "zen": 3},
            "Seasonal celebrations and ceremonies": {"paganism": 3, "wicca": 3},
            "Minimal to no ritual, prefer intellectual engagement": {"humanism": 2, "deism": 2},
            "Flexible, whatever feels meaningful to me": {"new_age": 2, "spiritual_not_religious": 3}
        }
    },
    {
        "id": 6,
        "question": "How do you view the relationship between humans and nature?",
        "options": {
            "Humans are stewards of God's creation": {"christianity": 2, "islam": 2, "judaism": 2},
            "All life is interconnected and sacred": {"buddhism": 2, "hinduism": 2, "jainism": 3},
            "Nature itself is divine": {"paganism": 3, "pantheism": 3, "indigenous": 3},
            "Nature follows natural laws we can understand": {"atheism": 2, "humanism": 2},
            "We should live in harmony with natural flow": {"taoism": 3, "shintoism": 2}
        }
    },
    {
        "id": 7,
        "question": "What is your view on suffering and its purpose?",
        "options": {
            "A test of faith or part of God's plan": {"christianity": 2, "islam": 2},
            "Result of attachment and desire": {"buddhism": 3, "stoicism": 2},
            "Karma from past actions": {"hinduism": 3, "sikhism": 2},
            "Random or result of natural causes": {"atheism": 3, "secular": 2},
            "An opportunity for growth and learning": {"new_age": 2, "spiritualism": 2}
        }
    },
    {
        "id": 8,
        "question": "How important is community in your spiritual life?",
        "options": {
            "Very important, prefer group worship": {"christianity": 2, "islam": 2, "sikhism": 3},
            "Somewhat important, but personal practice matters more": {"buddhism": 2, "hinduism": 2},
            "Community of like-minded seekers": {"paganism": 2, "unitarian": 3},
            "Not important, spirituality is personal": {"spiritual_not_religious": 3, "deism": 2},
            "Prefer secular community over religious": {"humanism": 2, "atheism": 2}
        }
    }
]

# Religion Descriptions
RELIGIONS = {
    "christianity": {"name": "Christianity", "description": "Faith in Jesus Christ emphasizing love, forgiveness, and salvation through grace.", "practices": "Prayer, Bible study, church, communion", "core_beliefs": "Trinity, salvation through Christ, eternal life"},
    "islam": {"name": "Islam", "description": "Submission to Allah through Prophet Muhammad's teachings and the Quran.", "practices": "Five daily prayers, Ramadan fasting, charity, Mecca pilgrimage", "core_beliefs": "One God (Allah), Muhammad as prophet, Day of Judgment"},
    "buddhism": {"name": "Buddhism", "description": "Path to enlightenment through mindfulness and compassion.", "practices": "Meditation, mindfulness, Eightfold Path", "core_beliefs": "Four Noble Truths, impermanence, ending suffering"},
    "hinduism": {"name": "Hinduism", "description": "Ancient tradition embracing diverse paths to spiritual realization.", "practices": "Yoga, meditation, puja, festivals", "core_beliefs": "Dharma, karma, reincarnation, moksha, multiple paths"},
    "judaism": {"name": "Judaism", "description": "Covenant with God through Torah and Jewish community.", "practices": "Shabbat, Torah study, prayer, kosher", "core_beliefs": "One God, Torah as divine law, ethical monotheism"},
    "taoism": {"name": "Taoism", "description": "Living in harmony with the Tao - the natural order.", "practices": "Meditation, tai chi, wu wei, simplicity", "core_beliefs": "Yin-yang balance, harmony with nature"},
    "paganism": {"name": "Modern Paganism", "description": "Nature-based spirituality honoring seasonal cycles.", "practices": "Seasonal celebrations, rituals, nature work", "core_beliefs": "Nature as sacred, multiple deities"},
    "humanism": {"name": "Secular Humanism", "description": "Ethics emphasizing human values and reason without supernatural beliefs.", "practices": "Critical thinking, ethical living, community service", "core_beliefs": "Human dignity, reason, science, secular ethics"},
    "atheism": {"name": "Atheism", "description": "Lack of belief in deities with naturalistic worldview.", "practices": "Evidence-based thinking, secular community", "core_beliefs": "No gods, natural explanations, this-life focus"},
    "agnosticism": {"name": "Agnosticism", "description": "Divine existence is unknown or unknowable.", "practices": "Philosophical inquiry, ethical living", "core_beliefs": "Uncertainty about divine, questions over answers"},
    "new_age": {"name": "New Age Spirituality", "description": "Eclectic approach emphasizing personal growth.", "practices": "Meditation, energy work, crystals, yoga", "core_beliefs": "Personal transformation, universal consciousness"},
    "spiritual_not_religious": {"name": "Spiritual But Not Religious", "description": "Personal spirituality without organized religion.", "practices": "Personal practices, meditation, self-reflection", "core_beliefs": "Individual journey, authenticity, diverse wisdom"},
    "sikhism": {"name": "Sikhism", "description": "One God emphasizing service, equality, and meditation.", "practices": "Prayer, meditation, community service, 5 Ks", "core_beliefs": "One God, equality, honest living, sharing"},
    "indigenous": {"name": "Indigenous Spirituality", "description": "Traditional practices honoring ancestors and land.", "practices": "Ceremonies, storytelling, seasonal rituals", "core_beliefs": "Land connection, ancestor veneration, reciprocity"}
}

# Email verification tokens (in-memory for simplicity)
VERIFICATION_TOKENS = {}

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_verification_email(email, token):
    """Send verification email (dev mode: prints to console)"""
    verification_url = f"{request.host_url}verify-email?token={token}"
    message = f"""
    Hello!
    
    Please verify your email by clicking this link:
    {verification_url}
    
    Or visit: {request.host_url}verify-email?token={token}
    """
    print(f"[EMAIL] To: {email}")
    print(f"[EMAIL] Subject: Verify your email")
    print(f"[EMAIL] Body:\n{message}")
    # In production, replace with actual SMTP sending
    return True

def send_password_reset_email(email, token):
    """Send password reset email (dev mode: prints to console)"""
    reset_url = f"{request.host_url}reset-password?token={token}"
    message = f"""
    Hello!
    
    You requested a password reset. Click this link:
    {reset_url}
    
    Or visit: {request.host_url}reset-password?token={token}
    """
    print(f"[EMAIL] To: {email}")
    print(f"[EMAIL] Subject: Password Reset Request")
    print(f"[EMAIL] Body:\n{message}")
    # In production, replace with actual SMTP sending
    return True

# ============================================================================
# FIRESTORE HELPER FUNCTIONS
# ============================================================================

def get_user_by_uid(uid):
    """Get user data from Firestore by Firebase UID"""
    if not db:
        return None
    try:
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    except Exception as e:
        print(f"Error getting user {uid}: {e}")
        return None

def create_or_update_user(uid, user_data):
    """Create or update user in Firestore"""
    if not db:
        return False
    try:
        user_ref = db.collection('users').document(uid)
        user_ref.set(user_data, merge=True)
        return True
    except Exception as e:
        print(f"Error saving user {uid}: {e}")
        return False

def get_user_answers(uid):
    """Get user's assessment answers from Firestore"""
    if not db:
        return []
    try:
        user_data = get_user_by_uid(uid)
        return user_data.get('answers', []) if user_data else []
    except Exception as e:
        print(f"Error getting answers for {uid}: {e}")
        return []

def save_user_answers(uid, answers):
    """Save user's assessment answers to Firestore"""
    if not db:
        return False
    try:
        user_ref = db.collection('users').document(uid)
        user_ref.update({'answers': answers})
        return True
    except Exception as e:
        print(f"Error saving answers for {uid}: {e}")
        return False

def get_user_results(uid):
    """Get user's assessment results from Firestore"""
    if not db:
        return []
    try:
        user_data = get_user_by_uid(uid)
        return user_data.get('results', []) if user_data else []
    except Exception as e:
        print(f"Error getting results for {uid}: {e}")
        return []

def save_user_results(uid, results):
    """Save user's assessment results to Firestore"""
    if not db:
        return False
    try:
        user_ref = db.collection('users').document(uid)
        user_ref.update({'results': results})
        return True
    except Exception as e:
        print(f"Error saving results for {uid}: {e}")
        return False

def verify_firebase_token(id_token):
    """Verify Firebase ID token and return decoded token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

# ============================================================================
# LEGACY JSON FILE FUNCTIONS (for backward compatibility)
# ============================================================================

def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
    return {}

def save_users(users):
    """Save users to JSON file"""
    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(USERS_FILE) if os.path.dirname(USERS_FILE) else '.', exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def initialize_default_user():
    """Create default test user if no users exist"""
    users = load_users()
    if not users:  # Only create if no users exist
        users['test'] = {
            'password': generate_password_hash('test'),
            'email': 'test@example.com',
            'verified': True,
            'answers': [],
            'results': []
        }
        save_users(users)
        print("✅ Default test user created (username: test, password: test)")

def calculate_results(answers):
    """Calculate which spiritual paths align with user's answers"""
    scores = {}
    
    for answer in answers:
        question = next((q for q in QUESTIONS if q["id"] == answer["question_id"]), None)
        if question and answer["answer"] in question["options"]:
            points = question["options"][answer["answer"]]
            for religion, score in points.items():
                scores[religion] = scores.get(religion, 0) + score
    
    # Sort by score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Get top 3 recommendations
    recommendations = []
    for religion_key, score in sorted_scores[:3]:
        if religion_key in RELIGIONS:
            religion_info = RELIGIONS[religion_key].copy()
            religion_info["score"] = score
            religion_info["percentage"] = round((score / (len(answers) * 3)) * 100)
            recommendations.append(religion_info)
    
    return recommendations

@app.route("/")
def landing():
    return render_template('landing.html')

@app.route("/assessment")
def assessment():
    # Check for Firebase user first, then legacy username
    user_id = session.get('user_id')
    username = session.get('username')
    
    if not user_id and not username:
        return redirect(url_for('login'))
    
    # Get user data from appropriate source
    if user_id:
        # Firebase user
        user_data = get_user_by_uid(user_id) or {}
        display_name = session.get('email', 'User')
        has_results = 'results' in user_data and user_data['results']
    else:
        # Legacy user
        users = load_users()
        user_data = users.get(username, {})
        display_name = username
        has_results = 'results' in user_data and user_data['results']
    
    return render_template(
        "index.html", 
        title="Spiritual Path Finder", 
        message=f"Welcome, {display_name}!",
        username=display_name,
        logged_in=True,
        questions=QUESTIONS,
        has_results=has_results,
        results=user_data.get('results', []) if has_results else [],
        firebase_config=FIREBASE_CONFIG
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "Invalid request"}), 400
            
            # Firebase authentication - verify ID token from frontend
            id_token = data.get('idToken')
            
            if id_token:
                # Firebase authentication flow
                decoded_token = verify_firebase_token(id_token)
                if not decoded_token:
                    return jsonify({"success": False, "message": "Invalid authentication token"}), 401
                
                uid = decoded_token['uid']
                email = decoded_token.get('email', '')
                
                # Check if user exists in Firestore, create if not
                user_data = get_user_by_uid(uid)
                if not user_data:
                    # Create new user document
                    create_or_update_user(uid, {
                        'email': email,
                        'answers': [],
                        'results': [],
                        'created_at': firestore.SERVER_TIMESTAMP
                    })
                
                # Store UID in session
                session['user_id'] = uid
                session['email'] = email
                session.permanent = True
                return jsonify({"success": True})
            else:
                # Legacy username/password flow (backward compatibility)
                username = data.get('username', '').strip()
                password = data.get('password', '')
                
                if not username or not password:
                    return jsonify({"success": False, "message": "Username and password required"}), 400
                
                users = load_users()
                if username not in users:
                    return jsonify({"success": False, "message": "Invalid credentials"}), 401
                
                user_data = users[username]
                
                # Check if email is verified
                if not user_data.get('verified', True):
                    return jsonify({"success": False, "message": "Please verify your email first. Check your inbox."}), 403
                
                stored = user_data['password']
                
                # Try hash-based verification first
                if stored.startswith(('scrypt:', 'pbkdf2:')):
                    if check_password_hash(stored, password):
                        session['username'] = username
                        session.permanent = True
                        return jsonify({"success": True})
                # Legacy plaintext fallback
                elif stored == password:
                    users[username]['password'] = generate_password_hash(password)
                    if not save_users(users):
                        return jsonify({"success": False, "message": "Error saving data"}), 500
                    session['username'] = username
                    session.permanent = True
                    return jsonify({"success": True})
                
                return jsonify({"success": False, "message": "Invalid credentials"}), 401
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({"success": False, "message": "Server error"}), 500
    
    # Pass Firebase config to template
    return render_template("index.html", logged_in=False, is_signup=False, firebase_config=FIREBASE_CONFIG)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "Invalid request"}), 400
            
            # Firebase authentication - verify ID token from frontend
            id_token = data.get('idToken')
            
            if id_token:
                # Firebase signup flow (user already created by Firebase Auth on frontend)
                decoded_token = verify_firebase_token(id_token)
                if not decoded_token:
                    return jsonify({"success": False, "message": "Invalid authentication token"}), 401
                
                uid = decoded_token['uid']
                email = decoded_token.get('email', '')
                
                # Create user document in Firestore
                user_data = {
                    'email': email,
                    'answers': [],
                    'results': [],
                    'created_at': firestore.SERVER_TIMESTAMP
                }
                
                if create_or_update_user(uid, user_data):
                    session['user_id'] = uid
                    session['email'] = email
                    session.permanent = True
                    return jsonify({
                        "success": True,
                        "message": "Account created successfully!"
                    })
                else:
                    return jsonify({"success": False, "message": "Error creating user profile"}), 500
            else:
                # Legacy username/password flow (backward compatibility)
                username = data.get('username', '').strip()
                password = data.get('password', '')
                email = data.get('email', '').strip().lower()
                
                if not username or not password:
                    return jsonify({"success": False, "message": "Username and password required"}), 400
                
                if not email:
                    return jsonify({"success": False, "message": "Email is required"}), 400
                
                if not validate_email(email):
                    return jsonify({"success": False, "message": "Invalid email format"}), 400
                
                users = load_users()
                
                if username in users:
                    return jsonify({"success": False, "message": "Username already exists"}), 409
                
                # Check if email already exists
                for user_data in users.values():
                    if user_data.get('email') == email:
                        return jsonify({"success": False, "message": "Email already registered"}), 409
                
                # Generate verification token
                token = secrets.token_urlsafe(32)
                VERIFICATION_TOKENS[token] = {
                    'username': username,
                    'email': email,
                    'password': password,
                    'timestamp': os.path.getmtime(USERS_FILE) if os.path.exists(USERS_FILE) else 0
                }
                
                # Send verification email
                send_verification_email(email, token)
                
                # Create user with verified status (auto-verify in dev mode)
                users[username] = {
                    'password': generate_password_hash(password),
                    'email': email,
                    'verified': True,  # Auto-verify in dev mode
                    'answers': [],
                    'results': []
                }
                
                if not save_users(users):
                    return jsonify({"success": False, "message": "Error saving user data"}), 500
                    
                return jsonify({
                    "success": True, 
                    "message": "Account created! Please check your email to verify your account.",
                    "verification_sent": True
                })
        except Exception as e:
            print(f"Signup error: {e}")
            return jsonify({"success": False, "message": "Server error"}), 500
    
    # Pass Firebase config to template
    return render_template("index.html", logged_in=False, is_signup=True, firebase_config=FIREBASE_CONFIG)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "Invalid request"}), 400
                
            email = data.get('email', '').strip().lower()
            
            if not email:
                return jsonify({"success": False, "message": "Email is required"}), 400
            
            if not validate_email(email):
                return jsonify({"success": False, "message": "Invalid email format"}), 400
            
            users = load_users()
            
            # Find user by email
            user_found = None
            for username, user_data in users.items():
                if user_data.get('email') == email:
                    user_found = username
                    break
            
            if not user_found:
                # Don't reveal that email doesn't exist (security best practice)
                return jsonify({
                    "success": True, 
                    "message": "If that email exists, a reset link has been sent."
                })
            
            # Generate reset token
            token = secrets.token_urlsafe(32)
            VERIFICATION_TOKENS[token] = {
                'username': user_found,
                'email': email,
                'type': 'password_reset',
                'timestamp': os.path.getmtime(USERS_FILE) if os.path.exists(USERS_FILE) else 0
            }
            
            # Send reset email
            send_password_reset_email(email, token)
            
            return jsonify({
                "success": True, 
                "message": "Password reset link sent to your email. Please check your inbox."
            })
        except Exception as e:
            print(f"Password reset error: {e}")
            return jsonify({"success": False, "message": "Server error"}), 500
    
    return render_template("index.html", logged_in=False, is_signup=False, is_forgot_password=True)

@app.route("/reset-password")
def reset_password_page():
    """Handle password reset via token - show form to enter new password"""
    token = request.args.get('token')
    if not token or token not in VERIFICATION_TOKENS:
        return render_template("index.html", logged_in=False, is_signup=False, 
                             reset_error="Invalid or expired reset token"), 400
    
    token_data = VERIFICATION_TOKENS[token]
    if token_data.get('type') != 'password_reset':
        return render_template("index.html", logged_in=False, is_signup=False, 
                             reset_error="Invalid token type"), 400
    
    # Store token in session temporarily for password reset form
    session['reset_token'] = token
    return render_template("index.html", logged_in=False, is_signup=False, 
                         show_reset_form=True, reset_token=token)

@app.route("/reset-password-submit", methods=["POST"])
def reset_password_submit():
    """Handle password reset submission"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password', '')
        
        if not token or token not in VERIFICATION_TOKENS:
            return jsonify({"success": False, "message": "Invalid or expired token"}), 400
        
        if not new_password:
            return jsonify({"success": False, "message": "Password is required"}), 400
        
        token_data = VERIFICATION_TOKENS[token]
        if token_data.get('type') != 'password_reset':
            return jsonify({"success": False, "message": "Invalid token type"}), 400
        
        # Reset password
        users = load_users()
        username = token_data['username']
        if username in users:
            users[username]['password'] = generate_password_hash(new_password)
            save_users(users)
            del VERIFICATION_TOKENS[token]
            session.pop('reset_token', None)
            return jsonify({"success": True, "message": "Password reset successfully"})
        
        return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        print(f"Password reset submit error: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500

@app.route("/verify-email")
def verify_email():
    """Handle email verification"""
    token = request.args.get('token')
    if not token or token not in VERIFICATION_TOKENS:
        return render_template("index.html", logged_in=False, is_signup=False, 
                             verify_error="Invalid or expired verification token"), 400
    
    token_data = VERIFICATION_TOKENS[token]
    users = load_users()
    username = token_data['username']
    
    if username in users:
        users[username]['verified'] = True
        save_users(users)
        del VERIFICATION_TOKENS[token]
        return render_template("index.html", logged_in=False, is_signup=False, 
                             verify_success=True)
    
    return render_template("index.html", logged_in=False, is_signup=False, 
                         verify_error="User not found"), 404

@app.route("/logout")
def logout():
    # Clear both Firebase and legacy session data
    session.pop('user_id', None)
    session.pop('email', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/submit_assessment", methods=["POST"])
def submit_assessment():
    user_id = session.get('user_id')
    username = session.get('username')
    
    if not user_id and not username:
        return jsonify({"success": False, "message": "Not logged in"})
    
    data = request.json
    answers = data.get('answers', [])
    
    if len(answers) != len(QUESTIONS):
        return jsonify({"success": False, "message": "Please answer all questions!"})
    
    # Calculate results
    results = calculate_results(answers)
    
    # Save to appropriate storage
    if user_id:
        # Firebase user - save to Firestore
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'answers': answers,
            'results': results,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return jsonify({"success": True, "results": results})
    else:
        # Legacy user - save to JSON
        users = load_users()
        if username in users:
            users[username]['answers'] = answers
            users[username]['results'] = results
            save_users(users)
            return jsonify({"success": True, "results": results})
    
    return jsonify({"success": False, "message": "User not found"})

@app.route("/reset_assessment", methods=["POST"])
def reset_assessment():
    user_id = session.get('user_id')
    username = session.get('username')
    
    if not user_id and not username:
        return jsonify({"success": False, "message": "Not logged in"})
    
    # Reset in appropriate storage
    if user_id:
        # Firebase user - reset in Firestore
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'answers': [],
            'results': [],
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return jsonify({"success": True})
    else:
        # Legacy user - reset in JSON
        users = load_users()
        if username in users:
            users[username]['answers'] = []
            users[username]['results'] = []
            save_users(users)
            return jsonify({"success": True})
    
    return jsonify({"success": False, "message": "User not found"})

@app.route("/chat", methods=["POST"])
def chat():
    """
    RAG-enhanced chat endpoint for spiritual guidance
    Uses retrieval-augmented generation with religion-specific context
    """
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not logged in"})
    
    if not client:
        return jsonify({"success": False, "message": "Chat service not configured. Please set TOGETHER_API_KEY."})
    
    data = request.json
    user_message = data.get('message', '').strip()
    religion_name = data.get('religion', '')
    chat_history = data.get('history', [])
    
    if not user_message or not religion_name:
        return jsonify({"success": False, "message": "Message and religion required"})
    
    # Find religion in CSV data first, fallback to basic RELIGIONS
    religion_data = None
    religion_key = None
    
    for key, value in RELIGIONS.items():
        if value['name'] == religion_name:
            religion_key = key
            # Use CSV data if available
            if key in RELIGIONS_CSV:
                religion_data = RELIGIONS_CSV[key]
            else:
                religion_data = value
            break
    
    if not religion_data:
        return jsonify({"success": False, "message": "Religion not found"})
    
    # Build RAG context using rag_utils
    if religion_key in RELIGIONS_CSV:
        # Rich context from CSV using RAG utilities
        csv_data = RELIGIONS_CSV[religion_key]
        context_chunks = prepare_religion_rag_context(csv_data)
        context = f"""REFERENCE DATA FOR {csv_data['name']}:

{context_chunks[0]}"""
    else:
        # Fallback to basic data
        basic_context = prepare_religion_rag_context(religion_data)
        context = f"""REFERENCE DATA FOR {religion_data['name']}:

{basic_context[0]}"""
    
    system_prompt = f"""You're a knowledgeable spiritual guide. Use the reference data below to answer questions.

{context}

INSTRUCTIONS:
- Keep responses concise, minimal. 30-60 words, depending on the context
- ALWAYS complete your sentences - never cut off mid-sentence
- Be respectful and accurate
- If unsure, say so
- Use * for bullet points if listing
- End responses with complete thoughts, not incomplete phrases
- If you need to cut information, end with "..." but complete the current sentence"""

    # Build conversation
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add recent chat history
    for msg in chat_history[-4:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct-Lite",
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )
        
        bot_response = response.choices[0].message.content
        
        return jsonify({
            "success": True,
            "response": bot_response
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Chat error: {str(e)}"
        })

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Convert audio to text using Whisper"""
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not logged in"})
    
    if not openai_client:
        return jsonify({"success": False, "message": "Whisper not configured"})
    
    audio_file = request.files.get('audio')
    if not audio_file:
        return jsonify({"success": False, "message": "No audio file"})
    
    try:
        # Convert FileStorage to bytes
        audio_bytes = audio_file.read()
        
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=("recording.webm", audio_bytes, "audio/webm")
        )
        return jsonify({"success": True, "text": transcript.text})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/debug")
def debug():
    """
    Debug endpoint to check API configuration and environment
    """
    return jsonify({
        "api_key_set": bool(TOGETHER_API_KEY),
        "client_available": client is not None,
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "together_api_key_length": len(TOGETHER_API_KEY) if TOGETHER_API_KEY else 0,
        "flask_debug": app.debug,
        "users_file": USERS_FILE
    })

@app.route("/session-debug")
def session_debug():
    """
    Debug endpoint to check session and user data
    """
    users = load_users()
    return jsonify({
        "session_data": dict(session),
        "username_in_session": 'username' in session,
        "current_username": session.get('username', 'None'),
        "users_file_exists": os.path.exists(USERS_FILE),
        "users_file_path": os.path.abspath(USERS_FILE),
        "users_count": len(users),
        "user_list": list(users.keys()),
        "session_cookie_config": {
            "secure": app.config.get('SESSION_COOKIE_SECURE'),
            "httponly": app.config.get('SESSION_COOKIE_HTTPONLY'),
            "samesite": app.config.get('SESSION_COOKIE_SAMESITE')
        }
    })

# Initialize default test user on startup
initialize_default_user()

if __name__ == "__main__":
    app.run(debug=True, port=5003)