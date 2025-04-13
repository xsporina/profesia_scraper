import asyncio
from scraper.profesia import Profesia
from scraper.deepseek import Deepseek
from scraper.scraper import Scraper
from scraper.db_manager import DatabaseManager
import zendriver as zd
from core.config import settings
from core.database import sessionLocal


async def main():
    browser = await zd.start(chrome_args=settings.CHROME_ARGS, headless=False)

    try:
        profesia = Profesia(browser)
        deepseek = Deepseek(browser)
        db_manager = DatabaseManager()

        with sessionLocal() as db_session:
            scraper = Scraper(profesia, deepseek, db_manager, db_session)
            await scraper.run()

    finally:
        await browser.stop()

if __name__ == '__main__':
    asyncio.run(main())