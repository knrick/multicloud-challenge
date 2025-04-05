// Chat widget functionality
class ChatWidget {
    constructor() {
        this.sessionId = null;
        this.isChatOpen = false;
    }

    async initChat() {
        try {
            const response = await fetch('/api/ai/bedrock/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to start chat session');
            }
            
            const data = await response.json();
            this.sessionId = data.sessionId;
            console.log('Chat session initialized:', this.sessionId);
            
            // Add initial message
            this.appendMessage("Hello! I'm your AI shopping assistant. How can I help you find products today?", false);
        } catch (error) {
            console.error('Error initializing chat:', error);
            this.appendMessage("Sorry, I'm having trouble connecting. Please try again later.", false);
        }
    }

    toggleChat() {
        const chatWidget = document.getElementById('chat-widget');
        this.isChatOpen = !this.isChatOpen;
        chatWidget.style.display = this.isChatOpen ? 'flex' : 'none';
        
        if (this.isChatOpen && !this.sessionId) {
            this.initChat();
        }
    }

    appendMessage(message, isUser = false) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`;
        
        const bubble = document.createElement('div');
        bubble.className = `rounded-lg px-4 py-2 max-w-[70%] ${
            isUser ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-800'
        }`;
        bubble.textContent = message;
        
        messageDiv.appendChild(bubble);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async sendMessage(event) {
        event.preventDefault();
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message || !this.sessionId) return;
        
        // Clear input
        messageInput.value = '';
        
        // Show user message
        this.appendMessage(message, true);
        
        try {
            const response = await fetch('/api/ai/bedrock/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.sessionId,
                    message: message
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to send message');
            }
            
            const data = await response.json();
            this.appendMessage(data.response, false);
        } catch (error) {
            console.error('Error sending message:', error);
            this.appendMessage("Sorry, I couldn't process your message. Please try again.", false);
        }
    }
}

// Initialize chat widget when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatWidget = new ChatWidget();
}); 