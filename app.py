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
import together  # Updated import

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
    # ... keep all your questions exactly as before ...
]

# Religion Descriptions
RELIGIONS = {
    # ... keep all your religions exactly as before ...
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

# --- Flask routes (login, signup, home, logout, assessment routes) ---
# Keep all your existing routes unchanged

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

        bot_response = response.output[0].content[0].text  # ✅ Correctly indented
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
