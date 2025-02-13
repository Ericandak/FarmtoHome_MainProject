// Get CSRF token
const DEBUG = true;


function log(...args) {
    if (DEBUG) {
        console.log(...args);
    }
}
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') return value;
    }
    return null;
}

function handleFetchError(error) {
    console.error('Error:', error);
    if (error.message === 'Failed to fetch') {
        addMessage('bot', 'Sorry, I cannot connect to the server right now. Please try again later.');
    } else {
        addMessage('bot', 'Sorry, I encountered an error. Please try again.');
    }
}

let chatVisible = false;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initChatWidget();
});

function initChatWidget() {
    const input = document.getElementById('botMessageInput');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendBotMessage();
            }
        });
    }
}

function initChatContent() {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer.querySelector('.chat-messages')) {
        const messagesDiv = document.getElementById('botMessages');
        if (messagesDiv) {
            messagesDiv.innerHTML = `
                <div class="message bot">
                    <div class="message-content">
                        <p>Hi 👋 How can I help you?</p>
                        <div class="quick-replies">
                            <button onclick="sendQuickReply('Track my order')">Track my order 📦</button>
                            <button onclick="sendQuickReply('How do I track my order?')">How do I track my order (FAQ)?</button>
                            <button onclick="sendQuickReply('Contact seller')">Contact seller</button>
                            <button onclick="sendQuickReply('Product information')">Product information</button>
                        </div>
                    </div>
                </div>
            `;
        }
    }
}

function toggleChat() {
    const chatContainer = document.getElementById('chatContainer');
    chatVisible = !chatVisible;
    chatContainer.style.display = chatVisible ? 'flex' : 'none';
    
    if (chatVisible && !chatContainer.hasAttribute('data-initialized')) {
        initChatContent();
        chatContainer.setAttribute('data-initialized', 'true');
    }
}

function sendQuickReply(message) {
    addMessage('user', message);
    sendMessage(message);
}

function sendBotMessage() {
    const input = document.getElementById('botMessageInput');
    const message = input.value.trim();
    
    if (message) {
        addMessage('user', message);
        sendMessage(message);
        input.value = '';
    }
}

function addMessage(type, content) {
    const messagesDiv = document.getElementById('botMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    if (typeof content === 'object' && content.text) {
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${content.text}</p>
                ${content.quickReplies ? `
                    <div class="quick-replies">
                        ${content.quickReplies.map(reply => 
                            `<button onclick="sendQuickReply('${reply}')">${reply}</button>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
    }
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
async function sendMessage(message) {
    try {
        log('Sending message:', message);

        const response = await fetch(CHATBOT_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ message: message })
        });
        log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        log('Received response:', data);
        addMessage('bot', data.message);
    } catch (error) {
        log('Error in sendMessage:', error);
        handleFetchError(error);
    }
}