# LLM Wiki - 个人知识库系统

基于 LLM 的个人知识库系统，支持数据摄入、Wiki 编译和智能问答。灵感来源于 [LLM Knowledge Bases](https://simonwillison.net/2025/Nov/17/llm-knowledge-bases/) 教程。

## 核心思路

```
原始数据 (文章/笔记/文档)
    ↓ 数据摄入
raw/ 目录
    ↓ LLM 编译
结构化 .md Wiki
    ↓ 智能问答 / 健康检查
知识增长 · 持续积累
```

## 功能特性

- **📥 数据摄入** - 粘贴文章、笔记或任意文本，自动保存到本地 raw 目录
- **📚 Wiki 编译** - 调用 LLM 将原始数据编译成带摘要、反向链接和概念分类的结构化 Wiki
- **❓ 智能问答** - 基于 Wiki 内容进行问答，LLM 会自动搜索相关内容给出答案
- **🔍 Wiki 浏览** - 查看和搜索已编译的 Wiki 内容
- **✨ 健康检查** - 自动发现 Wiki 中的不一致数据和缺失内容

## 技术栈

- **后端**: FastAPI + OpenAI SDK（兼容任何 OpenAI 格式的 LLM）
- **前端**: 原生 HTML/CSS/JS（零依赖，响应式设计）
- **LLM**: MiniMax M2.7（可轻松切换为 OpenAI / Claude / 本地模型）

## 项目结构

```
LLM_WIKI_DATAD/
├── backend/
│   ├── main.py           # FastAPI 主入口
│   ├── api.py            # API 路由
│   ├── wiki_engine.py    # Wiki 引擎（核心 LLM 逻辑）
│   ├── config.py         # 配置（模型、路径）
│   └── requirements.txt  # Python 依赖
├── frontend/
│   ├── index.html        # 主页面
│   ├── style.css         # 样式
│   └── app.js            # 前端逻辑
├── data/
│   ├── raw/              # 原始数据（摄入的内容）
│   └── wiki/             # 编译后的 Wiki 文件
├── .gitignore
└── README.md
```

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd LLM_WIKI_DATAD
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置 API Key

支持任何 OpenAI 兼容格式的 LLM。复制配置示例文件并填入你的 Key：

```bash
cd backend
copy .env.example .env
# 然后编辑 .env 填入真实 API Key
```

或直接设置环境变量：

```bash
# MiniMax
set MINIMAX_API_KEY=your-minimax-key
set MINIMAX_BASE_URL=https://api.minimax.chat/v1
set MINIMAX_MODEL=MiniMax-M2.7

# OpenAI
set OPENAI_API_KEY=your-openai-key
set OPENAI_BASE_URL=https://api.openai.com/v1
set OPENAI_MODEL=gpt-4o

# 本地 Ollama
set OPENAI_API_KEY=not-needed
set OPENAI_BASE_URL=http://localhost:11434/v1
set OPENAI_MODEL=llama3
```

### 4. 启动服务

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 打开前端

浏览器访问 **http://localhost:8000**

## 使用流程

1. **摄入数据** - 在"数据摄入"页面粘贴文章内容，填入来源名称，提交
2. **编译 Wiki** - 点击"编译 Wiki"，LLM 会分析所有原始数据，生成结构化 Wiki
3. **开始问答** - 在"智能问答"页面提问，LLM 会基于 Wiki 内容回答
4. **浏览 Wiki** - 在"Wiki 浏览"页面查看所有已编译的文档和搜索内容

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/ingest` | 摄入原始数据 |
| `POST` | `/api/compile` | 编译 Wiki |
| `POST` | `/api/chat` | 智能问答 |
| `GET` | `/api/wiki/list` | 列出 Wiki 文件 |
| `GET` | `/api/wiki/search` | 搜索 Wiki 内容 |

## 自定义配置

编辑 `backend/.env` 或 `backend/config.py` 修改：

```python
# 数据目录
RAW_DIR = DATA_DIR / "raw"
WIKI_DIR = DATA_DIR / "wiki"

# LLM 参数
MINIMAX_MODEL = "MiniMax-M2.7"
MINIMAX_TEMPERATURE = 0.7
```

## 扩展思路

- 接入 Obsidian 作为前端 IDE（配合 Marp 渲染幻灯片）
- 添加文件监听，自动摄入特定目录的新文件
- 接入 Web Searcher 实现联网补全缺失数据
- 合成数据生成 + 微调，让 LLM"记住"知识

## License

MIT
