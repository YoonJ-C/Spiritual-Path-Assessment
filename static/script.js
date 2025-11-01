// Helper function to sanitize religion names for IDs
function sanitizeReligionName(name) {
    return name.replace(/\s+/g, '-');
}

// ==================== FIREBASE AUTHENTICATION ====================

// Google Sign-In with Firebase
async function signInWithGoogle() {
    if (!window.firebaseEnabled || !window.firebaseAuth) {
        const resultDiv = document.getElementById('result');
        if (resultDiv) {
            resultDiv.innerHTML = '<p class="error-msg">⚠️ Firebase not configured</p>';
        }
        return;
    }
    
    const provider = new firebase.auth.GoogleAuthProvider();
    
    // Configure provider for better popup behavior
    provider.setCustomParameters({
        prompt: 'select_account'  // Always show account selection
    });
    
    try {
        // Show loading state
        const resultDiv = document.getElementById('result');
        if (resultDiv) {
            resultDiv.innerHTML = '<p style="color: #666;">Opening sign-in window...</p>';
        }
        
        const result = await window.firebaseAuth.signInWithPopup(provider);
        const user = result.user;
        
        if (resultDiv) {
            resultDiv.innerHTML = '<p style="color: #666;">Signing in...</p>';
        }
        
        // Get ID token to send to backend
        const idToken = await user.getIdToken();
        
        // Send to backend for session creation
        const endpoint = window.location.pathname === '/signup' ? '/signup' : '/login';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({idToken}),
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = '/assessment';
        } else {
            const resultDiv = document.getElementById('result');
            if (resultDiv) {
                resultDiv.innerHTML = `<p class="error-msg">${data.message || 'Authentication failed'}</p>`;
            }
        }
    } catch (error) {
        console.error('Google Sign-In Error:', error);
        console.error('Error code:', error.code);
        console.error('Error details:', error);
        
        const resultDiv = document.getElementById('result');
        let errorMsg = '';
        
        // Handle specific error cases
        if (error.code === 'auth/popup-closed-by-user') {
            errorMsg = '❌ Sign-in window was closed. Please try again and complete the sign-in process.';
        } else if (error.code === 'auth/popup-blocked') {
            errorMsg = '❌ Pop-up was blocked by your browser. Please allow pop-ups for this site and try again.';
        } else if (error.code === 'auth/cancelled-popup-request') {
            errorMsg = '❌ Another sign-in is in progress. Please wait a moment and try again.';
        } else if (error.code === 'auth/unauthorized-domain') {
            errorMsg = '❌ This domain is not authorized for Google Sign-In. Please contact the administrator.';
        } else if (error.code === 'auth/operation-not-allowed') {
            errorMsg = '❌ Google Sign-In is not enabled. Please contact the administrator.';
        } else if (error.code === 'auth/network-request-failed') {
            errorMsg = '❌ Network error. Please check your internet connection and try again.';
        } else {
            errorMsg = `❌ ${error.message || 'Google Sign-In failed. Please try again.'}`;
        }
        
        if (resultDiv) {
            resultDiv.innerHTML = `<p class="error-msg">${errorMsg}</p>`;
        }
    }
}

// Firebase Email/Password Authentication
async function authenticateWithFirebase(email, password, isSignup) {
    if (!window.firebaseEnabled || !window.firebaseAuth) {
        return null; // Fall back to legacy auth
    }
    
    try {
        let userCredential;
        
        if (isSignup) {
            // Create new user with Firebase
            userCredential = await window.firebaseAuth.createUserWithEmailAndPassword(email, password);
            
            // Send email verification
            await userCredential.user.sendEmailVerification();
        } else {
            // Sign in existing user
            userCredential = await window.firebaseAuth.signInWithEmailAndPassword(email, password);
            
            // Check if email is verified
            if (!userCredential.user.emailVerified) {
                document.getElementById('result').innerHTML = 
                    '<p class="error-msg">⚠️ Please verify your email first. Check your inbox.</p>';
                await window.firebaseAuth.signOut();
                return null;
            }
        }
        
        // Get ID token
        const idToken = await userCredential.user.getIdToken();
        return idToken;
        
    } catch (error) {
        console.error('Firebase Auth Error:', error);
        throw error;
    }
}

// ==================== AUTHENTICATION ====================

