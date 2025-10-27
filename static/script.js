// Helper function to sanitize religion names for IDs
function sanitizeReligionName(name) {
    return name.replace(/\s+/g, '-');
}

// ==================== AUTHENTICATION ====================

function authenticate() {
    const username = document.getElementById('authUsername').value.trim();
    const password = document.getElementById('authPassword').value;
    
    if (!username || !password) {
        document.getElementById('result').innerHTML = 
            '<p class="error-msg">⚠️ Please fill in all fields</p>';
        return;
    }
    
    const endpoint = window.location.pathname === '/signup' ? '/signup' : '/login';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/assessment';
        } else {
            document.getElementById('result').innerHTML = 
                `<p class="error-msg">${data.message}</p>`;
        }
    });
}

function switchAuth() {
    const newPath = window.location.pathname === '/signup' ? '/login' : '/signup';
    window.location.href = newPath;
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
    document.getElementById('progressBar').style.width = (questionIndex / totalQuestions) * 100 + '%';
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
        tooltip.className = 'custom-tooltip';
        
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

