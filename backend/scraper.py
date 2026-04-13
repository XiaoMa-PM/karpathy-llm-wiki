"""
小红书内容抓取器
使用 Playwright 模拟浏览器获取小红书帖子正文
"""
import re
from typing import Optional


def is_xiaohongshu_url(url: str) -> bool:
    """判断是否为小红书链接"""
    patterns = [
        r'xiaohongshu\.com',
        r'xhslink\.com',
        r' hongshu\.com',
    ]
    return any(re.search(p, url, re.IGNORECASE) for p in patterns)


async def fetch_xiaohongshu(url: str) -> dict:
    """
    抓取小红书帖子内容

    Returns:
        {"title": str, "content": str, "author": str}
    """
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
            await page.goto(url, timeout=30000, wait_until="networkidle")

            # 等待内容加载
            await page.wait_for_selector("meta[name='description']", timeout=10000)

            # 获取标题
            title = ""
            try:
                title = await page.title()
            except:
                pass

            # 获取 meta 描述（微博客平台常用）
            description = ""
            try:
                desc_elem = await page.query_selector("meta[name='description']")
                if desc_elem:
                    description = await desc_elem.get_attribute("content") or ""
            except:
                pass

            # 获取 og:description
            if not description:
                try:
                    og_desc = await page.query_selector("meta[property='og:description']")
                    if og_desc:
                        description = await og_desc.get_attribute("content") or ""
                except:
                    pass

            # 尝试获取页面正文
            content = ""
            selectors_to_try = [
                "#detail-desc",           # 小红书旧版
                "div.detail-content",      # 小红书详情内容
                "meta[name='description']",
                "meta[property='og:description']",
            ]

            for selector in selectors_to_try:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 50:
                            content = text.strip()
                            break
                except:
                    continue

            # 如果还是没内容，尝试获取所有文本
            if not content or len(content) < 50:
                try:
                    body_text = await page.inner_text("body")
                    # 清理掉导航等干扰内容
                    lines = [l.strip() for l in body_text.split("\n") if l.strip() and len(l.strip()) > 10]
                    content = "\n".join(lines[:50])  # 取前50行
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