async function authenticate() {
    const email = document.getElementById('authEmail').value.trim();
    const username = document.getElementById('authUsername') ? document.getElementById('authUsername').value.trim() : '';
    const password = document.getElementById('authPassword').value;
    
    if (!email || !password) {
        document.getElementById('result').innerHTML = 
            '<p class="error-msg">⚠️ Please fill in all fields</p>';
        return;
    }
    
    const isSignup = window.location.pathname === '/signup';
    const endpoint = isSignup ? '/signup' : '/login';
    
    // Try Firebase authentication first if available
    if (window.firebaseEnabled) {
        try {
            const idToken = await authenticateWithFirebase(email, password, isSignup);
            
            if (!idToken) {
                return; // Error already displayed
            }
            
            // Send token to backend
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({idToken}),
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (isSignup) {
                    document.getElementById('result').innerHTML = 
                        '<p class="success-msg">✅ Account created! Please check your email to verify.</p>';
                } else {
                    window.location.href = '/assessment';
                }
            } else {
                document.getElementById('result').innerHTML = 
                    `<p class="error-msg">${data.message || 'Authentication failed'}</p>`;
            }
            return;
        } catch (error) {
            console.error('Firebase auth error:', error);
            document.getElementById('result').innerHTML = 
                `<p class="error-msg">${error.message || 'Authentication failed'}</p>`;
            return;
        }
    }
    
    // Legacy authentication fallback (if Firebase is disabled)
    const body = isSignup 
        ? {username, password, email} 
        : {username, password};
    
    fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            if (data.verification_sent) {
                document.getElementById('result').innerHTML = 
                    '<p class="success-msg">✅ ' + (data.message || 'Account created! Please check your email to verify.') + '</p>';
            } else {
                window.location.href = '/assessment';
            }
        } else {
            document.getElementById('result').innerHTML = 
                `<p class="error-msg">${data.message || 'Authentication failed'}</p>`;
        }
    })
    .catch(error => {
        document.getElementById('result').innerHTML = 
            `<p class="error-msg">${error.message || 'Network error. Please try again.'}</p>`;
    });
}

function switchAuth() {
    const newPath = window.location.pathname === '/signup' ? '/login' : '/signup';
    window.location.href = newPath;
}

function resetPassword() {
    const email = document.getElementById('resetEmail').value.trim();
    
    if (!email) {
        document.getElementById('result').innerHTML = 
            '<p class="error-msg">⚠️ Please enter your email</p>';
        return;
    }
    
    fetch('/forgot-password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email}),
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            document.getElementById('result').innerHTML = 
                '<p class="success-msg">✅ Password reset link sent! Check your email (or server console in dev mode).</p>';
        } else {
            document.getElementById('result').innerHTML = 
                `<p class="error-msg">${data.message || 'Failed to send reset link'}</p>`;
        }
    })
    .catch(error => {
        document.getElementById('result').innerHTML = 
            `<p class="error-msg">${error.message || 'Network error. Please try again.'}</p>`;
    });
}

function submitPasswordReset() {
    const token = document.getElementById('resetToken').value;
    const password = document.getElementById('resetPassword').value;
    
    if (!password) {
        document.getElementById('result').innerHTML = 
            '<p class="error-msg">⚠️ Please enter a new password</p>';
        return;
    }
    
    fetch('/reset-password-submit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token, password}),
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            document.getElementById('result').innerHTML = 
                '<p class="success-msg">✅ Password reset successfully! Redirecting to login...</p>';
            setTimeout(() => window.location.href = '/login', 1500);
        } else {
            document.getElementById('result').innerHTML = 
                `<p class="error-msg">${data.message || 'Failed to reset password'}</p>`;
        }
    })
    .catch(error => {
        document.getElementById('result').innerHTML = 
            `<p class="error-msg">${error.message || 'Network error. Please try again.'}</p>`;
    });
}

// ==================== ASSESSMENT ====================

var currentQuestion = 1;
var maxQuestionReached = 1;
var assessmentDataEl = document.getElementById('assessmentData');
var totalQuestions = assessmentDataEl ? parseInt(assessmentDataEl.getAttribute('data-total')) : 0;
var questionIds = assessmentDataEl ? JSON.parse(assessmentDataEl.getAttribute('data-ids')) : [];

// Show first question on load
window.addEventListener('DOMContentLoaded', function() {
    if (assessmentDataEl) {
        showQuestion(1);
    }
    
    // Add Enter key listener for password field if it exists
    const passwordField = document.getElementById('authPassword');
    if (passwordField) {
        passwordField.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') authenticate();
        });
    }
});

function showQuestion(questionIndex) {
    if (questionIndex > maxQuestionReached + 1) return;
    if (questionIndex > maxQuestionReached) maxQuestionReached = questionIndex;
    
    document.querySelectorAll('.question-block').forEach(function(block) {
        block.classList.remove('active');
        var blockIndex = parseInt(block.getAttribute('data-question-index'));
        if (blockIndex === questionIndex) block.classList.add('active');
    });
    
    currentQuestion = questionIndex;
    document.getElementById('questionCounter').textContent = 'Question ' + questionIndex + ' of ' + totalQuestions;
    document.getElementById('progressBar').style.width = ((questionIndex - 1) / (totalQuestions - 1)) * 100 + '%';
    updateNavigationButtons();
}

