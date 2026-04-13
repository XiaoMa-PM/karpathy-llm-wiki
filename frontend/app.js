const API_BASE = '/api';

// 标签页切换
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`panel-${tab.dataset.tab}`).classList.add('active');
    });
});

// 数据摄入
async function ingestData() {
    const content = document.getElementById('raw-content').value;
    const sourceName = document.getElementById('source-name').value || '未命名';
    const statusDiv = document.getElementById('ingest-status');

    if (!content.trim()) {
        statusDiv.className = 'status error';
        statusDiv.textContent = '请输入内容';
        return;
    }

    statusDiv.className = 'status';
    statusDiv.innerHTML = '<div class="spinner"></div>摄入中...';

    try {
        const response = await fetch(`${API_BASE}/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, source_name: sourceName })
        });
        const data = await response.json();
        if (response.ok) {
            statusDiv.className = 'status success';
            statusDiv.textContent = `✓ ${data.message}`;
            document.getElementById('raw-content').value = '';
            document.getElementById('source-name').value = '';
        } else {
            throw new Error(data.detail || '摄入失败');
        }
    } catch (error) {
        statusDiv.className = 'status error';
        statusDiv.textContent = `✗ ${error.message}`;
    }
}

// 编译 Wiki
async function compileWiki() {
    const outputDiv = document.getElementById('compile-output');
    outputDiv.innerHTML = '<div class="spinner"></div>编译中...\n（这可能需要几分钟，请耐心等待）';

    try {
        const response = await fetch(`${API_BASE}/compile`, {
            method: 'POST'
        });
        const data = await response.json();
        if (response.ok) {
            outputDiv.innerHTML = marked.parse(data.result || '✓ 编译完成！');
        } else {
            throw new Error(data.detail || '编译失败');
        }
    } catch (error) {
        outputDiv.innerHTML = `✗ ${error.message}`;
    }
}

// 问答
let chatHistory = [];

async function askQuestion() {
    const input = document.getElementById('question-input');
    const question = input.value.trim();
    if (!question) return;

    const messagesDiv = document.getElementById('chat-messages');

    // 添加用户消息
    messagesDiv.innerHTML += `
        <div class="message user">
            <div class="role">你</div>
            <div>${escapeHtml(question)}</div>
        </div>
    `;
    input.value = '';
    chatHistory.push({ role: 'user', content: question });

    // 添加加载状态
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.innerHTML = '<div class="role">AI</div><div class="spinner"></div>思考中...';
    messagesDiv.appendChild(loadingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: chatHistory })
        });
        const data = await response.json();
        chatHistory.push({ role: 'assistant', content: data.response });

        loadingDiv.innerHTML = `<div class="role">AI</div><div>${marked.parse(data.response)}</div>`;
    } catch (error) {
        loadingDiv.innerHTML = `<div class="role">AI</div><div style="color:red">✗ ${error.message}</div>`;
    }
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        askQuestion();
    }
}

// Wiki 浏览
async function refreshWiki() {
    const contentDiv = document.getElementById('wiki-content');
    contentDiv.innerHTML = '<div class="spinner"></div>加载中...';

    try {
        const response = await fetch(`${API_BASE}/wiki/list`);
        const data = await response.json();
        if (response.ok) {
            let html = `## Wiki 文件列表\n\n共 ${data.files.length} 个文件：\n\n`;
            data.files.forEach(f => {
                html += `- **${f.title}** (${f.path})\n`;
            });
            contentDiv.innerHTML = marked.parse(html);
        } else {
            throw new Error(data.detail || '加载失败');
        }
    } catch (error) {
        contentDiv.innerHTML = `<p style="color:red">✗ ${error.message}</p>`;
    }
}

async function searchWiki() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return refreshWiki();

    const contentDiv = document.getElementById('wiki-content');
    contentDiv.innerHTML = '<div class="spinner"></div>搜索中...';

    try {
        const response = await fetch(`${API_BASE}/wiki/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (response.ok) {
            let html = `## 搜索结果：${escapeHtml(query)}\n\n`;
            if (data.results.length === 0) {
                html += '没有找到相关内容。';
            } else {
                data.results.forEach(r => {
                    html += `### ${r.title}\n${r.snippet}\n\n`;
                });
            }
            contentDiv.innerHTML = marked.parse(html);
        } else {
            throw new Error(data.detail || '搜索失败');
        }
    } catch (error) {
        contentDiv.innerHTML = `<p style="color:red">✗ ${error.message}</p>`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 初始化
refreshWiki();
