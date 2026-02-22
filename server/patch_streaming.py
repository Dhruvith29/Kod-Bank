"""
patch_dashboard_streaming.py
Adds:
  1. Circular upload spinner CSS (replaces fa-uploading CSS)
  2. Main chat streaming (replaces /api/chat fetch block)
  3. FA chat streaming (replaces faSend fetch block)
"""

PATH = r'c:\Users\Admin\Documents\github\Kod-Bank\server\templates\dashboard.html'

with open(PATH, encoding='utf-8') as f:
    content = f.read()

# ─── 1. Replace .fa-uploading CSS with animated circular spinner ──────────────
OLD_UPLOADING_CSS = '''.fa-upload-progress {
        display: none; margin-top: 10px; font-size: 0.78rem;
        color: #818cf8; text-align: center;
    }'''

NEW_SPINNER_CSS = '''.fa-upload-progress {
        display: none; margin-top: 12px;
        flex-direction: column; align-items: center; gap: 10px;
    }
    .fa-spinner-ring {
        width: 44px; height: 44px;
        border-radius: 50%;
        border: 3px solid rgba(99,102,241,0.2);
        border-top-color: #6366f1;
        animation: faSpinRing 0.85s linear infinite;
    }
    @keyframes faSpinRing {
        to { transform: rotate(360deg); }
    }
    .fa-spinner-label {
        font-size: 0.75rem; color: #818cf8;
        text-align: center; animation: faLabelPulse 1.5s ease-in-out infinite;
    }
    @keyframes faLabelPulse {
        0%, 100% { opacity: 0.5; }
        50%       { opacity: 1;   }
    }'''

content = content.replace(OLD_UPLOADING_CSS, NEW_SPINNER_CSS, 1)

# ─── 2. Replace the fa-upload-progress HTML with spinner markup ───────────────
OLD_PROGRESS_HTML = '                <div class="fa-upload-progress" id="faUploadProgress">&#9203; Uploading &amp; indexing...</div>'
NEW_PROGRESS_HTML = '''                <div class="fa-upload-progress" id="faUploadProgress" style="display:none;">
                    <div class="fa-spinner-ring"></div>
                    <span class="fa-spinner-label">Uploading &amp; indexing PDF&#8230;</span>
                </div>'''
content = content.replace(OLD_PROGRESS_HTML, NEW_PROGRESS_HTML, 1)

# ─── 3. faHandleFile: show spinner (flex not block) ──────────────────────────
content = content.replace(
    "progress.style.display = 'block';",
    "progress.style.display = 'flex';",
    1
)

# ─── 4. Replace main chat fetch block with streaming version ──────────────────
OLD_MAIN_CHAT = """                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: userMessage,
                        history: messages.slice(1, -1)
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    messages.push({ role: 'model', content: data.response });
                } else {
                    messages.push({ role: 'model', content: 'Sorry, I encountered an error. ' + (data.message || '') });
                }"""

NEW_MAIN_CHAT = """                // ── Streaming fetch (SSE) ──────────────────────────────
                const streamRes = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: userMessage, history: messages.slice(1, -1) })
                });
                if (!streamRes.ok) {
                    messages.push({ role: 'model', content: 'Sorry, I encountered an error.' });
                } else {
                    // Add a placeholder message
                    messages.push({ role: 'model', content: '' });
                    renderMessages();
                    let accumulated = '';
                    const reader = streamRes.body.getReader();
                    const decoder = new TextDecoder();
                    let buf = '';
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        buf += decoder.decode(value, { stream: true });
                        const lines = buf.split('\\n');
                        buf = lines.pop(); // keep incomplete line
                        for (const line of lines) {
                            if (!line.startsWith('data: ')) continue;
                            const payload = line.slice(6).trim();
                            if (payload === '[DONE]') break;
                            try {
                                const evt = JSON.parse(payload);
                                if (evt.token) {
                                    accumulated += evt.token;
                                    messages[messages.length - 1].content = accumulated;
                                    renderMessages();
                                }
                            } catch {}
                        }
                    }
                }"""

content = content.replace(OLD_MAIN_CHAT, NEW_MAIN_CHAT, 1)

# ─── 5. Replace faSend fetch block with streaming version ─────────────────────
OLD_FA_SEND = """        try {
            const res = await fetch('/api/fundamental/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: question, history: faHistory }),
            });
            const data = await res.json();
            faShowThinking(false);
            if (!res.ok) {
                faAppendMsg('ai', '&#9888;&#65039; ' + (data.message || 'Something went wrong.'), null);
            } else {
                faAppendMsg('ai', data.response, data.sources);
                faHistory.push({ role: 'model', content: data.response });
            }
        } catch (e) {
            faShowThinking(false);
            faAppendMsg('ai', '&#9888;&#65039; Network error \\u2014 please check your connection.', null);
        } finally {
            faIsThinking = false;
        }"""