function updateNavigationButtons() {
    // Check if we're on the last question and it's answered
    var currentQuestionId = questionIds[currentQuestion - 1];
    var radioName = 'q' + currentQuestionId;
    var isAnswered = document.querySelector('input[name="' + radioName + '"]:checked') !== null;
    
    if (currentQuestion === totalQuestions && isAnswered) {
        document.getElementById('submitBtn').style.display = 'block';
    }
}

function handleAnswer(radioElement) {
    var questionIndex = parseInt(radioElement.getAttribute('data-question-index'));
    
    // Only process if this is the current question
    if (questionIndex !== currentQuestion) {
        return;
    }
    
    // Auto-advance to next question after selection
    setTimeout(function() {
        if (questionIndex < totalQuestions) {
            showQuestion(questionIndex + 1);
        } else {
            // Last question - show submit button
            document.getElementById('submitBtn').style.display = 'block';
        }
    }, 400);
}

function goToNext() {
    if (currentQuestion < totalQuestions) {
        showQuestion(currentQuestion + 1);
    }
}

function goToPrev() {
    if (currentQuestion > 1) {
        showQuestion(currentQuestion - 1);
    }
}

function submitAssessment() {
    var form = document.getElementById('assessmentForm');
    var answers = [];
    
    questionIds.forEach(function(qId) {
        var radioName = 'q' + qId;
        var selectedRadio = form.querySelector('input[name="' + radioName + '"]:checked');
        if (selectedRadio) {
            answers.push({
                question_id: qId,
                answer: selectedRadio.value
            });
        }
    });
    
    if (answers.length !== totalQuestions) {
        document.getElementById('errorMsg').innerHTML = 
            '<p class="error-msg">⚠️ Please answer all questions</p>';
        return;
    }
    
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('submitBtn').textContent = '✨ Calculating...';
    
    fetch('/submit_assessment', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({answers: answers})
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success) {
            window.location.reload();
        } else {
            document.getElementById('errorMsg').innerHTML = 
                '<p class="error-msg">' + data.message + '</p>';
            document.getElementById('submitBtn').disabled = false;
            document.getElementById('submitBtn').textContent = '✨ Discover Your Path';
        }
    });
}

function resetAssessment() {
    if (!confirm('Are you sure you want to retake the assessment? Your current results will be cleared.')) {
        return;
    }
    
    fetch('/reset_assessment', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success) {
            window.location.reload();
        }
    });
}

// ==================== SHARE RESULTS ====================

function shareResults() {
    const results = getResultsSummary();
    const text = `My Spiritual Path Results:\n\n${results}\n\nTake the assessment: ${window.location.origin}`;
    
    if (navigator.share) {
        navigator.share({ title: 'Spiritual Path Results', text: text });
    } else {
        navigator.clipboard.writeText(text);
        alert('Results copied to clipboard!');
    }
}

function getResultsSummary() {
    const cards = document.querySelectorAll('.result-card');
    return Array.from(cards).map((card, i) => {
        const title = card.querySelector('h3').textContent;
        const percentage = card.querySelector('.result-percentage').textContent;
        return `${i+1}. ${title} (${percentage})`;
    }).join('\n');
}


// ==================== CHAT FUNCTIONALITY ====================

var chatHistories = {};

function formatBotResponse(text) {
    var div = document.createElement('div');
    div.textContent = text;
    var escaped = div.innerHTML;
    
    // Check for bullet points
    if (escaped.match(/\*\s+/g) || escaped.match(/•\s+/g) || escaped.match(/^\s*-\s+/gm)) {
        var lines = escaped.split(/(?:\*|•|\n-)\s+/);
        if (lines.length > 1) {
            var formatted = lines[0].trim() ? lines[0].trim() + '<br><br>' : '';
            formatted += '<ul style="margin: 0; padding-left: 20px; line-height: 1.8;">';
            for (var i = 1; i < lines.length; i++) {
                if (lines[i].trim()) {
                    formatted += '<li style="margin-bottom: 6px;">' + lines[i].trim() + '</li>';
                }
            }
            return formatted + '</ul>';
        }
    }
    return escaped.replace(/\n/g, '<br>');
}

function toggleChat(religionName) {
    var chatId = 'chat-' + sanitizeReligionName(religionName);
    var chatWindow = document.getElementById(chatId);
    
    if (chatWindow.classList.contains('open')) {
        chatWindow.classList.remove('open');
    } else {
        chatWindow.classList.add('open');
        var inputId = 'input-' + sanitizeReligionName(religionName);
        setTimeout(function() {
            document.getElementById(inputId).focus();
        }, 300);
    }
}

