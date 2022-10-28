from typing import Optional
from playwright.async_api import Browser, BrowserContext, async_playwright, Playwright

_browser: Optional[Browser] = None
_playwright: Optional[Playwright] = None


async def init(**kwargs) -> Browser:
    global _browser
    global _playwright
    _playwright = await async_playwright().start()
    _browser = await launch_browser(**kwargs)
    return _browser


async def launch_browser(**kwargs) -> Browser:
    return await _playwright.chromium.launch(**kwargs)


async def get_browser(**kwargs) -> Browser:
    kwargs["headless"] = False
    return _browser or await init(**kwargs)


async def get_context(**kwargs) -> BrowserContext:
    browser = await get_browser(**kwargs)
    return await browser.new_context()


async def close():
    contexts = _browser.contexts
    for cont in contexts:
        await cont.close()
    await _browser.close()
