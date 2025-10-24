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
            window.location.href = '/';
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
        if (blockIndex < questionIndex) {
            block.querySelectorAll('input[type="radio"]').forEach(function(radio) {
                radio.disabled = true;
            });
        }
    });
    
    currentQuestion = questionIndex;
    document.getElementById('questionCounter').textContent = 'Question ' + questionIndex + ' of ' + totalQuestions;
    document.getElementById('progressBar').style.width = (questionIndex / totalQuestions) * 100 + '%';
    updateNavigationButtons();
}

function updateNavigationButtons() {
    var nextBtn = document.getElementById('nextBtn' + currentQuestion);
    
    if (nextBtn) {
        var currentQuestionId = questionIds[currentQuestion - 1];
        var radioName = 'q' + currentQuestionId;
        var isAnswered = document.querySelector('input[name="' + radioName + '"]:checked') !== null;
        
        if (currentQuestion === totalQuestions && isAnswered) {
            nextBtn.style.display = 'none';
            document.getElementById('submitBtn').style.display = 'block';
        } else {
            nextBtn.disabled = !isAnswered;
            nextBtn.style.display = 'inline-block';
        }
    }
}

function handleAnswer(radioElement) {
    var questionIndex = parseInt(radioElement.getAttribute('data-question-index'));
    
    // Only process if this is the current question
    if (questionIndex !== currentQuestion) {
        return;
    }
    
    updateNavigationButtons();
    
    // Auto-advance to next question after selection
    setTimeout(function() {
        if (questionIndex < totalQuestions) {
            showQuestion(questionIndex + 1);
        } else {
            // Last question - show submit button
            var nextBtn = document.getElementById('nextBtn' + questionIndex);
            if (nextBtn) {
                nextBtn.style.display = 'none';
            }
            document.getElementById('submitBtn').style.display = 'block';
        }
    }, 400);
}

function goToNext() {
    if (currentQuestion < totalQuestions) {
        showQuestion(currentQuestion + 1);
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

