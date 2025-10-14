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
from dotenv import load_dotenv
from together import Together

load_dotenv()

app = Flask(__name__)
app.secret_key = 'spiritual-journey-finder-2024'

# File to store user data
USERS_FILE = os.getenv("USERS_FILE", "/data/users_data.json")

# Together API for chatbot
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=TOGETHER_API_KEY) if TOGETHER_API_KEY else None

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

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

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
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    users = load_users()
    user_data = users.get(session['username'], {})
    has_results = 'results' in user_data and user_data['results']
    
    return render_template(
        "index.html", 
        title="Spiritual Path Finder", 
        message=f"Welcome, {session['username']}! 🌟",
        username=session['username'],
        logged_in=True,
        questions=QUESTIONS,
        has_results=has_results,
        results=user_data.get('results', []) if has_results else []
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # --- replace your /login POST logic with this ---
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        users = load_users()
        if username in users:
            stored = users[username]['password']
        
            # 1) Try hash-based verification (works for any Werkzeug scheme)
            try:
                if check_password_hash(stored, password):
                    session['username'] = username
                    return jsonify({"success": True})
            except Exception:
                pass  # if stored isn't a hash string, we'll try plaintext next
        
            # 2) Legacy plaintext fallback → upgrade to a hash
            if stored == password:
                users[username]['password'] = generate_password_hash(password)
                save_users(users)
                session['username'] = username
                return jsonify({"success": True})
        
        return jsonify({"success": False, "message": "Invalid credentials!"})
    
    return render_template("index.html", logged_in=False, is_signup=False)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        users = load_users()
        
        if username in users:
            return jsonify({"success": False, "message": "Username already exists!"})
        
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password required!"})
        
        # Create new user with hashed password
        users[username] = {
            'password': generate_password_hash(password),
            'answers': [],
            'results': []
        }
        save_users(users)
        session['username'] = username
        return jsonify({"success": True})
    
    return render_template("index.html", logged_in=False, is_signup=True)

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/submit_assessment", methods=["POST"])
def submit_assessment():
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not logged in"})
    
    data = request.json
    answers = data.get('answers', [])
    
    if len(answers) != len(QUESTIONS):
        return jsonify({"success": False, "message": "Please answer all questions!"})
    
    # Calculate results
    results = calculate_results(answers)
    
    # Save to user data
    users = load_users()
    if session['username'] in users:
        users[session['username']]['answers'] = answers
        users[session['username']]['results'] = results
        save_users(users)
        
        return jsonify({"success": True, "results": results})
    
    return jsonify({"success": False, "message": "User not found"})

@app.route("/reset_assessment", methods=["POST"])
def reset_assessment():
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not logged in"})
    
    users = load_users()
    if session['username'] in users:
        users[session['username']]['answers'] = []
        users[session['username']]['results'] = []
        save_users(users)
        return jsonify({"success": True})
    
    return jsonify({"success": False, "message": "User not found"})

@app.route("/chat", methods=["POST"])
def chat():
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
    
    # Find religion details
    religion_data = None
    for key, value in RELIGIONS.items():
        if value['name'] == religion_name:
            religion_data = value
            break
    
    if not religion_data:
        return jsonify({"success": False, "message": "Religion not found"})
    
    # Create context-aware system prompt
    system_prompt = f"""You're a spiritual guide for {religion_data['name']}.
Info: {religion_data['description']} | Practices: {religion_data['practices']} | Beliefs: {religion_data['core_beliefs']}
Rules: Keep 30-50 words, be respectful, use * for bullet points (format: "Text: * item * item"), answer directly."""

    # Build conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add chat history (last 5 messages for context)
    for msg in chat_history[-5:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Call Together API with limited tokens for concise responses
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct-Lite",
            messages=messages,
            max_tokens=80,  # Roughly 50-60 words maximum
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

if __name__ == "__main__":
    app.run(debug=True, port=5001)