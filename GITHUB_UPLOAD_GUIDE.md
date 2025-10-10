# GitHub Upload Guide

## ✅ What to Upload to GitHub (Public Repository)

Upload these files:

```
✓ app.py                  # Your Flask application (now with password hashing!)
✓ requirements.txt        # Python dependencies
✓ README.md              # Project documentation
✓ .gitignore             # Tells Git what NOT to upload
✓ templates/             # HTML templates folder
  └── index.html
✓ static/                # CSS & JavaScript folder
  ├── style.css
  └── script.js
```

## ❌ What NOT to Upload (Automatically Ignored by .gitignore)

**NEVER upload these files:**

```
✗ users_data.json        # Contains usernames & hashed passwords
✗ .env                   # Contains your API keys (TOGETHER_API_KEY)
✗ .venv/                 # Python virtual environment
✗ __pycache__/           # Python cache files
✗ .DS_Store              # macOS system files
✗ *.log                  # Log files
```

## 🔒 Security Features Added

### Password Hashing
Your app now uses **werkzeug.security** to hash passwords:

- **New users**: Passwords are hashed automatically on signup
- **Existing users**: Passwords auto-upgrade to hashed on next login
- **Hash method**: PBKDF2-SHA256 (industry standard)

Example of hashed password in users_data.json:
```json
"password": "pbkdf2:sha256:600000$abc123$..."
```

## 📝 Setup Instructions for GitHub

### Step 1: Initialize Git (if not already done)
```bash
cd /Users/yoon/Documents/GitHub/Spiritual-Path-Assessment
git init
```

### Step 2: Add All Safe Files
```bash
git add .
```

The `.gitignore` file will automatically prevent sensitive files from being added.

### Step 3: Commit
```bash
git commit -m "Initial commit: Spiritual Path Assessment with secure password hashing"
```

### Step 4: Push to GitHub
```bash
# Create a new repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/Spiritual-Path-Assessment.git
git branch -M main
git push -u origin main
```

## 🌐 For Others to Use Your App

When someone clones your repository, they need to:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create .env file** (if they want the chatbot feature):
   ```bash
   # Create .env file
   echo "TOGETHER_API_KEY=their_api_key_here" > .env
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. **Access at:** http://localhost:5001

## 📋 Repository Description

When creating your GitHub repository, use this description:

```
Spiritual Path Assessment Tool - An interactive web app to help users discover 
which spiritual or religious path aligns with their beliefs. Built with Flask, 
featuring AI-powered chatbot, secure password hashing, and beautiful UI.
```

### Suggested Tags:
`flask` `python` `spiritual` `assessment` `chatbot` `together-ai` `web-app`

## ⚠️ Important Notes

1. **API Key**: The app works without an API key, but the chatbot feature requires a Together AI API key
2. **User Data**: Each installation starts fresh (no shared user database)
3. **Development Mode**: The app runs in debug mode by default (change for production)
4. **Secret Key**: Consider changing `app.secret_key` in app.py for production

## 🔐 Password Security Details

**Before:**
- Passwords stored in plaintext
- Example: `"password": "12341234"`

**After:**
- Passwords hashed with PBKDF2-SHA256
- Example: `"password": "pbkdf2:sha256:600000$salt$hash"`
- 600,000 iterations (very secure)
- Backward compatible (auto-upgrades old passwords)

---

**Ready to upload!** Just follow the steps above. 🚀

