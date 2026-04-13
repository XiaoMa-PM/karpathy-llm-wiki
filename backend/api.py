"""
API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from wiki_engine import get_engine

router = APIRouter()


class IngestRequest(BaseModel):
    content: str
    source_name: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


@router.post("/ingest")
async def ingest(req: IngestRequest):
    """摄入原始数据"""
    engine = get_engine()
    result = engine.ingest(req.content, req.source_name)
    return {"message": f"成功摄入: {result['filename']}", **result}


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
