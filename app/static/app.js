/**
 * Legal RAG Chat Application
 * Industry-level chat interface with conversation management
 */

// ============================================================================
// Configuration
// ============================================================================
const CONFIG = {
    API_BASE: '',
    STORAGE_KEY: 'legal-rag-conversations',
    THEME_KEY: 'legal-rag-theme',
    LANGUAGE_KEY: 'legal-rag-language',
    MAX_CONVERSATIONS: 50,
    TYPING_SPEED: 15, // ms per character for streaming effect
};

// ============================================================================
// Utilities
// ============================================================================
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function formatDate(date) {
    const now = new Date();
    const d = new Date(date);
    const diff = now - d;

    if (diff < 86400000) return 'Today';
    if (diff < 172800000) return 'Yesterday';
    if (diff < 604800000) return 'This Week';
    return 'Older';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function debounce(fn, delay) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
}

// ============================================================================
// Theme Controller
// ============================================================================
const ThemeController = {
    init() {
        const savedTheme = localStorage.getItem(CONFIG.THEME_KEY) || 'dark';
        this.setTheme(savedTheme, false);
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = current === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme, true);
    },

    setTheme(theme, save = true) {
        document.documentElement.setAttribute('data-theme', theme);
        if (save) localStorage.setItem(CONFIG.THEME_KEY, theme);

        // Update theme toggle icon
        const themeBtn = $('#themeToggle');
        if (themeBtn) {
            themeBtn.innerHTML = theme === 'dark'
                ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        }
    }
};

// ============================================================================
// Language Controller
// ============================================================================
const LanguageController = {
    currentLanguage: 'en',

    languages: {
        'en': { name: 'English', native: 'English' },
        'kn': { name: 'Kannada', native: 'ಕನ್ನಡ' },
        'hi': { name: 'Hindi', native: 'हिंदी' }
    },

    init() {
        this.currentLanguage = localStorage.getItem(CONFIG.LANGUAGE_KEY) || 'en';
        this.updateUI();
        this.bindEvents();
    },

    bindEvents() {
        // Language pill buttons
        $$('.lang-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                const lang = pill.dataset.lang;
                this.setLanguage(lang);
            });
        });
    },

    setLanguage(lang) {
        if (!this.languages[lang]) return;

        this.currentLanguage = lang;
        localStorage.setItem(CONFIG.LANGUAGE_KEY, lang);
        this.updateUI();
    },

    updateUI() {
        // Update active state for pill buttons
        $$('.lang-pill').forEach(pill => {
            pill.classList.toggle('active', pill.dataset.lang === this.currentLanguage);
        });
    },

    getLanguage() {
        return this.currentLanguage;
    }
};

// ============================================================================
// Conversation Manager
// ============================================================================
const ConversationManager = {
    conversations: [],
    currentId: null,

    init() {
        this.load();
        if (this.conversations.length === 0) {
            this.create();
        } else {
            this.switch(this.conversations[0].id);
        }
        this.render();
    },

    load() {
        try {
            const data = localStorage.getItem(CONFIG.STORAGE_KEY);
            this.conversations = data ? JSON.parse(data) : [];
        } catch {
            this.conversations = [];
        }
    },

    save() {
        // Keep only recent conversations
        if (this.conversations.length > CONFIG.MAX_CONVERSATIONS) {
            this.conversations = this.conversations.slice(0, CONFIG.MAX_CONVERSATIONS);
        }
        localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(this.conversations));
    },

    create() {
        const conversation = {
            id: generateId(),
            title: 'New Conversation',
            messages: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        this.conversations.unshift(conversation);
        this.save();
        this.switch(conversation.id);
        this.render();
        ChatUI.showWelcome();
        return conversation;
    },

    switch(id) {
        this.currentId = id;
        this.render();
        ChatUI.renderMessages(this.getCurrent().messages);
    },

    getCurrent() {
        return this.conversations.find(c => c.id === this.currentId) || this.conversations[0];
    },

    addMessage(role, content, sources = null) {
        const conversation = this.getCurrent();
        if (!conversation) return;

        const message = {
            id: generateId(),
            role,
            content,
            sources,
            timestamp: new Date().toISOString()
        };

        conversation.messages.push(message);
        conversation.updatedAt = new Date().toISOString();

        // Update title from first user message
        if (role === 'user' && conversation.messages.filter(m => m.role === 'user').length === 1) {
            conversation.title = content.slice(0, 40) + (content.length > 40 ? '...' : '');
        }

        this.save();
        this.render();
        return message;
    },

    delete(id) {
        const index = this.conversations.findIndex(c => c.id === id);
        if (index === -1) return;

        this.conversations.splice(index, 1);
        this.save();

        if (id === this.currentId) {
            if (this.conversations.length > 0) {
                this.switch(this.conversations[0].id);
            } else {
                this.create();
            }
        }
        this.render();
    },

    search(query) {
        if (!query.trim()) {
            this.render();
            return;
        }

        const q = query.toLowerCase();
        const filtered = this.conversations.filter(c =>
            c.title.toLowerCase().includes(q) ||
            c.messages.some(m => m.content.toLowerCase().includes(q))
        );
        this.render(filtered);
    },

    render(list = null) {
        const conversations = list || this.conversations;
        const container = $('#conversationList');
        if (!container) return;

        // Group by date
        const groups = {};
        conversations.forEach(conv => {
            const group = formatDate(conv.updatedAt);
            if (!groups[group]) groups[group] = [];
            groups[group].push(conv);
        });

        let html = '';
        Object.entries(groups).forEach(([label, convs]) => {
            html += `<div class="conversation-group-label">${label}</div>`;
            convs.forEach(conv => {
                const isActive = conv.id === this.currentId;
                html += `
                    <div class="conversation-item ${isActive ? 'active' : ''}" data-id="${conv.id}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                        <span class="conversation-title">${escapeHtml(conv.title)}</span>
                        <button class="conversation-delete" data-id="${conv.id}" title="Delete">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                    </div>
                `;
            });
        });

        container.innerHTML = html || '<p style="text-align:center;color:var(--text-muted);padding:20px;">No conversations yet</p>';

        // Add event listeners
        container.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.conversation-delete')) return;
                this.switch(item.dataset.id);
                SidebarController.close();
            });
        });

        container.querySelectorAll('.conversation-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.delete(btn.dataset.id);
            });
        });
    }
};

