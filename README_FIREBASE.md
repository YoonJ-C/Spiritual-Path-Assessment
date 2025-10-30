# Spiritual Path Assessment Tool

A Flask-based web application that helps users discover which religious or spiritual path aligns with their beliefs, values, and lifestyle through an interactive questionnaire.

## Features

- 🔐 **Firebase Authentication**
  - Email/Password authentication
  - Google Sign-In
  - Email verification
  - Password reset
  
- 📊 **Assessment System**
  - 8-question spiritual path questionnaire
  - Personalized recommendations based on responses
  - Detailed information about each spiritual path
  
- 💬 **AI-Powered Chatbot**
  - Ask questions about recommended spiritual paths
  - RAG-enhanced responses using religion-specific data
  - Voice input support with Whisper transcription
  
- 🗄️ **Firestore Database**
  - Secure user data storage
  - Assessment answers and results persistence
  - Real-time synchronization

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Firebase Authentication
- **Database**: Cloud Firestore
- **AI/ML**: 
  - Together AI (chatbot)
  - OpenAI Whisper (voice transcription)
- **Deployment**: Render.com / Docker

## Quick Start

### Prerequisites

- Python 3.9+
- Firebase project (see [FIREBASE_SETUP.md](FIREBASE_SETUP.md))
- API keys for Together AI and OpenAI (optional, for chatbot features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YoonJ-C/Spiritual-Path-Assessment.git
   cd Spiritual-Path-Assessment
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Firebase** (detailed guide in [FIREBASE_SETUP.md](FIREBASE_SETUP.md))
   - Create a Firebase project
   - Enable Authentication (Email/Password and Google)
   - Create Firestore database
   - Download service account key as `serviceAccountKey.json`

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Firebase credentials and API keys
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   ```
   http://localhost:5003
   ```

## Environment Variables

See `.env.example` for all required environment variables. Key variables:

- `FIREBASE_CREDENTIALS_PATH`: Path to service account JSON file
- `FIREBASE_WEB_API_KEY`: Firebase web API key
- `FIREBASE_PROJECT_ID`: Your Firebase project ID
- `TOGETHER_API_KEY`: Together AI API key (for chatbot)
- `OPENAI_API_KEY`: OpenAI API key (for voice input)

## Deployment

### Render.com

1. Push your code to GitHub
2. Create a new Web Service on Render.com
3. Connect your GitHub repository
4. Add environment variables in Render dashboard
5. Upload `serviceAccountKey.json` as a secret file
6. Deploy!

See [FIREBASE_SETUP.md](FIREBASE_SETUP.md) for detailed deployment instructions.

### Docker

```bash
docker build -t spiritual-path-assessment .
docker run -p 5003:5003 --env-file .env spiritual-path-assessment
```

## Project Structure

```
Spiritual-Path-Assessment/
├── app.py                  # Main Flask application
├── rag_utils.py           # RAG utilities for chatbot
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── FIREBASE_SETUP.md     # Firebase setup guide
├── .env.example          # Environment variables template
├── religions.csv         # Religion data for RAG
├── static/
│   ├── style.css         # Main styles
│   ├── landing.css       # Landing page styles
│   ├── script.js         # Frontend JavaScript
│   ├── design-tokens.css # Design system tokens
│   └── images/           # Image assets
└── templates/
    ├── landing.html      # Landing page
    └── index.html        # Main app template
```

## Features in Detail

### Authentication

- **Firebase Authentication** provides secure user management
- **Google Sign-In** for quick access
- **Email verification** ensures valid user accounts
- **Password reset** via email
- **Legacy support** for existing username/password users

### Assessment

- 8 carefully crafted questions covering:
  - Views on divinity
  - Spiritual practices
  - Afterlife beliefs
  - Moral guidance
  - Ritual importance
  - Nature relationship
  - Suffering perspective
  - Community role

- Results show top 3 spiritual paths with:
  - Alignment percentage
  - Description
  - Common practices
  - Core beliefs

### Chatbot

- Ask questions about recommended spiritual paths
- Powered by Meta-Llama-3-8B-Instruct-Lite
- RAG-enhanced with detailed religion data
- Voice input with live transcription
- Conversation history maintained per religion

## Security

- Firebase handles authentication securely
- Firestore security rules restrict data access
- Service account keys kept secure
- HTTPS enforced in production
- Session management with secure cookies

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

Apache 2.0 License - see LICENSE file for details

## Support

For issues or questions:
- Open an issue on GitHub
- Check [FIREBASE_SETUP.md](FIREBASE_SETUP.md) for setup help
- Review Firebase documentation

## Acknowledgments

- Firebase for authentication and database
- Together AI for chatbot capabilities
- OpenAI for Whisper transcription
- All contributors and users

---

Made with ❤️ for spiritual seekers everywhere

