"""
Concept: Flask + HTML Integration - Spiritual Path Assessment Tool
This app helps users discover which religious or spiritual path aligns with their 
beliefs, values, lifestyle, and background through an interactive questionnaire.
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import warnings
from dotenv import load_dotenv
import together

warnings.filterwarnings("ignore")
load_dotenv()

app = Flask(__name__)
app.secret_key = 'spiritual-journey-finder-2024'

# File to store user data
USERS_FILE = 'users_data.json'

# Together API for chatbot
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
together.api_key = TOGETHER_API_KEY
client = together if TOGETHER_API_KEY else None

# Assessment Questions
QUESTIONS = [
    {
        "id": 1,
        "question": "What is your view on the existence of God or a higher power?",
        "options": {
            "One supreme God": {"Christianity": 3, "Islam": 3, "Judaism": 3, "Sikhism": 3},
            "Multiple gods": {"Hinduism": 3, "Ancient Greek": 3, "Norse": 3},
            "Spiritual force/energy": {"Buddhism": 2, "Taoism": 3, "New Age": 3},
            "Uncertain/Agnostic": {"Secular Humanism": 3, "Buddhism": 1},
            "No God (Atheist)": {"Secular Humanism": 3}
        }
    },
    {
        "id": 2,
        "question": "How do you prefer to connect with the divine or spiritual realm?",
        "options": {
            "Organized worship services": {"Christianity": 3, "Islam": 3, "Judaism": 3},
            "Personal meditation": {"Buddhism": 3, "Hinduism": 2, "New Age": 2},
            "Nature and environment": {"Taoism": 3, "Wicca": 3, "Indigenous": 3},
            "Study and reflection": {"Judaism": 2, "Secular Humanism": 3},
            "No spiritual practice": {"Secular Humanism": 3}
        }
    },
    {
        "id": 3,
        "question": "What role should religious texts play in your life?",
        "options": {
            "Central authority": {"Islam": 3, "Christianity": 3, "Judaism": 3},
            "Guidance but not absolute": {"Hinduism": 2, "Buddhism": 2, "Sikhism": 2},
            "Philosophical insights": {"Taoism": 2, "Buddhism": 2, "Confucianism": 3},
            "Not important": {"Secular Humanism": 3, "New Age": 1}
        }
    },
    {
        "id": 4,
        "question": "What happens after death?",
        "options": {
            "Heaven or Hell": {"Christianity": 3, "Islam": 3},
            "Reincarnation": {"Hinduism": 3, "Buddhism": 3, "Sikhism": 2},
            "Merge with the universe": {"Taoism": 3, "New Age": 2},
            "Nothing/End of consciousness": {"Secular Humanism": 3},
            "Unknown": {"Secular Humanism": 1, "Buddhism": 1}
        }
    },
    {
        "id": 5,
        "question": "How important is community in your spiritual life?",
        "options": {
            "Very important": {"Christianity": 3, "Islam": 3, "Judaism": 3, "Sikhism": 3},
            "Somewhat important": {"Hinduism": 2, "Buddhism": 2, "Wicca": 2},
            "Not very important": {"Taoism": 2, "New Age": 2},
            "Prefer solitary practice": {"Buddhism": 1, "New Age": 2}
        }
    },
    {
        "id": 6,
        "question": "What is the purpose of life?",
        "options": {
            "Serve God": {"Christianity": 3, "Islam": 3, "Judaism": 3},
            "Achieve enlightenment": {"Buddhism": 3, "Hinduism": 3},
            "Live in harmony": {"Taoism": 3, "Confucianism": 3, "Indigenous": 3},
            "Help humanity": {"Secular Humanism": 3, "Sikhism": 2},
            "Personal fulfillment": {"New Age": 3, "Secular Humanism": 2}
        }
    },
    {
        "id": 7,
        "question": "How do you view suffering?",
        "options": {
            "Test from God": {"Christianity": 3, "Islam": 3, "Judaism": 2},
            "Result of attachment": {"Buddhism": 3},
            "Natural part of life": {"Taoism": 3, "Stoicism": 3, "Secular Humanism": 2},
            "Karma from past actions": {"Hinduism": 3, "Buddhism": 2, "Sikhism": 2}
        }
    },
    {
        "id": 8,
        "question": "What is your stance on ritual and ceremony?",
        "options": {
            "Essential": {"Hinduism": 3, "Judaism": 3, "Wicca": 3},
            "Important but flexible": {"Christianity": 2, "Islam": 2, "Buddhism": 2},
            "Optional": {"New Age": 2, "Taoism": 2},
            "Unnecessary": {"Secular Humanism": 3}
        }
    }
]

# Religion Descriptions
RELIGIONS = {
    "Christianity": {
        "name": "Christianity",
        "description": "Based on the life and teachings of Jesus Christ, emphasizing love, forgiveness, and salvation through faith.",
        "core_beliefs": "Trinity (Father, Son, Holy Spirit), Salvation through Jesus, Bible as sacred text",
        "practices": "Church attendance, prayer, sacraments, Bible study",
        "resources": ["Bible", "Local churches", "Christian counseling", "Bible.com"]
    },
    "Islam": {
        "name": "Islam",
        "description": "Monotheistic faith revealed to Prophet Muhammad, emphasizing submission to Allah's will.",
        "core_beliefs": "Five Pillars, Quran as final revelation, Prophet Muhammad, One God (Allah)",
        "practices": "Five daily prayers, fasting during Ramadan, charity, pilgrimage to Mecca",
        "resources": ["Quran", "Local mosques", "Islamic centers", "Quran.com"]
    },
    "Buddhism": {
        "name": "Buddhism",
        "description": "Path to enlightenment through understanding the nature of suffering and following the Eightfold Path.",
        "core_beliefs": "Four Noble Truths, Eightfold Path, Karma, Reincarnation, No eternal soul",
        "practices": "Meditation, mindfulness, following precepts, studying dharma",
        "resources": ["Buddhist temples", "Meditation centers", "AccessToInsight.org"]
    },
    "Hinduism": {
        "name": "Hinduism",
        "description": "Ancient tradition with diverse beliefs, emphasizing dharma, karma, and moksha (liberation).",
        "core_beliefs": "Brahman (ultimate reality), Karma, Reincarnation, Multiple paths to divine",
        "practices": "Puja (worship), yoga, meditation, festivals, pilgrimages",
        "resources": ["Bhagavad Gita", "Hindu temples", "Yoga centers"]
    },
    "Judaism": {
        "name": "Judaism",
        "description": "Covenant relationship between God and the Jewish people, emphasizing Torah study and ethical living.",
        "core_beliefs": "One God, Chosen people, Torah, Messiah to come, Ethical monotheism",
        "practices": "Sabbath observance, kashrut (dietary laws), prayer, Torah study",
        "resources": ["Torah", "Synagogues", "Jewish community centers"]
    },
    "Sikhism": {
        "name": "Sikhism",
        "description": "Monotheistic faith founded by Guru Nanak, emphasizing equality, service, and devotion to one God.",
        "core_beliefs": "One God, Equality of all people, Karma and reincarnation, Guru Granth Sahib",
        "practices": "Prayer, meditation on God's name, service (seva), honest living",
        "resources": ["Guru Granth Sahib", "Gurdwaras", "Sikh community organizations"]
    },
    "Taoism": {
        "name": "Taoism",
        "description": "Chinese philosophy emphasizing living in harmony with the Tao (the Way), natural flow of the universe.",
        "core_beliefs": "The Tao, Wu wei (effortless action), Yin and yang, Natural harmony",
        "practices": "Meditation, Tai Chi, Qigong, simplicity, nature connection",
        "resources": ["Tao Te Ching", "Taoist temples", "Tai Chi classes"]
    },
    "Secular Humanism": {
        "name": "Secular Humanism",
        "description": "Non-religious philosophy emphasizing reason, ethics, human welfare without supernatural beliefs.",
        "core_beliefs": "Human reason, Scientific method, Ethical living without religion, Human dignity",
        "practices": "Critical thinking, ethical action, community service, rational inquiry",
        "resources": ["Humanist organizations", "Secular communities", "Philosophy books"]
    },
    "New Age": {
        "name": "New Age Spirituality",
        "description": "Modern spiritual movement combining various traditions, emphasizing personal growth and consciousness.",
        "core_beliefs": "Universal energy, Personal transformation, Interconnectedness, Alternative healing",
        "practices": "Meditation, crystal healing, astrology, energy work, holistic wellness",
        "resources": ["Spiritual centers", "Wellness workshops", "Metaphysical bookstores"]
    },
    "Wicca": {
        "name": "Wicca",
        "description": "Modern pagan religion honoring nature, practicing ritual magic, and worshipping the Goddess and God.",
        "core_beliefs": "Nature reverence, Magic, Goddess and God, Harm none, Wheel of the Year",
        "practices": "Seasonal rituals, spell work, moon celebrations, nature worship",
        "resources": ["Wiccan covens", "Pagan gatherings", "Nature-based spirituality books"]
    }
}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def calculate_results(answers):
    scores = {}
    for answer in answers:
        question = next((q for q in QUESTIONS if q["id"] == answer["question_id"]), None)
        if question and answer["answer"] in question["options"]:
            points = question["options"][answer["answer"]]
            for religion, score in points.items():
                scores[religion] = scores.get(religion, 0) + score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    recommendations = []
    for religion_key, score in sorted_scores[:3]:
        if religion_key in RELIGIONS:
            religion_info = RELIGIONS[religion_key].copy()
            religion_info["score"] = score
            religion_info["percentage"] = round((score / (len(answers) * 3)) * 100)
            recommendations.append(religion_info)
    return recommendations

# Routes
@app.route("/")
def index():
    # Check if user is logged in
    if 'username' in session:
        users = load_users()
        user_data = users.get(session['username'], {})
        has_results = len(user_data.get('recommendations', [])) > 0
        
        return render_template("index.html",
            logged_in=True,
            username=session['username'],
            title="🌟 Your Spiritual Journey" if has_results else "🌟 Spiritual Path Assessment",
            message="Explore your personalized results" if has_results else "Discover your path",
            has_results=has_results,
            questions=QUESTIONS,
            results=user_data.get('recommendations', [])
        )
    
    # Not logged in - show login page
    return render_template("index.html",
        logged_in=False,
        is_signup=False
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password required"})
        
        users = load_users()
        if username in users and users[username].get('password') == password:
            session['username'] = username
            return jsonify({"success": True, "message": "Login successful"})
        
        return jsonify({"success": False, "message": "Invalid credentials"})
    
    # GET request - show login page
    return render_template("index.html",
        logged_in=False,
        is_signup=False
    )

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"success": False, "message": "All fields required"})
        
        users = load_users()
        if username in users:
            return jsonify({"success": False, "message": "Username already exists"})
        
        users[username] = {
            "password": password,
            "answers": [],
            "recommendations": []
        }
        save_users(users)
        session['username'] = username
        return jsonify({"success": True, "message": "Account created successfully"})
    
    # GET request - show signup page
    return render_template("index.html",
        logged_in=False,
        is_signup=True
    )

@app.route("/submit_assessment", methods=["POST"])
def submit_assessment():
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not logged in"})
    
    data = request.json
    answers = data.get('answers', [])
    
    if not answers:
        return jsonify({"success": False, "message": "No answers provided"})
    
    users = load_users()
    username = session['username']
    
    if username in users:
        users[username]['answers'] = answers
        recommendations = calculate_results(answers)
        users[username]['recommendations'] = recommendations
        save_users(users)
        return jsonify({"success": True, "recommendations": recommendations})
    
    return jsonify({"success": False, "message": "User not found"})

@app.route("/reset_assessment", methods=["POST"])
def reset_assessment():
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not logged in"})
    
    users = load_users()
    username = session['username']
    
    if username in users:
        users[username]['answers'] = []
        users[username]['recommendations'] = []
        save_users(users)
        return jsonify({"success": True})
    
    return jsonify({"success": False, "message": "User not found"})

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

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

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-5:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = together.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct-Lite",
            messages=messages,
            max_tokens=80,
            temperature=0.7,
        )

        bot_response = response.output[0].content[0].text
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
    app.run(debug=True, host="0.0.0.0", port=7860)