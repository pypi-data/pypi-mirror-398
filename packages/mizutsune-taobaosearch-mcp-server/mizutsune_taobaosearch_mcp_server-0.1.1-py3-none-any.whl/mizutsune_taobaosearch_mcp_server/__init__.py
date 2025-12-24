import asyncio
import sys
from uuid import uuid4
from fastmcp import FastMCP
from playwright.async_api import async_playwright
from mcp.types import ImageContent, EmbeddedResource

mcp = FastMCP("TaobaoSpecHunter")

# 全局变量保存 playwright 对象，防止函数结束时被回收
_playwright_instance = None
_browser_instance = None

async def get_existing_page():
    """
    异步连接已有的 Chrome 浏览器
    """
    global _playwright_instance, _browser_instance
    
    # 启动异步 Playwright
    if not _playwright_instance:
        _playwright_instance = await async_playwright().start()
    
    try:
        # 注意：这里必须加 await
        # 尝试连接已打开的浏览器 (CDP)
        browser = await _playwright_instance.chromium.connect_over_cdp("http://127.0.0.1:9222")
        _browser_instance = browser # 保持引用
        
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        return page
    except Exception as e:
        raise Exception(f"连接浏览器失败: {e}\n请确保已在命令行运行: chrome --remote-debugging-port=9222")

async def force_lazy_load(page, max_scrolls=5):
    """异步滚动加载"""
    print("正在预加载图片...")
    for i in range(max_scrolls):
        # 异步滚动
        await page.mouse.wheel(0, 1000)
        await asyncio.sleep(0.2) # 必须用 asyncio.sleep
    
    await page.mouse.wheel(0, -2000) 
    await asyncio.sleep(1)

# ---------------------------------------------------------
# 工具 1: 负责“搜索关键字” + ”显示价格区间框“,搜索完成后，悬停于区间按钮，会有下拉框出现，再去填价格
# ---------------------------------------------------------
@mcp.tool()
async def search_and_filter(keyword: str) -> str:
    try:
        page = await get_existing_page()
        await page.goto(f"https://s.taobao.com/search?q={keyword}&sort=sale-desc")
        
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)

        #找到”区间“按钮
        selector = 'div.next-tabs-tab-inner:text("区间")'
        # 悬停于价格筛选按钮
        await page.wait_for_selector(selector,timeout=2000)
        await page.click(selector)
        await page.hover(selector)
        await page.wait_for_timeout(2000)

        return "搜索并悬停价格筛选成功"


    except Exception as e:
        return f"出错: {str(e)}"
    

# ---------------------------------------------------------
# 工具 2: 负责价格区间填写+确认
# ---------------------------------------------------------   
@mcp.tool()
async def fill_price_filter(min_price: int, max_price: int) -> str:
    """
    在价格筛选弹窗中填写价格区间并确认
    
    Args:
        min_price: 最低价格，千万不要小数点
        max_price: 最高价格，千万不要小数点
    """
    try:
        page = await get_existing_page()
        # 查找价格输入框
        selector = 'input.textInput--QBre6Fdc'
        price_inputs = page.locator(selector)
        count = price_inputs.count()
        if await count >= 2:
            # 输入最低价，不要小数点
            await price_inputs.nth(0).fill(str(min_price))
            await asyncio.sleep(0.5)
            # 输入最高价，不要小数点
            await price_inputs.nth(1).fill(str(max_price))
            await asyncio.sleep(2)
            # 查找确认按钮
            confirm_btn = page.locator('div.confirmButton--gHXjLus4')
            
            if await confirm_btn.count() > 0:
                await confirm_btn.first.click()
                await page.wait_for_timeout(3000)
                return f"搜索完成，已应用价格筛选 {min_price}-{max_price}."
            else:
                return "未找到确认按钮，不能应用筛选。"
        else:
            return "未找到价格输入框。"
            
    except Exception as e:
        return f"填充价格筛选失败: {str(e)}"


# ---------------------------------------------------------
# 工具 3: 负责“获取当前页面的前 N 个商品链接”
# ---------------------------------------------------------
@mcp.tool()
async def get_top_product_links(limit: int = 3) -> list[str]:
    """
    第二步：获取当前浏览器页面中显示的商品链接。
    请在执行完 search_and_filter 后调用此工具。
    """
    try:
        page = await get_existing_page()
        print(f"[Action] 正在抓取前 {limit} 个商品...", file=sys.stderr)
        
        # 确保有商品显示
        try:
            await page.wait_for_selector('a[href*="item.htm"]', timeout=5000)
        except:
            return ["当前页面未发现商品链接，请检查是否需要登录或验证码"]

        locators = page.locator('a[href*="item.htm"]')
        count = await locators.count()
        
        valid_links = []
        seen_ids = set()
        import re

        for i in range(count):
            if len(valid_links) >= limit:
                break
            
            href = await locators.nth(i).get_attribute("href")
            if not href: continue

            if href.startswith("//"): 
                href = "https:" + href
            
            # ID 去重逻辑
            id_match = re.search(r'[?&]id=(\d+)', href)
            if id_match:
                item_id = id_match.group(1)
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                valid_links.append(href)
            else:
                if href not in valid_links:
                    valid_links.append(href)

        if not valid_links:
            return ["未找到链接"]
            
        print(f"[Success] 成功抓取 {len(valid_links)} 个链接", file=sys.stderr)
        return valid_links

    except Exception as e:
        return [f"抓取链接出错: {str(e)}"]

@mcp.tool()
async def capture_specs_area(url: str):
    """
    智能抓取配置单 (异步版) - 直接截图版
    """
    page = await get_existing_page()
    print(f"正在分析配置: {url}")
    
    try:
        # 导航到页面
        await page.goto(url)
        
        # 直接截图 (await screenshot)
        screenshot_bytes = await page.screenshot(full_page=False)
        
        # 保存到文件
        path = f"/tmp/specs_{uuid4().hex}.png"
        with open(path, "wb") as f:
            f.write(screenshot_bytes)
        
        return {
            "type": "image",
            "path": path
        }
        
    except Exception as e:
        return {
            "type": "error",
            "error": f"截图失败: {str(e)}"
        }




def main() -> None:
    print("Hello from mizutsune-taobaosearch-mcp-server!")
    mcp.run(transport="stdio")
    
