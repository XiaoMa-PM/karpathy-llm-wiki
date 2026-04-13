"""
API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from wiki_engine import get_engine
from scraper import fetch_content

router = APIRouter()


class IngestRequest(BaseModel):
    content: str
    source_name: str


class IngestUrlRequest(BaseModel):
    url: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


@router.post("/ingest")
async def ingest(req: IngestRequest):
    """摄入原始数据（文本）"""
    engine = get_engine()
    result = engine.ingest(req.content, req.source_name)
    return {"message": f"成功摄入: {result['filename']}", **result}


@router.post("/ingest/url")
async def ingest_url(req: IngestUrlRequest):
    """从 URL 摄入内容（支持多平台）"""
    url = req.url.strip()

    # 抓取内容
    result = await fetch_content(url)

    if "error" in result:
        return {"success": False, "message": result["error"]}

    # 抓取成功，摄入到 wiki
    engine = get_engine()
    content = f"# {result['title']}\n\n**作者**: {result.get('author', '未知')}\n**来源**: {url}\n\n---\n\n{result['content']}"
    ingest_result = engine.ingest(content, result['title'])

    return {
        "success": True,
        "message": f"成功抓取并摄入: {result['title']}",
        "filename": ingest_result['filename']
    }


@router.post("/compile")
async def compile():
    """编译 Wiki"""
    engine = get_engine()
    result = engine.compile_wiki()
    return {"result": result}


@router.post("/chat")
async def chat(req: ChatRequest):
    """智能问答"""
    engine = get_engine()
    messages = [m.model_dump() for m in req.messages]
    response = engine.chat(messages)
    return {"response": response}


@router.get("/wiki/list")
async def list_wiki():
    """列出 Wiki 文件"""
    engine = get_engine()
    files = engine.list_wiki()
    return {"files": files}


@router.get("/wiki/search")
async def search_wiki(q: str):
    """搜索 Wiki"""
    engine = get_engine()
    results = engine.search_wiki(q)
    return {"results": results}
