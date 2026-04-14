"""
Wiki 引擎 - 核心 LLM 调用和 Wiki 管理逻辑
"""
import json
import os
import re
from pathlib import Path
from datetime import datetime
from openai import OpenAI

from config import (
    API_KEY, BASE_URL, MODEL,
    RAW_DIR, WIKI_DIR, WIKI_INDEX_FILE,
    CONCEPTS_DIR, ARTICLES_DIR
)


class WikiEngine:
    def __init__(self):
        self.client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )
        self.model = MODEL
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保目录存在"""
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        WIKI_DIR.mkdir(parents=True, exist_ok=True)
        CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
        ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    def ingest(self, content: str, source_name: str) -> dict:
        """摄入原始数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^\w\u4e00-\u9fff-]', '_', source_name)[:50]
        filename = f"{timestamp}_{safe_name}.md"
        filepath = RAW_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {source_name}\n\n")
            f.write(f"**摄入时间**: {datetime.now().isoformat()}\n\n")
            f.write(content)

        return {
            "filename": filename,
            "path": str(filepath),
            "size": len(content)
        }

    def compile_wiki(self) -> str:
        """编译 Wiki - 将原始数据转换为结构化 wiki"""
        # 1. 读取所有原始数据
        raw_files = list(RAW_DIR.glob("*.md"))
        if not raw_files:
            return "没有原始数据需要编译"

        raw_contents = []
        for f in raw_files:
            with open(f, 'r', encoding='utf-8') as fp:
                content = fp.read()
                raw_contents.append({
                    "filename": f.name,
                    "content": content[:5000]  # 限制长度
                })

        # 2. 生成系统提示
        system_prompt = """你是一个知识库管理助手，负责将原始数据编译成结构化的 Wiki。

请分析提供的原始数据，然后：
1. 为每个文档生成摘要
2. 提取关键概念
3. 识别概念之间的关联
4. 生成 Wiki 结构建议

请以 Markdown 格式输出编译结果。"""

        # 3. 构建用户消息
        docs_text = "\n\n---\n\n".join([f"## {d['filename']}\n{d['content']}" for d in raw_contents])

        # 4. 调用 LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请编译以下原始文档：\n\n{docs_text}"}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        result = response.choices[0].message.content

        # 5. 保存编译结果到 index.md
        index_path = WIKI_DIR / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(f"# Wiki 索引\n\n**编译时间**: {datetime.now().isoformat()}\n\n")
            f.write("## 概念\n\n")
            f.write("## 文章\n\n")
            f.write("---\n\n")
            f.write(result)

        # 6. 更新索引文件
        self._update_index(raw_files)

        return result

    def _update_index(self, raw_files):
        """更新 Wiki 索引"""
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "raw_files": [f.name for f in raw_files],
            "wiki_files": [str(f) for f in WIKI_DIR.glob("**/*.md")]
        }
        with open(WIKI_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def chat(self, messages: list) -> str:
        """智能问答"""
        # 读取 Wiki 内容作为上下文
        wiki_context = self._get_wiki_context()

        system_prompt = f"""你是一个知识库问答助手。请根据提供的 Wiki 内容回答用户问题。

如果 Wiki 中没有相关信息，请如实告知。

## Wiki 内容
{wiki_context}
"""

        # 调用 LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages
            ],
            temperature=0.7,
            max_tokens=2000
        )

        return response.choices[0].message.content

    def _get_wiki_context(self) -> str:
        """获取 Wiki 内容作为上下文"""
        wiki_files = list(WIKI_DIR.glob("**/*.md"))
        if not wiki_files:
            # 如果没有 wiki，返回 raw 内容
            raw_files = list(RAW_DIR.glob("*.md"))
            contents = []
            for f in raw_files[:5]:  # 限制最多5个文件
                with open(f, 'r', encoding='utf-8') as fp:
                    contents.append(fp.read()[:2000])
            return "\n\n---\n\n".join(contents) if contents else "（暂无 Wiki 内容）"
        else:
            # 返回所有 wiki 文件内容
            all_content = []
            for f in wiki_files[:10]:
                with open(f, 'r', encoding='utf-8') as fp:
                    all_content.append(fp.read()[:3000])
            return "\n\n---\n\n".join(all_content)

    def list_wiki(self) -> list:
        """列出 Wiki 文件"""
        wiki_files = list(WIKI_DIR.glob("**/*.md"))
        return [
            {
                "path": str(f.relative_to(WIKI_DIR)),
                "title": self._extract_title(f),
                "size": f.stat().st_size
            }
            for f in wiki_files
        ]

    def _extract_title(self, filepath: Path) -> str:
        """从文件提取标题"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('# '):
                    return first_line[2:]
                return filepath.stem
        except:
            return filepath.stem

    def search_wiki(self, query: str) -> list:
        """搜索 Wiki 内容"""
        results = []
        wiki_files = list(WIKI_DIR.glob("**/*.md"))

        for f in wiki_files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    if query.lower() in content.lower():
                        # 提取匹配片段
                        idx = content.lower().find(query.lower())
                        start = max(0, idx - 100)
                        end = min(len(content), idx + 200)
                        snippet = content[start:end]

                        results.append({
                            "path": str(f.relative_to(WIKI_DIR)),
                            "title": self._extract_title(f),
                            "snippet": "..." + snippet + "..."
                        })
            except:
                continue

        return results

    # ============= Raw 数据维护 =============

    def list_raw(self) -> list:
        """列出所有原始数据文件"""
        files = list(RAW_DIR.glob("*.md"))
        result = []
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    # 提取标题（第一个 # 后面那段）
                    title = f.stem
                    for line in content.split('\n'):
                        if line.startswith('# '):
                            title = line[2:].strip()
                            break
                    # 提取来源 URL（如果有）
                    url_match = re.search(r'来源.*?(https?://[^\s]+)', content)
                    url = url_match.group(1) if url_match else None
                    # 内容预览（前200字符）
                    preview = content[:200].replace('\n', ' ').strip()

                    result.append({
                        "filename": f.name,
                        "title": title,
                        "size": f.stat().st_size,
                        "url": url,
                        "preview": preview + "..." if len(content) > 200 else preview
                    })
            except:
                continue
        return result

    def delete_raw(self, filename: str) -> bool:
        """删除指定原始数据文件"""
        filepath = RAW_DIR / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def delete_all_raw(self) -> int:
        """清空所有原始数据文件"""
        files = list(RAW_DIR.glob("*.md"))
        count = 0
        for f in files:
            try:
                f.unlink()
                count += 1
            except:
                continue
        return count

    def get_raw_stats(self) -> dict:
        """获取原始数据统计"""
        files = list(RAW_DIR.glob("*.md"))
        total_size = sum(f.stat().st_size for f in files)
        # 统计各平台数量
        platforms = {"xiaohongshu": 0, "zhihu": 0, "weibo": 0, "bilibili": 0, "other": 0}
        from scraper import detect_platform
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    url_match = re.search(r'来源.*?(https?://[^\s]+)', content)
                    if url_match:
                        p = detect_platform(url_match.group(1))
                        if p in platforms:
                            platforms[p] += 1
                        else:
                            platforms["other"] += 1
                    else:
                        platforms["other"] += 1
            except:
                platforms["other"] += 1

        return {
            "total_files": len(files),
            "total_size": total_size,
            "platforms": platforms
        }


# 全局实例
_engine = None

def get_engine() -> WikiEngine:
    global _engine
    if _engine is None:
        _engine = WikiEngine()
    return _engine
