"""
patch_all.py — Combined patch: adds Fundamental Analysis UI + Streaming + Spinner
Run once on the clean 1393-line dashboard.html
"""

PATH = r'c:\Users\Admin\Documents\github\Kod-Bank\server\templates\dashboard.html'

with open(PATH, encoding='utf-8') as f:
    content = f.read()

assert 'fundamentalView' not in content, "Already patched! Restore from git first."

# ═══════════════════════════════════════════════════════════════════
# PART 1 — Fundamental Analysis CSS (inject into extra_head block)
# ═══════════════════════════════════════════════════════════════════
FA_CSS = """
    /* ── Fundamental Analysis ──────────────────────────────────────────── */
    #fundamentalView {
        display: none; height: 100%; overflow: hidden;
        font-family: 'Inter', sans-serif;
    }
    .fa-layout { display: flex; height: 100%; }
    .fa-sidebar {
        width: 280px; min-width: 240px;
        background: rgba(255,255,255,0.03);
        border-right: 1px solid rgba(255,255,255,0.08);
        display: flex; flex-direction: column;
        padding: 24px 16px; gap: 16px; overflow-y: auto;
    }
    .fa-sidebar h3 {
        font-size: 0.78rem; font-weight: 600; color: #64748b;
        text-transform: uppercase; letter-spacing: .08em; margin: 0 0 4px;
    }
    .fa-upload-zone {
        border: 2px dashed rgba(99,102,241,0.4);
        border-radius: 12px; padding: 24px 16px;
        text-align: center; cursor: pointer;
        background: rgba(99,102,241,0.04);
        transition: border-color .2s, background .2s;
    }
    .fa-upload-zone:hover, .fa-upload-zone.dragover {
        border-color: #6366f1; background: rgba(99,102,241,0.1);
    }
    .fa-upload-zone .upload-icon { font-size: 1.6rem; margin-bottom: 8px; }
    .fa-upload-zone p { margin: 0; font-size: 0.82rem; color: #94a3b8; }
    .fa-upload-zone span { font-size: 0.75rem; color: #475569; display: block; margin-top: 4px; }
    #faFileInput { display: none; }
    .fa-upload-btn {
        margin-top: 10px;
        background: linear-gradient(135deg,#6366f1,#4f46e5);
        color: #fff; border: none; border-radius: 8px;
        padding: 8px 20px; font-size: 0.82rem; font-weight: 600;
        cursor: pointer; transition: opacity .2s; width: 100%;
    }
    .fa-upload-btn:hover { opacity: 0.85; }

    /* ── Circular upload spinner ─────────────────────────────────── */
    .fa-upload-progress {
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
    @keyframes faSpinRing { to { transform: rotate(360deg); } }
    .fa-spinner-label {
        font-size: 0.75rem; color: #818cf8;
        text-align: center;
        animation: faLabelPulse 1.5s ease-in-out infinite;
    }
    @keyframes faLabelPulse { 0%,100%{opacity:.5} 50%{opacity:1} }

    .fa-doc-list { flex: 1; display: flex; flex-direction: column; gap: 8px; }
    .fa-doc-item {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 12px 14px;
        display: flex; align-items: flex-start; gap: 10px;
        transition: border-color .2s;
    }
    .fa-doc-item:hover { border-color: rgba(99,102,241,0.4); }
    .fa-doc-icon { font-size: 1.3rem; flex-shrink: 0; }
    .fa-doc-info { flex: 1; min-width: 0; }
    .fa-doc-name { font-size: 0.82rem; font-weight: 600; color: #e2e8f0;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .fa-doc-meta { font-size: 0.72rem; color: #64748b; margin-top: 2px; }
    .fa-doc-del {
        background: none; border: none; color: #475569;
        cursor: pointer; padding: 2px; line-height: 1;
        font-size: 1rem; transition: color .2s; flex-shrink: 0;
    }
    .fa-doc-del:hover { color: #ef4444; }
    .fa-no-docs { text-align: center; color: #475569; font-size: 0.82rem; padding: 20px 0; }
    .fa-chat-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
    .fa-chat-header {
        padding: 20px 28px 14px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        display: flex; align-items: center; gap: 12px;
    }
    .fa-chat-header h2 { margin: 0; font-size: 1rem; font-weight: 600; color: #f1f5f9; }
    .fa-badge {
        font-size: 0.68rem; font-weight: 700;
        background: linear-gradient(135deg,#6366f1,#818cf8);
        color: #fff; padding: 2px 8px; border-radius: 20px;
    }
    .fa-messages {
        flex: 1; overflow-y: auto; padding: 24px 28px;
        display: flex; flex-direction: column; gap: 20px;
        scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.1) transparent;
    }
    .fa-msg { display: flex; gap: 12px; align-items: flex-start; }
    .fa-msg.user { flex-direction: row-reverse; }
    .fa-avatar {
        width: 32px; height: 32px; border-radius: 50%;
        background: linear-gradient(135deg,#6366f1,#818cf8);
        display: flex; align-items: center; justify-content: center;
        font-size: 0.78rem; font-weight: 700; color: #fff; flex-shrink: 0;
    }
    .fa-avatar.user-av { background: linear-gradient(135deg,#0ea5e9,#38bdf8); }
    .fa-bubble {
        max-width: 75%; background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 14px; padding: 14px 18px;
        font-size: 0.88rem; color: #e2e8f0; line-height: 1.6; white-space: pre-wrap;
    }
    .fa-msg.user .fa-bubble {
        background: rgba(99,102,241,0.18);
        border-color: rgba(99,102,241,0.3); color: #c7d2fe;
    }
    .fa-sources { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
    .fa-source-pill {
        font-size: 0.7rem; color: #818cf8;
        background: rgba(99,102,241,0.12);
        border: 1px solid rgba(99,102,241,0.25);
        border-radius: 20px; padding: 3px 10px;
    }
    .fa-empty-state {
        flex: 1; display: flex; flex-direction: column;
        align-items: center; justify-content: center; gap: 12px; color: #475569;
    }
    .fa-empty-state .es-icon { font-size: 2.5rem; }
    .fa-empty-state p { margin: 0; font-size: 0.88rem; text-align: center; max-width: 280px; }
    .fa-thinking { display: flex; align-items: center; gap: 6px; color: #64748b; font-size: 0.82rem; padding: 8px 0; }
    .fa-dots span {
        display: inline-block; width: 6px; height: 6px;
        background: #6366f1; border-radius: 50%;
        animation: faDotBounce 1.2s infinite;
    }
    .fa-dots span:nth-child(2) { animation-delay: .2s; }
    .fa-dots span:nth-child(3) { animation-delay: .4s; }
    @keyframes faDotBounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }

    /* ── Streaming cursor ────────────────────────────────────────── */
    .fa-streaming::after {
        content: '|'; display: inline-block;
        color: #6366f1;
        animation: faCursorBlink 0.8s step-end infinite;
        margin-left: 1px;
    }
    @keyframes faCursorBlink { 0%,100%{opacity:1} 50%{opacity:0} }

    .fa-input-row {
        padding: 16px 28px 20px;
        border-top: 1px solid rgba(255,255,255,0.06);
        display: flex; gap: 10px; align-items: flex-end;
    }
    .fa-input {
        flex: 1; background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 12px; padding: 12px 16px;
        color: #f1f5f9; font-size: 0.9rem;
        font-family: 'Inter', sans-serif;
        resize: none; outline: none; min-height: 46px; max-height: 120px;
        transition: border-color .2s;
    }
    .fa-input:focus { border-color: rgba(99,102,241,0.5); }
    .fa-input::placeholder { color: #475569; }
    .fa-send-btn {
        background: linear-gradient(135deg,#6366f1,#4f46e5);
        border: none; border-radius: 10px; width: 44px; height: 44px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; transition: opacity .2s; color: #fff; flex-shrink: 0;
    }
    .fa-send-btn:hover { opacity: 0.85; }
    .fa-send-btn svg { width: 18px; height: 18px; }
"""

