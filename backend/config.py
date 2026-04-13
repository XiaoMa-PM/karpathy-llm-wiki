"""
LLM 个人知识库配置
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
WIKI_DIR = DATA_DIR / "wiki"

# LLM API 配置（支持 OpenAI 兼容格式的任意 LLM）
# MiniMax
API_KEY = os.getenv("MINIMAX_API_KEY", os.getenv("OPENAI_API_KEY", "your-api-key-here"))
BASE_URL = os.getenv("MINIMAX_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://api.minimax.chat/v1"))
MODEL = os.getenv("MINIMAX_MODEL", os.getenv("OPENAI_MODEL", "MiniMax-M2.7"))

# Wiki 配置
WIKI_INDEX_FILE = WIKI_DIR / "index.json"
CONCEPTS_DIR = WIKI_DIR / "concepts"
ARTICLES_DIR = WIKI_DIR / "articles"
