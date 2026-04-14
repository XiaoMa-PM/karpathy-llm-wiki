"""
通用内容抓取器
支持：小红书、知乎、微博、B站、今日头条、语雀、Notion、Medium
"""
import re
import json
from typing import Optional


PLATFORMS = {
    "xiaohongshu": ["xiaohongshu.com", "xhslink.com"],
    "zhihu": ["zhihu.com"],
    "weibo": ["weibo.com", "微博"],
    "bilibili": ["bilibili.com", "b23.tv"],
    "toutiao": ["toutiao.com", "头条"],
    "yuque": ["yuque.com"],
    "notion": ["notion.so"],
    "medium": ["medium.com"],
}


def detect_platform(url: str) -> Optional[str]:
    """检测 URL 属于哪个平台"""
    url_lower = url.lower()
    for platform, domains in PLATFORMS.items():
        for domain in domains:
            if domain in url_lower:
                return platform
    return None


async def fetch_content(url: str) -> dict:
    """根据平台调用对应抓取器"""
    platform = detect_platform(url)

    if not platform:
        return {"error": f"暂不支持该平台，当前支持: {', '.join(PLATFORMS.keys())}"}

    fetchers = {
        "xiaohongshu": fetch_xiaohongshu,
        "zhihu": fetch_zhihu,
        "weibo": fetch_weibo,
        "bilibili": fetch_bilibili,
        "toutiao": fetch_toutiao,
        "yuque": fetch_yuque,
        "notion": fetch_notion,
        "medium": fetch_medium,
    }

    fetcher = fetchers.get(platform)
    if fetcher:
        return await fetcher(url)
    return {"error": f"平台 {platform} 抓取器未实现"}