// ============================================================================
// Sidebar Controller
// ============================================================================
const SidebarController = {
    init() {
        const menuToggle = $('#menuToggle');
        const overlay = $('#sidebarOverlay');

        menuToggle?.addEventListener('click', () => this.toggle());
        overlay?.addEventListener('click', () => this.close());
    },

    toggle() {
        const sidebar = $('#sidebar');
        sidebar?.classList.toggle('open');
    },

    close() {
        const sidebar = $('#sidebar');
        sidebar?.classList.remove('open');
    }
};

// ============================================================================
// Chat UI
// ============================================================================
const ChatUI = {
    isTyping: false,

    init() {
        this.bindEvents();
        this.checkHealth();
        setInterval(() => this.checkHealth(), 30000);
    },

    bindEvents() {
        const input = $('#messageInput');
        const sendBtn = $('#sendBtn');
        const form = $('#chatForm');

        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        input?.addEventListener('input', () => {
            this.autoResize(input);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+N: New conversation
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                ConversationManager.create();
            }
            // Escape: Close modals/sidebar
            if (e.key === 'Escape') {
                UploadModal.close();
                SidebarController.close();
            }
        });

        // Theme toggle
        $('#themeToggle')?.addEventListener('click', () => ThemeController.toggle());

        // Upload button
        $('#uploadToggle')?.addEventListener('click', () => UploadModal.open());

        // New chat button
        $('#newChatBtn')?.addEventListener('click', () => ConversationManager.create());

        // Search
        $('#searchInput')?.addEventListener('input', debounce((e) => {
            ConversationManager.search(e.target.value);
        }, 300));
    },

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    },

    async checkHealth() {
        const dot = $('#statusDot');
        const text = $('#statusText');

        try {
            const response = await fetch('/health/');
            const data = await response.json();

            if (data.api_status === 'active' && data.db_status === 'connected') {
                dot.className = 'status-dot online';
                text.textContent = 'Online';
            } else if (data.api_status === 'inactive') {
                dot.className = 'status-dot offline';
                text.textContent = 'API Error';
            } else {
                dot.className = 'status-dot offline';
                text.textContent = 'DB Error';
            }
        } catch {
            dot.className = 'status-dot offline';
            text.textContent = 'Offline';
        }
    },

    showWelcome() {
        const container = $('#messagesWrapper');
        container.innerHTML = `
            <div class="welcome-screen">
                <div class="welcome-icon">⚖️</div>
                <h2>Legal RAG Assistant</h2>
                <p>Ask questions about legal documents. I'll search through the knowledge base and provide detailed answers with sources.</p>
                <div class="suggestions">
                    <button class="suggestion-chip" data-query="What are the key provisions in the Civil Procedure Code?">Civil Procedure Code basics</button>
                    <button class="suggestion-chip" data-query="Explain RERA regulations for real estate">RERA regulations</button>
                    <button class="suggestion-chip" data-query="What are the filing deadlines for appeals?">Appeal deadlines</button>
                </div>
            </div>
        `;

        container.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const input = $('#messageInput');
                input.value = chip.dataset.query;
                this.sendMessage();
            });
        });
    },

    renderMessages(messages) {
        const container = $('#messagesWrapper');

        if (!messages || messages.length === 0) {
            this.showWelcome();
            return;
        }

        container.innerHTML = messages.map(msg => this.createMessageHTML(msg)).join('');
        this.scrollToBottom();
    },

    createMessageHTML(message) {
        const isUser = message.role === 'user';
        const avatar = isUser ? '👤' : '⚖️';
        const content = isUser ? escapeHtml(message.content) : this.renderMarkdown(message.content);

        let sourcesHTML = '';
        if (!isUser && message.sources && message.sources.length > 0) {
            sourcesHTML = `
                <div class="sources-panel" onclick="ChatUI.toggleSources(this)">
                    <div class="sources-header">
                        <div class="sources-header-left">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>
                            </svg>
                            <span>Sources (${message.sources.length} documents)</span>
                        </div>
                        <svg class="sources-toggle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M6 9l6 6 6-6"/>
                        </svg>
                    </div>
                    <div class="sources-content">
                        ${message.sources.map(source => `
                            <div class="source-item">
                                <div class="source-title">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                        <path d="M14 2v6h6"/>
                                    </svg>
                                    ${escapeHtml(source.filename || 'Document')}${source.page ? ` (p. ${source.page})` : ''}
                                </div>
                                <div class="source-excerpt">${escapeHtml(source.excerpt || source.text || '')}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        return `
            <div class="message ${message.role}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-body">
                    <div class="message-content">${content}</div>
                    ${sourcesHTML}
                    ${!isUser ? `
                        <div class="message-actions">
                            <button class="message-action-btn" onclick="ChatUI.copyMessage(this)" title="Copy">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="9" y="9" width="13" height="13" rx="2"/>
                                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                                </svg>
                                Copy
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },

    renderMarkdown(text) {
        if (!text) return '';

        // Use marked.js if available, otherwise basic formatting
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }

        // Basic markdown fallback
        let html = escapeHtml(text);

        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Code blocks
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // Inline code
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');
        // Line breaks
        html = html.replace(/\n/g, '<br>');
        // Headers
        html = html.replace(/^### (.*?)(<br>|$)/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.*?)(<br>|$)/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.*?)(<br>|$)/gm, '<h1>$1</h1>');

        return html;
    },

    toggleSources(panel) {
        panel.classList.toggle('open');
    },

    copyMessage(btn) {
        const content = btn.closest('.message-body').querySelector('.message-content');
        navigator.clipboard.writeText(content.textContent).then(() => {
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Copied!';
            setTimeout(() => btn.innerHTML = originalHTML, 2000);
        });
    },

    async sendMessage() {
        const input = $('#messageInput');
        const message = input.value.trim();

        if (!message || this.isTyping) return;

        // Clear input
        input.value = '';
        input.style.height = 'auto';

        // Remove welcome screen if present
        const welcome = $('.welcome-screen');
        if (welcome) welcome.remove();

        // Add user message
        const userMsg = ConversationManager.addMessage('user', message);
        this.appendMessage(userMsg);

        // Show typing
        this.showTyping();
        this.isTyping = true;

        // Get the current language setting
        const lang = LanguageController.getLanguage();

        try {
            const response = await fetch(`/chat/?message=${encodeURIComponent(message)}&lang=${lang}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

            const data = await response.json();

            // Prepare sources if available
            const sources = data.sources || data.contexts?.map(ctx => ({
                filename: ctx.source_file || ctx.metadata?.filename,
                page: ctx.page || ctx.metadata?.page,
                excerpt: ctx.text?.slice(0, 200) + '...'
            }));

            // Remove typing indicator
            this.hideTyping();

            // Add assistant response with streaming effect
            const assistantMsg = {
                id: generateId(),
                role: 'assistant',
                content: data.answer,
                sources: sources,
                timestamp: new Date().toISOString()
            };

            await this.streamMessage(assistantMsg);
            ConversationManager.addMessage('assistant', data.answer, sources);

        } catch (error) {
            console.error('Chat error:', error);
            this.hideTyping();

            const errorMsg = {
                id: generateId(),
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request. Please try again.',
                timestamp: new Date().toISOString()
            };
            this.appendMessage(errorMsg);
        }

        this.isTyping = false;
        input.focus();
    },

    appendMessage(message) {
        const container = $('#messagesWrapper');
        container.insertAdjacentHTML('beforeend', this.createMessageHTML(message));
        this.scrollToBottom();
    },

    async streamMessage(message) {
        const container = $('#messagesWrapper');
        const isUser = message.role === 'user';
        const avatar = isUser ? '👤' : '⚖️';

        // Create message container
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-body">
                <div class="message-content"></div>
            </div>
        `;
        container.appendChild(messageDiv);

        const contentDiv = messageDiv.querySelector('.message-content');

        // Stream the text
        const text = message.content;
        let currentIndex = 0;

        await new Promise(resolve => {
            const stream = () => {
                if (currentIndex < text.length) {
                    // Add characters in chunks for better performance
                    const chunk = text.slice(currentIndex, currentIndex + 3);
                    currentIndex += 3;
                    contentDiv.innerHTML = this.renderMarkdown(text.slice(0, currentIndex));
                    this.scrollToBottom();
                    setTimeout(stream, CONFIG.TYPING_SPEED);
                } else {
                    // Done streaming, add full content with sources and actions
                    messageDiv.outerHTML = this.createMessageHTML(message);
                    resolve();
                }
            };
            stream();
        });

        this.scrollToBottom();
    },

    showTyping() {
        const container = $('#messagesWrapper');
        const typingHTML = `
            <div class="message assistant" id="typingIndicator">
                <div class="message-avatar">⚖️</div>
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', typingHTML);
        this.scrollToBottom();
    },

    hideTyping() {
        $('#typingIndicator')?.remove();
    },

    scrollToBottom() {
        const container = $('#messagesContainer');
        container.scrollTop = container.scrollHeight;
    }
};

// ============================================================================
// Upload Modal
// ============================================================================
const UploadModal = {
    selectedFile: null,

    init() {
        const zone = $('#uploadZone');
        const fileInput = $('#fileInput');
        const closeBtn = $('#modalClose');
        const cancelBtn = $('#cancelUpload');
        const uploadBtn = $('#uploadBtn');

        zone?.addEventListener('click', () => fileInput?.click());
        zone?.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });
        zone?.addEventListener('dragleave', () => zone.classList.remove('dragover'));
        zone?.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            if (e.dataTransfer.files[0]) this.selectFile(e.dataTransfer.files[0]);
        });

        fileInput?.addEventListener('change', () => {
            if (fileInput.files[0]) this.selectFile(fileInput.files[0]);
        });

        closeBtn?.addEventListener('click', () => this.close());
        cancelBtn?.addEventListener('click', () => this.close());
        uploadBtn?.addEventListener('click', () => this.upload());

        // Close on overlay click
        $('#uploadModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'uploadModal') this.close();
        });
    },

    open() {
        $('#uploadModal')?.classList.add('open');
    },

    close() {
        $('#uploadModal')?.classList.remove('open');
        this.reset();
    },

    selectFile(file) {
        if (!file.name.endsWith('.pdf')) {
            this.showStatus('error', 'Please select a PDF file');
            return;
        }

        this.selectedFile = file;
        const zone = $('#uploadZone');
        zone.classList.add('has-file');
        zone.querySelector('h4').textContent = 'File selected';
        zone.querySelector('p').innerHTML = `<span class="filename">${escapeHtml(file.name)}</span>`;
        $('#uploadBtn').disabled = false;
    },

    async upload() {
        if (!this.selectedFile) return;

        const uploadBtn = $('#uploadBtn');
        const tag = $('#tagInput').value.trim();

        uploadBtn.disabled = true;
        this.showStatus('loading', 'Uploading and processing...');

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        if (tag) formData.append('tag', tag);

        try {
            const response = await fetch('/ingest/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.showStatus('success', `✅ Processed ${data.pages} pages, stored ${data.chunks_stored} chunks`);
                setTimeout(() => this.close(), 2000);
            } else {
                throw new Error(data.message || data.detail || 'Upload failed');
            }
        } catch (error) {
            this.showStatus('error', `❌ ${error.message}`);
            uploadBtn.disabled = false;
        }
    },

    showStatus(type, message) {
        const status = $('#uploadStatus');
        status.className = `upload-status ${type}`;
        status.textContent = message;
    },

    reset() {
        this.selectedFile = null;

        const zone = $('#uploadZone');
        zone.classList.remove('has-file');
        zone.querySelector('h4').textContent = 'Drop your PDF here';
        zone.querySelector('p').textContent = 'or click to browse';

        $('#fileInput').value = '';
        $('#tagInput').value = '';
        $('#uploadBtn').disabled = true;
        $('#uploadStatus').className = 'upload-status';
    }
};

// ============================================================================
// Initialize Application
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    ThemeController.init();
    LanguageController.init();
    ConversationManager.init();
    SidebarController.init();
    ChatUI.init();
    UploadModal.init();

    console.log('Legal RAG Chat initialized');
});

// Make ChatUI globally accessible for inline handlers
window.ChatUI = ChatUI;