content = content.replace(
    '</style>\n{% endblock %}',
    FA_CSS + '</style>\n{% endblock %}',
    1
)

# ═══════════════════════════════════════════════════════════════════
# PART 2 — navFundamental button (after navAnalytics)
# ═══════════════════════════════════════════════════════════════════
NAV_BTN = """            <button id="navFundamental" class="nav-item" onclick="switchView('fundamental')">
                <i data-lucide="file-text" style="width: 18px; height: 18px;"></i>
                Fundamental AI
            </button>"""

content = content.replace(
    '                Stock Analytics\n            </button>\n\n            <span style="margin-top: 16px">Yesterday</span>',
    '                Stock Analytics\n            </button>\n' + NAV_BTN + '\n\n            <span style="margin-top: 16px">Yesterday</span>'
)

# ═══════════════════════════════════════════════════════════════════
# PART 3 — fundamentalView HTML (after analyticsView)
# ═══════════════════════════════════════════════════════════════════
FA_HTML = """
    <!-- ── Fundamental Analysis View ──────────────────────────────── -->
    <div id="fundamentalView" style="display:none; height:100%; overflow:hidden;">
        <div class="fa-layout">
            <!-- Left: Document Panel -->
            <div class="fa-sidebar">
                <h3>Documents</h3>
                <div class="fa-upload-zone" id="faDropZone" onclick="document.getElementById('faFileInput').click()">
                    <div class="upload-icon">&#128196;</div>
                    <p>Drop a PDF here or click to upload</p>
                    <span>Annual reports, filings, prospectuses</span>
                    <button class="fa-upload-btn" onclick="event.stopPropagation(); document.getElementById('faFileInput').click()">Choose PDF</button>
                </div>
                <input type="file" id="faFileInput" accept=".pdf" onchange="faHandleFile(this.files[0])">
                <div class="fa-upload-progress" id="faUploadProgress">
                    <div class="fa-spinner-ring"></div>
                    <span class="fa-spinner-label">Uploading &amp; indexing PDF&#8230;</span>
                </div>
                <div class="fa-doc-list" id="faDocList">
                    <div class="fa-no-docs" id="faNoDocsMsg">No documents yet.<br>Upload a PDF to get started.</div>
                </div>
            </div>
            <!-- Right: Chat Panel -->
            <div class="fa-chat-panel">
                <div class="fa-chat-header">
                    <h2>Fundamental Analysis AI</h2>
                    <span class="fa-badge">Pinecone &middot; Gemini</span>
                </div>
                <div class="fa-empty-state" id="faEmptyState">
                    <div class="es-icon">&#128269;</div>
                    <p>Upload a financial PDF and ask questions about it &mdash; earnings, revenue, risk factors, and more.</p>
                </div>
                <div class="fa-messages" id="faMessages" style="display:none;"></div>
                <div class="fa-input-row">
                    <textarea class="fa-input" id="faInput" rows="1" placeholder="Ask about your documents..."
                        onkeydown="faInputKeydown(event)"
                        oninput="this.style.height='auto';this.style.height=this.scrollHeight+'px'"></textarea>
                    <button class="fa-send-btn" onclick="faSend()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </div><!-- /fundamentalView -->
"""

