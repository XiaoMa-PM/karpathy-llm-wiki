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

// URL 摄入（小红书等）
async function ingestUrl() {
    const url = document.getElementById('url-input').value.trim();
    const statusDiv = document.getElementById('url-status');

    if (!url) {
        statusDiv.className = 'status error';
        statusDiv.textContent = '请输入链接';
        return;
    }

    statusDiv.className = 'status';
    statusDiv.innerHTML = '<div class="spinner"></div>正在抓取内容...\n（可能需要10-30秒）';

    try {
        const response = await fetch(`${API_BASE}/ingest/url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await response.json();
        if (response.ok && data.success) {
            statusDiv.className = 'status success';
            statusDiv.textContent = `✓ ${data.message}`;
            document.getElementById('url-input').value = '';
        } else {
            statusDiv.className = 'status error';
            statusDiv.textContent = `✗ ${data.message || '抓取失败'}`;
        }
    } catch (error) {
        statusDiv.className = 'status error';
        statusDiv.textContent = `✗ ${error.message}`;
    }
}

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

// ============= 数据维护 =============

async function loadRawStats() {
    try {
        const response = await fetch(`${API_BASE}/raw/stats`);
        const data = await response.json();
        if (response.ok) {
            const sizeMB = (data.total_size / 1024).toFixed(1);
            document.getElementById('stats-bar').innerHTML = `
                <span class="stat-item">📄 共 ${data.total_files} 个文件</span>
                <span class="stat-item">💾 ${sizeMB} KB</span>
                <span class="stat-item">小红书: ${data.platforms.xiaohongshu || 0}</span>
                <span class="stat-item">知乎: ${data.platforms.zhihu || 0}</span>
                <span class="stat-item">微博: ${data.platforms.weibo || 0}</span>
                <span class="stat-item">B站: ${data.platforms.bilibili || 0}</span>
            `;
        }
    } catch (error) {
        console.error('Stats error:', error);
    }
}

async function loadRawList() {
    const listDiv = document.getElementById('raw-list');
    listDiv.innerHTML = '<div class="spinner"></div>加载中...';

    try {
        const response = await fetch(`${API_BASE}/raw/list`);
        const data = await response.json();
        if (response.ok) {
            if (data.files.length === 0) {
                listDiv.innerHTML = '<p>暂无数据</p>';
                return;
            }
            let html = '<table class="raw-table"><thead><tr><th width="40"><input type="checkbox" id="select-all" onchange="toggleSelectAll()"></th><th>标题</th><th width="100">大小</th><th width="100">操作</th></tr></thead><tbody>';
            data.files.forEach(f => {
                const sizeKB = (f.size / 1024).toFixed(1);
                const preview = escapeHtml(f.preview).substring(0, 80);
                html += `<tr>
                    <td><input type="checkbox" class="raw-checkbox" value="${escapeHtml(f.filename)}"></td>
                    <td>
                        <strong>${escapeHtml(f.title)}</strong><br>
                        <small style="color:#888">${preview}...</small>
                    </td>
                    <td>${sizeKB} KB</td>
                    <td>
                        <button onclick="deleteRaw('${escapeHtml(f.filename)}')" class="small-btn">删除</button>
                    </td>
                </tr>`;
            });
            html += '</tbody></table>';
            listDiv.innerHTML = html;
        }
    } catch (error) {
        listDiv.innerHTML = `<p style="color:red">✗ ${error.message}</p>`;
    }
}

function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('.raw-checkbox');
    const selectAll = document.getElementById('select-all');
    checkboxes.forEach(cb => cb.checked = selectAll.checked);
}

async function deleteRaw(filename) {
    if (!confirm(`确定要删除 "${filename}" 吗？`)) return;
    try {
        const response = await fetch(`${API_BASE}/raw/${encodeURIComponent(filename)}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok && data.success) {
            alert(data.message);
            loadRawList();
            loadRawStats();
        } else {
            alert('删除失败: ' + (data.message || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

async function deleteSelectedRaw() {
    const checkboxes = document.querySelectorAll('.raw-checkbox:checked');
    if (checkboxes.length === 0) {
        alert('请先选择要删除的文件');
        return;
    }
    if (!confirm(`确定要删除选中的 ${checkboxes.length} 个文件吗？`)) return;

    let deleted = 0;
    for (const cb of checkboxes) {
        try {
            await fetch(`${API_BASE}/raw/${encodeURIComponent(cb.value)}`, { method: 'DELETE' });
            deleted++;
        } catch (e) {}
    }
    alert(`已删除 ${deleted} 个文件`);
    loadRawList();
    loadRawStats();
}

async function clearAllRaw() {
    if (!confirm('⚠️ 确定要清空所有原始数据吗？此操作不可恢复！')) return;
    if (!confirm('再次确认：清空后所有摄入的原始数据将被永久删除！')) return;

    try {
        const response = await fetch(`${API_BASE}/raw`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) {
            alert(data.message);
            loadRawList();
            loadRawStats();
        }
    } catch (error) {
        alert('清空失败: ' + error.message);
    }
}

// 初始化
refreshWiki();
loadRawStats();
