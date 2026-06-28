# backend/scrapers/recovery.py
"""
When platform scraper_status.status='broken', use Playwright to re-fetch the page,
analyze selector candidates, and reset failure count so the scraper retries.
"""
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from backend.models import ScraperStatus

CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_DIR.mkdir(exist_ok=True)


async def attempt_recovery(platform: str, url: str, db: AsyncSession) -> bool:
    """
    1. Fetch the page with Playwright
    2. Find most-repeated element classes (likely item cards)
    3. Save selector candidates + screenshot to config/{platform}.json
    4. Reset failure_count to 2 so scraper retries on next cycle
    Returns True if candidates found, False on error.
    """
    screenshot_path = f"/tmp/scraper_screenshots/recovery_{platform}_{int(time.time())}.png"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            )
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.screenshot(path=screenshot_path, full_page=False)

            candidates = await page.evaluate("""
                () => {
                    const countMap = {};
                    document.querySelectorAll('*').forEach(el => {
                        if (el.className && typeof el.className === 'string') {
                            const cls = el.className.trim().split(/\\s+/)[0];
                            if (cls.length > 2) {
                                countMap[cls] = (countMap[cls] || 0) + 1;
                            }
                        }
                    });
                    return Object.entries(countMap)
                        .filter(([k, v]) => v >= 5 && v <= 50)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 10)
                        .map(([cls, count]) => ({ selector: '.' + cls, count }));
                }
            """)
            await browser.close()

        config = {
            "platform": platform,
            "url": url,
            "recovered_at": time.time(),
            "candidate_selectors": candidates,
            "screenshot": screenshot_path,
        }
        config_path = CONFIG_DIR / f"{platform}.json"
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2))

        await db.execute(
            update(ScraperStatus)
            .where(ScraperStatus.platform == platform)
            .values(status="failing", failure_count=2, screenshot_path=screenshot_path)
        )
        await db.commit()
        return bool(candidates)

    except Exception as e:
        await db.execute(
            update(ScraperStatus)
            .where(ScraperStatus.platform == platform)
            .values(error_log=f"recovery failed: {str(e)[:500]}")
        )
        await db.commit()
        return False