# ============= 小红书 =============
async def fetch_xiaohongshu(url: str) -> dict:
    """抓取小红书帖子"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright 未安装，请运行: pip install playwright && playwright install chromium"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # 等待内容加载
            await page.wait_for_timeout(5000)

            title = await page.title() or ""
            description = ""

            # 获取 meta 描述
            for selector in ["meta[name='description']", "meta[property='og:description']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        description = await elem.get_attribute("content") or ""
                        break
                except:
                    continue

            # 获取正文
            content = ""
            for selector in ["#detail-desc", "div.detail-content"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 50:
                            content = text.strip()
                            break
                except:
                    continue

            # 兜底：获取页面所有文本
            if not content or len(content) < 50:
                try:
                    body_text = await page.inner_text("body")
                    lines = [l.strip() for l in body_text.split("\n") if l.strip() and len(l.strip()) > 10]
                    content = "\n".join(lines[:50])
                except:
                    pass

            await browser.close()

            if not content and not title:
                return {"error": "无法获取内容，页面结构可能已更新"}

            return {
                "title": title.replace("小红书", "").strip() or "小红书帖子",
                "content": content or description,
                "author": "小红书用户",
                "url": url
            }

        except Exception as e:
            await browser.close()
            return {"error": f"抓取失败: {str(e)}"}


# ============= 知乎 =============
async def fetch_zhihu(url: str) -> dict:
    """抓取知乎文章（公开内容）"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright 未安装"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            title = await page.title() or ""
            content = ""

            # 知乎文章正文
            for selector in [".Post-RichText", "div.RichText", "#root .content"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 100:
                            content = text.strip()
                            break
                except:
                    continue

            # 获取标题
            for selector in ["h1.Post-Title", "h1[data-za-detail-view-id]>span"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        t = await elem.inner_text()
                        if t:
                            title = t.strip()
                            break
                except:
                    continue

            await browser.close()

            if not content:
                return {"error": "无法获取知乎内容，可能需要登录"}

            return {
                "title": title or "知乎文章",
                "content": content,
                "author": "知乎用户",
                "url": url
            }
        except Exception as e:
            await browser.close()
            return {"error": f"抓取失败: {str(e)}"}


# ============= 微博 =============
async def fetch_weibo(url: str) -> dict:
    """抓取微博文章"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright 未安装"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            title = await page.title() or ""
            content = ""

            for selector in [".article-content", "div[node-type='article']", ".weibo-text"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 50:
                            content = text.strip()
                            break
                except:
                    continue

            await browser.close()

            if not content:
                return {"error": "无法获取微博内容"}

            return {
                "title": title.replace("微博", "").strip() or "微博",
                "content": content,
                "author": "微博用户",
                "url": url
            }
        except Exception as e:
            await browser.close()
            return {"error": f"抓取失败: {str(e)}"}


# ============= B站 =============
async def fetch_bilibili(url: str) -> dict:
    """抓取B站文章/专栏"""
    import requests

    # 尝试从 URL 提取专栏 ID
    match = re.search(r'/article/(\d+)', url)
    if not match:
        # 可能是视频，尝试获取描述
        return await fetch_bilibili_with_playwright(url)

    article_id = match.group(1)

    # B站专栏有公开 API
    try:
        api_url = f"https://api.bilibili.com/x/article/view?id={article_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com/"
        }
        resp = requests.get(api_url, headers=headers, timeout=10)
        data = resp.json()

        if data.get("code") == 0:
            article = data["data"]
            return {
                "title": article.get("title", "B站专栏"),
                "content": article.get("content", ""),
                "author": article.get("author_name", "B站用户"),
                "url": url
            }
    except:
        pass

    # 兜底 Playwright
    return await fetch_bilibili_with_playwright(url)


async def fetch_bilibili_with_playwright(url: str) -> dict:
    """用 Playwright 抓取B站"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright 未安装"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            title = await page.title() or ""

            # 获取视频描述
            desc = ""
            for selector in ["div.desc-v2", "div.video-desc", "meta[property='og:description']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        if selector.startswith("meta"):
                            desc = await elem.get_attribute("content") or ""
                        else:
                            desc = await elem.inner_text()
                        if desc:
                            break
                except:
                    continue

            await browser.close()
            return {
                "title": title.replace(" - 哔哩哔哩", "").strip() or "B站内容",
                "content": desc,
                "author": "B站用户",
                "url": url
            }
        except Exception as e:
            await browser.close()
            return {"error": f"抓取失败: {str(e)}"}


# ============= 今日头条 =============
async def fetch_toutiao(url: str) -> dict:
    """抓取今日头条文章"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright 未安装"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            title = ""
            content = ""

            for selector in ["h1.article-title", "h1.tite-content", "meta[property='og:title']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        title = await elem.inner_text() if not selector.startswith("meta") else await elem.get_attribute("content") or ""
                        break
                except:
                    continue

            for selector in ["div.article-content", "div.article-body", "article"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 100:
                            content = text.strip()
                            break
                except:
                    continue

            await browser.close()

            if not content:
                return {"error": "无法获取头条内容"}

            return {
                "title": title or "今日头条",
                "content": content,
                "author": "头条用户",
                "url": url
            }
        except Exception as e:
            await browser.close()
            return {"error": f"抓取失败: {str(e)}"}


# ============= 语雀 =============
async def fetch_yuque(url: str) -> dict:
    """抓取语雀文档（公开知识库）"""
    import requests

    # 语雀 API
    match = re.search(r'yuque\.com/([^/]+)/([^/]+)', url)
    if not match:
        return await fetch_yuque_with_playwright(url)

    try:
        # 尝试 API 方式
        api_url = f"https://www.yuque.com/api/docs/{match.group(1)}/{match.group(2)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        resp = requests.get(api_url, headers=headers, timeout=10)
        data = resp.json()

        if data.get("data"):
            doc = data["data"]
            return {
                "title": doc.get("title", "语雀文档"),
                "content": doc.get("description") or doc.get("body", ""),
                "author": doc.get("user_name", "语雀用户"),
                "url": url
            }
    except:
        pass

    return await fetch_yuque_with_playwright(url)


async def fetch_yuque_with_playwright(url: str) -> dict:
    """用 Playwright 抓取语雀"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright 未安装"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            title = await page.title() or ""
            content = ""

            for selector in ["div.article-body", "div#body", "article"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 50:
                            content = text.strip()
                            break
                except:
                    continue

            await browser.close()
            return {
                "title": title.replace(" - 语雀", "").strip() or "语雀文档",
                "content": content,
                "author": "语雀用户",
                "url": url
            }
        except Exception as e:
            await browser.close()
            return {"error": f"抓取失败: {str(e)}"}


# ============= Notion =============
async def fetch_notion(url: str) -> dict:
    """抓取 Notion 页面（公开页面）"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright 未安装"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            title = ""
            content = ""

            for selector in ["meta[property='og:title']", "span.notion-heading-1"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        title = await elem.get_attribute("content") if "meta" in selector else await elem.inner_text()
                        if title:
                            break
                except:
                    continue

            for selector in ["div.notion-page-content", "div.page-body"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 50:
                            content = text.strip()
                            break
                except:
                    continue

            await browser.close()

            if not content:
                return {"error": "无法获取 Notion 内容，可能需要登录或页面未公开"}

            return {
                "title": title or "Notion 页面",
                "content": content,
                "author": "Notion",
                "url": url
            }
        except Exception as e:
            await browser.close()
            return {"error": f"抓取失败: {str(e)}"}


# ============= Medium =============
async def fetch_medium(url: str) -> dict:
    """抓取 Medium 文章"""
    import requests

    # Medium 有简单的 HTML 端点
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html"
        }
        resp = requests.get(url, headers=headers, timeout=10)

        title = ""
        content = ""

        title_match = re.search(r'<meta name="title" content="([^"]+)"', resp.text)
        if title_match:
            title = title_match.group(1)

        content_match = re.search(r'<meta name="description" content="([^"]+)"', resp.text)
        if content_match:
            content = content_match.group(1)

        # 获取文章正文 section
        article_match = re.search(r'<article[^>]*>(.*?)</article>', resp.text, re.DOTALL)
        if article_match:
            # 简单清理 HTML 标签
            text = re.sub(r'<[^>]+>', '', article_match.group(1))
            text = ' '.join(text.split())
            if len(text) > 100:
                content = text

        if title or content:
            return {
                "title": title or "Medium 文章",
                "content": content,
                "author": "Medium 作者",
                "url": url
            }
    except:
        pass

    # 兜底 Playwright
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright 未安装"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            title = await page.title() or ""

            for selector in ["article", "div[data-component='paragraph']"]:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 100:
                            content = text.strip()
                            break
                except:
                    continue

            await browser.close()
            return {
                "title": title or "Medium 文章",
                "content": content,
                "author": "Medium 作者",
                "url": url
            }
        except Exception as e:
            await browser.close()
            return {"error": f"抓取失败: {str(e)}"}