content = content.replace(
    '    </div><!-- /analyticsView -->\n\n</div>\n{% endblock %}',
    '    </div><!-- /analyticsView -->\n' + FA_HTML + '\n</div>\n{% endblock %}'
)

# ═══════════════════════════════════════════════════════════════════
# PART 4 — switchView JS: add fundamentalView support
# ═══════════════════════════════════════════════════════════════════
content = content.replace(
    "document.getElementById('analyticsView').style.display = view === 'analytics' ? 'block' : 'none';",
    "document.getElementById('analyticsView').style.display = view === 'analytics' ? 'block' : 'none';\n        document.getElementById('fundamentalView').style.display = view === 'fundamental' ? 'flex' : 'none';"
)
content = content.replace(
    "document.getElementById('navAnalytics').classList.toggle('active', view === 'analytics');",
    "document.getElementById('navAnalytics').classList.toggle('active', view === 'analytics');\n        document.getElementById('navFundamental').classList.toggle('active', view === 'fundamental');"
)

# ═══════════════════════════════════════════════════════════════════
# PART 5 — Main chat streaming (replaces /api/chat fetch)
# ═══════════════════════════════════════════════════════════════════
OLD_MAIN = """                const response = await fetch('/api/chat', {
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

NEW_MAIN = """                // ── Streaming fetch ────────────────────────────────
                const streamRes = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: userMessage, history: messages.slice(1, -1) })
                });
                if (!streamRes.ok) {
                    messages.push({ role: 'model', content: 'Sorry, I encountered an error.' });
                    renderMessages();
                } else {
                    messages.push({ role: 'model', content: '' });
                    renderMessages();
                    let accumulated = '';
                    const reader = streamRes.body.getReader();
                    const decoder = new TextDecoder();
                    let buf = '';
                    // Add streaming cursor to last bubble
                    const allBubbles = document.querySelectorAll('.chat-message.ai .chat-message-content');
                    const lastBubble = allBubbles[allBubbles.length - 1];
                    if (lastBubble) lastBubble.classList.add('streaming');
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
                                    messages[messages.length - 1].content = accumulated;
                                    renderMessages();
                                }
                            } catch {}
                        }
                    }
                    if (lastBubble) lastBubble.classList.remove('streaming');
                }"""

content = content.replace(OLD_MAIN, NEW_MAIN, 1)

# ═══════════════════════════════════════════════════════════════════
# PART 6 — Add Fundamental Analysis JS before </script>{% endblock %}
# ═══════════════════════════════════════════════════════════════════
FA_JS = """
    // ── Fundamental Analysis JS ────────────────────────────────────────────────
    let faHistory = [];
    let faIsThinking = false;

    const faDropZone = document.getElementById('faDropZone');
    faDropZone.addEventListener('dragover', e => { e.preventDefault(); faDropZone.classList.add('dragover'); });
    faDropZone.addEventListener('dragleave', () => faDropZone.classList.remove('dragover'));
    faDropZone.addEventListener('drop', e => {
        e.preventDefault();
        faDropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.name.toLowerCase().endsWith('.pdf')) faHandleFile(file);
        else showToast('Only PDF files are supported.', 'error');
    });

    async function faHandleFile(file) {
        if (!file) return;
        const progress = document.getElementById('faUploadProgress');
        progress.style.display = 'flex';
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch('/api/fundamental/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (!res.ok) { showToast(data.message || 'Upload failed.', 'error'); return; }
            showToast('"' + data.filename + '" indexed \u2014 ' + data.chunk_count + ' chunks.', 'success');
            faRefreshDocs();
            document.getElementById('faEmptyState').style.display = 'none';
            document.getElementById('faMessages').style.display = 'flex';
        } catch (e) {
            showToast('Upload error: ' + e.message, 'error');
        } finally {
            progress.style.display = 'none';
            document.getElementById('faFileInput').value = '';
        }
    }

    async function faRefreshDocs() {
        try {
            const res = await fetch('/api/fundamental/documents');
            const data = await res.json();
            faRenderDocList(data.documents || []);
        } catch {}
    }

    function faRenderDocList(docs) {
        const list = document.getElementById('faDocList');
        const noMsg = document.getElementById('faNoDocsMsg');
        list.querySelectorAll('.fa-doc-item').forEach(el => el.remove());
        if (!docs.length) { noMsg.style.display = 'block'; return; }
        noMsg.style.display = 'none';
        docs.forEach(doc => {
            const item = document.createElement('div');
            item.className = 'fa-doc-item';
            item.innerHTML = `
                <div class="fa-doc-icon">&#128196;</div>
                <div class="fa-doc-info">
                    <div class="fa-doc-name" title="${doc.filename}">${doc.filename}</div>
                    <div class="fa-doc-meta">${doc.page_count} pages &middot; ${doc.chunk_count} chunks</div>
                </div>
                <button class="fa-doc-del" title="Remove" onclick="faDeleteDoc('${doc.filename.replace(/'/g, "\\'")}')">&#x2715;</button>
            `;
            list.appendChild(item);
        });
    }

    async function faDeleteDoc(filename) {
        try {
            await fetch('/api/fundamental/document/' + encodeURIComponent(filename), { method: 'DELETE' });
            showToast('"' + filename + '" removed.', 'success');
            faRefreshDocs();
        } catch (e) { showToast('Delete failed.', 'error'); }
    }

    function faInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); faSend(); }
    }

    // Streaming helpers
    function faAppendMsg(role, text, sources) {
        const msgs = document.getElementById('faMessages');
        const isUser = role === 'user';
        const div = document.createElement('div');
        div.className = 'fa-msg ' + (isUser ? 'user' : 'ai');
        let sourcesHtml = '';
        if (sources && sources.length) {
            sourcesHtml = '<div class="fa-sources">' +
                sources.map(s => `<span class="fa-source-pill">&#128196; ${s.filename}, p.${s.page}</span>`).join('') +
                '</div>';
        }
        div.innerHTML = `
            <div class="fa-avatar ${isUser ? 'user-av' : ''}">${isUser ? 'You' : 'AI'}</div>
            <div><div class="fa-bubble">${text}</div>${sourcesHtml}</div>
        `;
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
        return div;
    }

    function faAppendStreamingBubble() {
        const msgs = document.getElementById('faMessages');
        const div = document.createElement('div');
        div.className = 'fa-msg ai';
        div.innerHTML = '<div class="fa-avatar">AI</div><div><div class="fa-bubble fa-streaming" data-bubble></div></div>';
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
        return div;
    }

    function faShowThinking(show) {
        const existing = document.getElementById('faThinkingIndicator');
        if (existing) existing.remove();
        if (!show) return;
        const msgs = document.getElementById('faMessages');
        const div = document.createElement('div');
        div.id = 'faThinkingIndicator';
        div.className = 'fa-thinking';
        div.innerHTML = '<div class="fa-dots"><span></span><span></span><span></span></div> Analyzing documents...';
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
    }

    async function faSend() {
        if (faIsThinking) return;
        const input = document.getElementById('faInput');
        const question = input.value.trim();
        if (!question) return;
        input.value = '';
        input.style.height = 'auto';
        document.getElementById('faEmptyState').style.display = 'none';
        document.getElementById('faMessages').style.display = 'flex';
        faAppendMsg('user', question, null);
        faHistory.push({ role: 'user', content: question });
        faIsThinking = true;
        faShowThinking(true);
        try {
            const res = await fetch('/api/fundamental/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: question, history: faHistory }),
            });

            // Plain JSON short-circuit (no docs uploaded yet)
            const ct = res.headers.get('content-type') || '';
            if (ct.includes('application/json')) {
                const data = await res.json();
                faShowThinking(false);
                faAppendMsg('ai', res.ok ? data.response : ('\u26a0\ufe0f ' + (data.message || 'Error')), data.sources || []);
                if (res.ok) faHistory.push({ role: 'model', content: data.response });
                return;
            }

            // SSE streaming
            faShowThinking(false);
            const msgEl = faAppendStreamingBubble();
            const bubble = msgEl.querySelector('[data-bubble]');
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
                            bubble.textContent = accumulated;
                            msgEl.scrollIntoView({ block: 'end' });
                        }
                        if (evt.sources) sources = evt.sources;
                    } catch {}
                }
            }
            // Done streaming — remove cursor, add sources
            bubble.classList.remove('fa-streaming');
            if (sources.length) {
                const srcDiv = document.createElement('div');
                srcDiv.className = 'fa-sources';
                srcDiv.innerHTML = sources.map(s => `<span class="fa-source-pill">&#128196; ${s.filename}, p.${s.page}</span>`).join('');
                bubble.parentElement.appendChild(srcDiv);
            }
            faHistory.push({ role: 'model', content: accumulated });
        } catch (e) {
            faShowThinking(false);
            faAppendMsg('ai', '\u26a0\ufe0f Network error \u2014 please check your connection.', null);
        } finally {
            faIsThinking = false;
        }
    }

    // Load docs on page ready
    faRefreshDocs();
"""

content = content.replace(
    '\n</script>\n{% endblock %}',
    FA_JS + '\n</script>\n{% endblock %}'
)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

with open(PATH, encoding='utf-8') as f:
    lines = f.readlines()

joined = ''.join(lines)
print(f'Done! {len(lines)} lines')
checks = [
    ('FA CSS',          'fa-spinner-ring'),
    ('NavFundamental',  'navFundamental'),
    ('FA HTML',         'fundamentalView'),
    ('SwitchView fix',  "view === 'fundamental'"),
    ('Main streaming',  'streamRes'),
    ('FA streaming',    'faAppendStreamingBubble'),
    ('FA JS complete',  'faRefreshDocs'),
]
for label, needle in checks:
    print(f'  {"OK  " if needle in joined else "MISS"} {label}')