NEW_FA_SEND = """        try {
            const res = await fetch('/api/fundamental/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: question, history: faHistory }),
            });

            // Non-streaming short-circuit (e.g. "no docs yet")
            const contentType = res.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                const data = await res.json();
                faShowThinking(false);
                if (!res.ok) {
                    faAppendMsg('ai', '\\u26a0\\ufe0f ' + (data.message || 'Something went wrong.'), null);
                } else {
                    faAppendMsg('ai', data.response, data.sources || []);
                    faHistory.push({ role: 'model', content: data.response });
                }
                return;
            }

            // ── SSE streaming response ─────────────────────────────────────
            faShowThinking(false);
            const msgEl = faAppendStreamingMsg('ai');
            let accumulated = '';
            let sources = [];

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buf = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buf += decoder.decode(value, { stream: true });
                const lines = buf.split('\\n');
                buf = lines.pop();
                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    const payload = line.slice(6).trim();
                    if (payload === '[DONE]') break;
                    try {
                        const evt = JSON.parse(payload);
                        if (evt.token) {
                            accumulated += evt.token;
                            faBubbleSetText(msgEl, accumulated);
                        }
                        if (evt.sources) { sources = evt.sources; }
                    } catch {}
                }
            }
            faRemoveCursor(msgEl);
            faAttachSources(msgEl, sources);
            faHistory.push({ role: 'model', content: accumulated });
        } catch (e) {
            faShowThinking(false);
            faAppendMsg('ai', '\\u26a0\\ufe0f Network error \\u2014 please check your connection.', null);
        } finally {
            faIsThinking = false;
        }"""

content = content.replace(OLD_FA_SEND, NEW_FA_SEND, 1)

# ─── 6. Add helper functions before faSend ────────────────────────────────────
FA_HELPERS = """
    // Streaming helpers for FA chat
    function faAppendStreamingMsg(role) {
        const msgs = document.getElementById('faMessages');
        const div = document.createElement('div');
        div.className = 'fa-msg ' + (role === 'user' ? 'user' : 'ai');
        div.innerHTML = `
            <div class="fa-avatar">AI</div>
            <div>
                <div class="fa-bubble" data-bubble></div>
            </div>
        `;
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
        return div;
    }

    function faBubbleSetText(msgEl, text) {
        const bubble = msgEl.querySelector('[data-bubble]');
        if (bubble) {
            bubble.textContent = text;
            // blinking cursor
            bubble.classList.add('fa-streaming');
        }
        const msgs = document.getElementById('faMessages');
        msgs.scrollTop = msgs.scrollHeight;
    }

    function faRemoveCursor(msgEl) {
        const bubble = msgEl.querySelector('[data-bubble]');
        if (bubble) bubble.classList.remove('fa-streaming');
    }

    function faAttachSources(msgEl, sources) {
        if (!sources || !sources.length) return;
        const container = msgEl.querySelector('div > div') || msgEl.querySelector('div');
        const srcDiv = document.createElement('div');
        srcDiv.className = 'fa-sources';
        srcDiv.innerHTML = sources.map(s => `<span class="fa-source-pill">&#128196; ${s.filename}, p.${s.page}</span>`).join('');
        if (container) container.appendChild(srcDiv);
    }

"""

content = content.replace(
    '    async function faSend() {',
    FA_HELPERS + '    async function faSend() {',
    1
)

# ─── 7. Add fa-streaming cursor CSS ──────────────────────────────────────────
FA_CURSOR_CSS = """
    .fa-streaming::after {
        content: '|';
        display: inline-block;
        color: #6366f1;
        animation: faCursorBlink 0.8s step-end infinite;
        margin-left: 1px;
    }
    @keyframes faCursorBlink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    /* Main chat streaming cursor */
    .chat-message-content.streaming::after {
        content: '|';
        display: inline-block;
        color: #3b82f6;
        animation: faCursorBlink 0.8s step-end infinite;
        margin-left: 1px;
    }
"""

content = content.replace(
    '.fa-dots span:nth-child(3) { animation-delay: .4s; }',
    '.fa-dots span:nth-child(3) { animation-delay: .4s; }' + FA_CURSOR_CSS,
    1
)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

with open(PATH, encoding='utf-8') as f:
    lines = f.readlines()

print(f'Done! {len(lines)} lines.')

# Quick checks
joined = ''.join(lines)
checks = [
    ('Spinner CSS', 'fa-spinner-ring'),
    ('Spinner HTML', 'fa-spinner-ring'),
    ('Streaming CSS', 'fa-streaming'),
    ('Main chat stream', 'streamRes'),
    ('FA helpers', 'faAppendStreamingMsg'),
    ('FA stream', 'SSE streaming response'),
]
for label, needle in checks:
    print(f'  {"OK" if needle in joined else "MISSING"} {label}')
