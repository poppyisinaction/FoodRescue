// FoodRescue AI Chatbot Frontend Controller

document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('chatbot-toggle-btn');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeBtn = document.getElementById('chatbot-close-btn');
    const inputField = document.getElementById('chatbot-input');
    const sendBtn = document.getElementById('chatbot-send-btn');
    const messagesContainer = document.getElementById('chatbot-messages');
    const typingIndicator = document.getElementById('chatbot-typing');
    const suggestionChips = document.querySelectorAll('.chat-suggestion-chip');

    if (!toggleBtn || !chatbotWindow) return;

    // Toggle Chat Window
    function toggleChat() {
        const isOpen = chatbotWindow.classList.contains('open');
        if (isOpen) {
            chatbotWindow.classList.remove('open');
        } else {
            chatbotWindow.classList.add('open');
            if (inputField) inputField.focus();
            scrollToBottom();
        }
    }

    toggleBtn.addEventListener('click', toggleChat);
    if (closeBtn) closeBtn.addEventListener('click', toggleChat);

    // Click outside to close on mobile
    document.addEventListener('click', function (e) {
        if (!chatbotWindow.contains(e.target) && !toggleBtn.contains(e.target) && chatbotWindow.classList.contains('open')) {
            chatbotWindow.classList.remove('open');
        }
    });

    // Handle Suggestions
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', function () {
            const query = this.getAttribute('data-query') || this.innerText.trim();
            if (inputField) {
                inputField.value = query;
                sendMessage();
            }
        });
    });

    // Send on Enter
    if (inputField) {
        inputField.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', function (e) {
            e.preventDefault();
            sendMessage();
        });
    }

    function scrollToBottom() {
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    function formatText(text) {
        // Simple markdown bold and linebreaks
        let formatted = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
            
        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Convert bullet lines
        formatted = formatted.replace(/\n\s*•\s*/g, '<br>• ');
        formatted = formatted.replace(/\n\s*-\s*/g, '<br>• ');
        // Convert line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        return formatted;
    }

    function appendUserMessage(text) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble chat-bubble-user';
        bubble.innerHTML = formatText(text);
        messagesContainer.appendChild(bubble);
        scrollToBottom();
    }

    function appendBotMessage(text, isLLM = false) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble chat-bubble-bot';
        let content = formatText(text);
        if (isLLM) {
            content += `<div class="text-end mt-1"><span class="badge bg-light text-secondary border" style="font-size:0.65rem;"><i class="fa-solid fa-sparkles text-success me-1"></i>AI Enhanced</span></div>`;
        }
        bubble.innerHTML = content;
        messagesContainer.appendChild(bubble);
        scrollToBottom();
    }

    function sendMessage() {
        const message = inputField.value.trim();
        if (!message) return;

        appendUserMessage(message);
        inputField.value = '';

        // Show typing indicator
        if (typingIndicator) {
            typingIndicator.style.display = 'flex';
            scrollToBottom();
        }

        fetch('/chatbot/api/message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (typingIndicator) typingIndicator.style.display = 'none';
            if (data.response) {
                appendBotMessage(data.response, data.used_llm);
            } else if (data.error) {
                appendBotMessage("I encountered an issue: " + data.error);
            }
        })
        .catch(err => {
            console.error('Chatbot error:', err);
            if (typingIndicator) typingIndicator.style.display = 'none';
            appendBotMessage("Sorry, I'm currently unable to process your request. Please try again or visit our Contact Us page.");
        });
    }
});
