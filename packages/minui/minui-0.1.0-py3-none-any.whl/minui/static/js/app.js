const STORAGE_KEY = 'mui_settings_v1';

// Single Source of Truth for Defaults
const DEFAULT_SETTINGS = {
    provider: 'openai',
    api_url: 'https://openrouter.ai/api/v1',
    api_key: '',
    model: 'deepseek/deepseek-chat',
    system_prompt: 'You are maintaining the repository. The user is sending you patches or questions regarding the codebase. Reply in plain-text as a Senior Engineer in the style of a mailing list.'
};

const UI = {
    els: {
        input: document.getElementById('main-input'),
        thread: document.getElementById('thread-container'),
        sendBtn: document.getElementById('send-btn'),
        status: document.getElementById('status-indicator'),
        tokens: document.getElementById('token-counter'),
        debugModal: document.getElementById('debug-modal'),
        settingsModal: document.getElementById('settings-modal'),
        debugContent: document.getElementById('debug-content'),
        modelDisplay: document.getElementById('model-display')
    },

    appendMessage(role, text, isHtml = false) {
        const div = document.createElement('div');
        div.className = 'message';
        
        let headerHtml = `<div class="message-header"><span class="role-name">${role}</span>`;
        if (role !== "Me") headerHtml += `<button class="text-btn copy-btn" style="font-size:12px">Copy</button>`;
        headerHtml += `</div>`;

        const body = document.createElement('div');
        body.className = 'message-body';
        if (isHtml) body.innerHTML = text; else body.innerText = text;

        div.innerHTML = headerHtml;
        div.appendChild(body);
        this.els.thread.appendChild(div);
        return body;
    },

    renderFormat(text) {
        const parts = text.split(/(```[\s\S]*?```)/g);
        return parts.map(part => {
            if (part.startsWith('```')) {
                const match = part.match(/^```(\w*)\n([\s\S]*?)```$/);
                if (match) {
                    const lang = match[1] || 'text';
                    const code = match[2];
                    try { return `<pre><code class="hljs">${hljs.highlightAuto(code).value}</code></pre>`; } 
                    catch (e) { return `<pre>${code}</pre>`; }
                }
                return part;
            }
            return part.split('\n').map(line => {
                const clean = line.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                if (clean.trim().startsWith('&gt;')) return `<div class="email-quote">${clean}</div>`;
                return clean;
            }).join('<br>');
        }).join('');
    }
};

class App {
    constructor() {
        this.history = [];
        this.settings = this.loadSettings();
        
        this.bindEvents();
        
        // Initialize UI with loaded settings (or defaults)
        this.updateUI();
        
        // Force settings open if no key
        if (!this.settings.api_key) {
            UI.els.settingsModal.classList.add('active');
        }
    }

    loadSettings() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return { ...DEFAULT_SETTINGS };
        return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }

    saveSettings() {
        const newSettings = {
            provider: document.getElementById('cfg-provider').value,
            api_url: document.getElementById('cfg-url').value,
            api_key: document.getElementById('cfg-key').value,
            model: document.getElementById('cfg-model').value,
            system_prompt: document.getElementById('cfg-prompt').value
        };
        this.settings = newSettings;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
        UI.els.settingsModal.classList.remove('active');
        this.updateUI();
    }

    updateUI() {
        UI.els.modelDisplay.innerText = this.settings.model || "No Model";
        
        document.getElementById('cfg-provider').value = this.settings.provider;
        document.getElementById('cfg-url').value = this.settings.api_url;
        document.getElementById('cfg-key').value = this.settings.api_key;
        document.getElementById('cfg-model').value = this.settings.model;
        document.getElementById('cfg-prompt').value = this.settings.system_prompt;
    }

    bindEvents() {
        document.getElementById('send-btn').addEventListener('click', () => this.handleSend());
        document.getElementById('reset-btn').addEventListener('click', () => window.location.reload());
        UI.els.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) this.handleSend();
        });

        document.getElementById('debug-btn').addEventListener('click', () => this.showContext());
        document.getElementById('settings-btn').addEventListener('click', () => UI.els.settingsModal.classList.add('active'));
        document.getElementById('save-settings-btn').addEventListener('click', () => this.saveSettings());
        
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', (e) => e.target.closest('.modal').classList.remove('active'));
        });

        document.body.addEventListener('click', async (e) => {
            if (e.target.classList.contains('copy-btn')) {
                const text = e.target.closest('.message').querySelector('.message-body').innerText;
                await navigator.clipboard.writeText(text);
                e.target.innerText = "Copied!";
                setTimeout(() => e.target.innerText = "Copy", 2000);
            }
        });
    }

    async showContext() {
        UI.els.debugModal.classList.add('active');
        UI.els.debugContent.innerText = "Fetching tree...";
        try {
            const res = await fetch('/api/context');
            const data = await res.json();
            UI.els.debugContent.innerText = data.content;
        } catch(e) { UI.els.debugContent.innerText = "Error fetching context."; }
    }

    async handleSend() {
        const text = UI.els.input.value.trim();
        if (!text) return;
        
        if (!this.settings.api_key) {
            alert("Please configure your API Key in Settings.");
            UI.els.settingsModal.classList.add('active');
            return;
        }

        UI.els.input.value = "";
        UI.els.sendBtn.disabled = true;
        UI.els.status.innerText = "Processing...";

        let messagePayload = text;
        if (this.history.length === 0) {
            UI.els.status.innerText = "Reading Repo...";
            try {
                const res = await fetch('/api/context');
                const ctx = await res.json();
                messagePayload = `REPO CONTEXT:\n${ctx.content}\n\nUSER QUERY:\n${text}`;
            } catch (e) { console.error(e); }
        }

        UI.appendMessage("Me", UI.renderFormat(text), true);
        this.history.push({ role: "user", content: messagePayload });

        const responseBody = UI.appendMessage("Maintainer", "", true);
        let fullResponse = "";
        let reasoningBuffer = "";

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    messages: this.history,
                    ...this.settings 
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const chunk = JSON.parse(line);
                        if (chunk.type === 'content') {
                            fullResponse += chunk.payload;
                            let html = UI.renderFormat(fullResponse);
                            if (reasoningBuffer) html = `<div class="reasoning-block">${reasoningBuffer}</div>` + html;
                            responseBody.innerHTML = html;
                        } 
                        else if (chunk.type === 'reasoning') reasoningBuffer += chunk.payload;
                        else if (chunk.type === 'error') {
                            responseBody.innerHTML += `<br><strong>Error:</strong> ${chunk.payload}`;
                        }
                    } catch (e) {}
                }
            }
            this.history.push({ role: "assistant", content: fullResponse });
        } catch (e) {
            responseBody.innerText += `\n[System Error: ${e.message}]`;
        } finally {
            UI.els.sendBtn.disabled = false;
            UI.els.status.innerText = "Ready";
        }
    }
}

new App();