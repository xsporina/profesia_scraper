import time
from typing import Optional
import zendriver as zd
from scraper.profesia import Profesia
from scraper.deepseek import Deepseek
from scraper.db_manager import DatabaseManager
from sqlalchemy.orm import Session


class Scraper:
    def __init__(self, profesia: Profesia, deepseek: Deepseek, db_manager: DatabaseManager, db_session: Session):
        self.profesia = profesia
        self.deepseek = deepseek
        self.db_manager = db_manager
        self.db_session = db_session
    
    async def run(self):
        await self.profesia.initialize()
        await self.deepseek.initialize()

        while True:
            page_jobs = await self.profesia.get_page_jobs_urls()
            for job_url in page_jobs:
                if self.db_manager.check_duplicate(self.db_session, job_url):
                    continue
                
                raw_job = await self.profesia.get_job_details(job_url)
                ai_results = await self.deepseek.send_prompt(raw_job["job_body"])

                job_data = {**raw_job, **ai_results, "url": job_url}

                self.db_manager.save_job_data(self.db_session, job_data)

                time.sleep(30)
            
            if not await self.profesia.next_page():
                break              