function sendMessage(religionName) {
    var inputId = 'input-' + sanitizeReligionName(religionName);
    var messagesId = 'messages-' + sanitizeReligionName(religionName);
    var sendBtnId = 'send-' + sanitizeReligionName(religionName);
    
    var inputEl = document.getElementById(inputId);
    var messagesEl = document.getElementById(messagesId);
    var sendBtn = document.getElementById(sendBtnId);
    
    var message = inputEl.value.trim();
    if (!message) return;
    
    // Initialize chat history if not exists
    if (!chatHistories[religionName]) {
        chatHistories[religionName] = [];
    }
    
    // Add user message to UI
    var userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'chat-message user';
    userMsgDiv.textContent = message;
    messagesEl.appendChild(userMsgDiv);
    
    // Clear input and disable send button
    inputEl.value = '';
    sendBtn.disabled = true;
    
    // Show typing indicator
    var typingDiv = document.createElement('div');
    typingDiv.className = 'chat-typing';
    typingDiv.textContent = '💭 Thinking...';
    messagesEl.appendChild(typingDiv);
    
    // Scroll to bottom
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    // Add to chat history
    chatHistories[religionName].push({
        role: 'user',
        content: message
    });
    
    // Send to backend
    fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: message,
            religion: religionName,
            history: chatHistories[religionName]
        })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        messagesEl.removeChild(typingDiv);
        
        if (data.success) {
            var botMsgDiv = document.createElement('div');
            botMsgDiv.className = 'chat-message bot';
            
            // Format the response with proper bullet points
            var formattedResponse = formatBotResponse(data.response);
            botMsgDiv.innerHTML = formattedResponse;
            
            messagesEl.appendChild(botMsgDiv);
            
            chatHistories[religionName].push({
                role: 'assistant',
                content: data.response
            });
        } else {
            var errorMsgDiv = document.createElement('div');
            errorMsgDiv.className = 'chat-message bot';
            errorMsgDiv.style.color = '#EF4444';
            errorMsgDiv.textContent = '❌ ' + data.message;
            messagesEl.appendChild(errorMsgDiv);
        }
        
        sendBtn.disabled = false;
        messagesEl.scrollTop = messagesEl.scrollHeight;
    })
    .catch(function(error) {
        messagesEl.removeChild(typingDiv);
        
        var errorMsgDiv = document.createElement('div');
        errorMsgDiv.className = 'chat-message bot';
        errorMsgDiv.style.color = '#EF4444';
        errorMsgDiv.textContent = '❌ Connection error';
        messagesEl.appendChild(errorMsgDiv);
        
        sendBtn.disabled = false;
        messagesEl.scrollTop = messagesEl.scrollHeight;
    });
}

// ==================== VOICE CHAT ====================

var recognition = null;
var currentReligion = null;
var isRecording = false;

function initializeSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        recognition.onresult = function(event) {
            var interimTranscript = '';
            var finalTranscript = '';
            
            for (var i = event.resultIndex; i < event.results.length; i++) {
                var transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Update input field with live transcription
            if (currentReligion) {
                var inputId = 'input-' + sanitizeReligionName(currentReligion);
                var inputEl = document.getElementById(inputId);
                if (inputEl) {
                    inputEl.value = finalTranscript + interimTranscript;
                }
            }
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'no-speech') {
                stopVoiceInput();
            }
        };
        
        recognition.onend = function() {
            if (isRecording) {
                // Restart if it stopped unexpectedly
                try {
                    recognition.start();
                } catch(e) {
                    stopVoiceInput();
                }
            }
        };
    }
}

function startVoiceInput(religionName) {
    if (!recognition) {
        alert('Speech recognition not supported in your browser');
        return;
    }
    
    currentReligion = religionName;
    isRecording = true;
    
    try {
        recognition.start();
        document.getElementById('voice-' + sanitizeReligionName(religionName)).classList.add('recording');
    } catch(e) {
        console.log('Already started or error:', e);
    }
}

function stopVoiceInput(religionName) {
    if (recognition && isRecording) {
        isRecording = false;
        recognition.stop();
        document.getElementById('voice-' + sanitizeReligionName(religionName)).classList.remove('recording');
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSpeechRecognition);
} else {
    initializeSpeechRecognition();
}

// Make tooltips appear instantly on hover
document.addEventListener('DOMContentLoaded', function() {
    const micButtons = document.querySelectorAll('button[title]');
    
    micButtons.forEach(button => {
        const tooltipText = button.getAttribute('title');
        button.removeAttribute('title'); // Remove native tooltip
        
        // Create custom tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = tooltipText;
        
        // Add tooltip to button
        button.style.position = 'relative';
        button.appendChild(tooltip);
        
        button.addEventListener('mouseenter', function() {
            tooltip.style.opacity = '1';
        });
        
        button.addEventListener('mouseleave', function() {
            tooltip.style.opacity = '0';
        });
    });
});

