document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.querySelector('.typing-indicator');
    const errorMessage = document.getElementById('error-message');
    const themeToggle = document.getElementById('theme-toggle');
    const createSessionBtn = document.getElementById('create-session-btn');
    const sessionForm = document.getElementById('session-form');
    const saveSessionBtn = document.getElementById('save-session-btn');
    const cancelSessionBtn = document.getElementById('cancel-session-btn');
    const sessionsList = document.getElementById('sessions-list');
    const systemPrompt = document.getElementById('system-prompt');
    const currentSessionInfo = document.getElementById('current-session-info');

    // State management
    let currentSessionId = localStorage.getItem('lastSessionId');
    let darkMode = localStorage.getItem('darkMode') === 'true';
    let isFirstVisit = !localStorage.getItem('hasVisited');

    // Generate unique user ID if not exists
    let userId = localStorage.getItem('userId');
    if (!userId) {
        userId = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('userId', userId);
    }

    // Session Management Functions
    function showSessionForm() {
        sessionForm.classList.add('active');
        systemPrompt.focus();
    }

    function hideSessionForm() {
        sessionForm.classList.remove('active');
        systemPrompt.value = '';
    }

    async function createDefaultSession() {
        try {
            const response = await fetch('/create_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    system_prompt: "Default chat session"
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                currentSessionId = data.session_id;
                localStorage.setItem('lastSessionId', currentSessionId);
                await loadSessions();
                return data.session_id;
            }
            throw new Error('Failed to create default session');
        } catch (error) {
            console.error('Error creating default session:', error);
            showError('Error creating default session');
        }
    }

    async function createSession(systemPromptText) {
        try {
            const response = await fetch('/create_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    system_prompt: systemPromptText || "New chat session"
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                currentSessionId = data.session_id;
                localStorage.setItem('lastSessionId', currentSessionId);
                await loadSessions();
                switchSession(data.session_id);
                hideSessionForm();
            } else {
                showError('Failed to create session');
            }
        } catch (error) {
            console.error('Error creating session:', error);
            showError('Error creating session');
        }
    }

    async function loadSessions() {
        try {
            const response = await fetch('/get_sessions');
            const data = await response.json();
            
            if (data.status === 'success') {
                sessionsList.innerHTML = '';
                data.sessions.forEach(session => {
                    const sessionElement = document.createElement('div');
                    sessionElement.classList.add('session-item');
                    
                    if (session.session_id === currentSessionId) {
                        sessionElement.classList.add('active');
                    }

                    sessionElement.innerHTML = `
                        <div class="session-info" data-session-id="${session.session_id}">
                            <div class="session-prompt">${session.system_prompt || 'Untitled Session'}</div>
                            <div class="session-date">${new Date(session.created_at).toLocaleDateString()}</div>
                        </div>
                    `;

                    sessionsList.appendChild(sessionElement);
                });

                // Add create new session button
                const newSessionElement = document.createElement('div');
                newSessionElement.classList.add('session-item', 'new-session');
                newSessionElement.innerHTML = `
                    <div class="session-info">
                        <div class="session-prompt">
                            <i class="fas fa-plus"></i> New Chat
                        </div>
                    </div>
                `;
                newSessionElement.addEventListener('click', showSessionForm);
                sessionsList.appendChild(newSessionElement);
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
            showError('Error loading sessions');
        }
    }

    async function switchSession(sessionId) {
        if (currentSessionId === sessionId) return;
        
        currentSessionId = sessionId;
        localStorage.setItem('lastSessionId', sessionId);
        chatMessages.innerHTML = '';
        
        try {
            const response = await fetch(`/get_conversation/${sessionId}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                data.conversations.forEach(conv => {
                    addMessageToUI({
                        content: conv.content,
                        isUser: conv.role === 'user',
                        timestamp: new Date(conv.timestamp).toLocaleTimeString()
                    }, false);
                });

                // Update session info display
                const sessionElements = document.querySelectorAll('.session-item');
                sessionElements.forEach(el => {
                    el.classList.toggle('active', el.querySelector('.session-info')?.dataset.sessionId === sessionId);
                });

                const activeSession = document.querySelector('.session-item.active .session-prompt');
                if (activeSession) {
                    currentSessionInfo.textContent = activeSession.textContent;
                }
            }
        } catch (error) {
            console.error('Error switching session:', error);
            showError('Error loading conversation');
        }
    }

    // UI Helper Functions
    function showTypingIndicator() {
        typingIndicator.style.display = 'flex';
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.add('active');
        
        setTimeout(() => {
            errorMessage.classList.remove('active');
        }, 5000);
    }

    function updateTheme() {
        document.body.setAttribute('data-theme', darkMode ? 'dark' : 'light');
        themeToggle.innerHTML = darkMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }

    function formatMessage(message) {
        // Handle code blocks
        message = message.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, language, code) => {
            return `<pre><code class="${language || ''}">${code.trim()}</code></pre>`;
        });

        // Handle inline code
        message = message.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Handle URLs
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        message = message.replace(urlRegex, url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);

        return message;
    }

    function addMessageToUI(message, animate = true) {
        const wrapper = document.createElement('div');
        wrapper.classList.add('message-wrapper', message.isUser ? 'user-message-wrapper' : 'bot-message-wrapper');

        const messageElement = document.createElement('div');
        messageElement.classList.add('message', message.isUser ? 'user-message' : 'bot-message');

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        messageContent.innerHTML = formatMessage(message.content);

        const timestampElement = document.createElement('div');
        timestampElement.classList.add('timestamp');
        timestampElement.textContent = message.timestamp;

        messageElement.appendChild(messageContent);
        messageElement.appendChild(timestampElement);
        wrapper.appendChild(messageElement);
        
        if (animate) {
            wrapper.style.opacity = '0';
            wrapper.style.transform = 'translateY(20px)';
        }
        
        chatMessages.appendChild(wrapper);
        
        if (animate) {
            requestAnimationFrame(() => {
                wrapper.style.opacity = '1';
                wrapper.style.transform = 'translateY(0)';
            });
        }

        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: animate ? 'smooth' : 'auto'
        });

        // Initialize code highlighting if present
        if (messageContent.querySelector('pre code')) {
            hljs.highlightAll();
        }
    }

    function disableInterface() {
        messageInput.disabled = true;
        sendButton.disabled = true;
        messageInput.style.opacity = '0.7';
        sendButton.style.opacity = '0.7';
    }

    function enableInterface() {
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.style.opacity = '1';
        sendButton.style.opacity = '1';
        messageInput.focus();
    }

    // Message Handling
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || !currentSessionId) return;

        const timestamp = new Date().toLocaleTimeString();

        addMessageToUI({
            content: message,
            isUser: true,
            timestamp: timestamp
        });
        
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        disableInterface();
        showTypingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    message: message,
                    session_id: currentSessionId,
                    userId: userId
                })
            });

            const data = await response.json();
            
            hideTypingIndicator();
            
            if (data.status === 'error') {
                showError('Sorry, something went wrong. Please try again.');
                console.error('Error:', data.error);
            } else {
                setTimeout(() => {
                    addMessageToUI({
                        content: data.response,
                        isUser: false,
                        timestamp: data.timestamp
                    });
                }, 300);
            }
        } catch (error) {
            hideTypingIndicator();
            showError('Network error. Please check your connection.');
            console.error('Error:', error);
        }

        enableInterface();
    }

    // Event Listeners
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sessionsList.addEventListener('click', (e) => {
        const sessionInfo = e.target.closest('.session-info');
        if (sessionInfo && sessionInfo.dataset.sessionId) {
            switchSession(sessionInfo.dataset.sessionId);
        }
    });

    sendButton.addEventListener('click', sendMessage);
    themeToggle.addEventListener('click', () => {
        darkMode = !darkMode;
        localStorage.setItem('darkMode', darkMode);
        updateTheme();
    });

    createSessionBtn.addEventListener('click', showSessionForm);
    cancelSessionBtn.addEventListener('click', hideSessionForm);
    saveSessionBtn.addEventListener('click', (e) => {
        e.preventDefault();
        createSession(systemPrompt.value);
    });

    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 250);
    });

    // Initialization
    (async function init() {
        try {
            updateTheme();
            
            // Create default session for first-time visitors
            if (isFirstVisit || !currentSessionId) {
                currentSessionId = await createDefaultSession();
                localStorage.setItem('hasVisited', 'true');
            }
            
            await loadSessions();
            if (currentSessionId) {
                await switchSession(currentSessionId);
            }
            
            messageInput.focus();
        } catch (error) {
            console.error('Initialization error:', error);
            showError('Error initializing chat');
        }
    })();
});