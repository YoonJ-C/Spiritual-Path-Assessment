---
title: Spiritual Path Assessment
emoji: ✨
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
hf_oauth: true
hf_oauth_scopes:
  - read-repos
---

## 🌟 Spiritual Path Finder with AI Chatbot

An interactive web application that helps users discover which religious or spiritual path aligns with their beliefs, values, and lifestyle through an 8-question assessment. Features real-time AI chatbot assistance for each recommended path.

### ✨ Features:
- **Interactive Assessment**: 8 thoughtful questions about worldview and beliefs
- **Smart Recommendations**: Top 3 spiritual paths with match percentages
- **AI Chatbot Integration**: Ask questions about each spiritual path in real-time
- **User Authentication**: Personal accounts with saved results
- **Beautiful UI**: Modern, responsive design with smooth animations
- **Navigation Controls**: Back/Next buttons to review and change answers

### 🚀 How to Setup & Run:

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Configure API Key
- Copy `env_example.txt` to `.env`
- Get your Together API key from: https://api.together.xyz/
- Add your API key to `.env`:
```
TOGETHER_API_KEY=your_actual_key_here
```

#### 3. Run the Application
```bash
python app.py
```

#### 4. Open in Browser
Navigate to: `http://localhost:5001`

### 🎯 How to Use:
1. **Sign Up/Login**: Create an account or sign in
2. **Take Assessment**: Answer 8 questions about your beliefs
3. **View Results**: See your top 3 spiritual path matches
4. **Chat with AI**: Click "💬 Ask Questions" on any result to chat
5. **Learn More**: Ask the AI chatbot anything about the spiritual paths

### 💬 Chatbot Features:
- **Context-Aware**: Each chatbot is specialized in its specific religion/path
- **Real-Time Responses**: Powered by Together AI (Llama-3 model)
- **Conversation History**: Maintains context within each chat
- **Multiple Chats**: Separate conversation for each result card

### 🗂️ Spiritual Paths Included:
- Christianity, Islam, Judaism, Buddhism, Hinduism
- Sikhism, Taoism, Paganism, Indigenous Spirituality
- Secular Humanism, Atheism, Agnosticism
- New Age Spirituality, Spiritual But Not Religious

### 🔧 Technical Stack:
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI Integration**: Together API (Llama-3)
- **Authentication**: Session-based
- **Data Storage**: JSON files

### 📁 Key Files:
- `app.py` - Main Flask application with routes and chatbot logic
- `templates/index.html` - Frontend UI with assessment and chat interface
- `users_data.json` - User accounts and assessment results
- `.env` - API keys configuration (create from env_example.txt)

### 🎨 Example Questions:
Ask the chatbot things like:
- "What are the daily practices?"
- "How do I get started with this path?"
- "What are the main texts or teachings?"
- "Is this compatible with my current lifestyle?"
- "What's the community like?"

### 💡 TIP: 
The chatbot uses AI to provide informative, respectful, and objective information about each spiritual path. It's designed to help you explore and learn, not to convert or convince.
