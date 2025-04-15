import asyncio
import json
import re

import zendriver as zd
from . import deepseek as ais

# from parser import parse_with_ollama
# from core.database_manager import sessionLocal
from utils.browser_utils import safe_element_search
from core.config import settings
from utils.browser_utils import handle_cookies, href_to_url

class Profesia:

    def __init__(self, browser: zd.Browser):
        self.browser = browser
        self.tab: zd.Tab
        self.scrape_url = settings.JOB_LIST_URL
        self._load_position_mapping()
    
    def _load_position_mapping(self):
        """
        Load job positions translations
        
        """
        try:
            with open('app/scraper/position_tl.json', 'r', encoding='utf-8') as file:
                self.position_mapping = json.load(file)
        except FileNotFoundError:
            # logger.warning("Position mapping file not found, using empty mapping")
            self.position_mapping = {}
    
    async def initialize(self):
        """
        Initialize the profesia website for job scraping
        
        """
        self.tab = await self.browser.get(self.scrape_url, new_tab=True)
        
        await handle_cookies(self.tab, "Accept necessary")

    async def get_page_jobs_urls(self) -> list[str]:
        """
        Gets URLs to job offers on single profesia page
        
        """
        await self.tab.activate()

        jobs = await self.tab.select_all('a[id*=offer]')
        jobs.pop(0)

        return [href_to_url("https://www.profesia.sk", str(job.href)) for job in jobs]
    
    async def get_job_details(self, job_url: str) -> dict:
        """
        Gets job offer data with text body
        
        """
        job_tab = await self.browser.get(job_url, new_tab=True)
        job_data = await self._scrape_overall_info(job_tab)
        job_body = await self._scrape_job_body(job_tab)
        await job_tab.close()

        return {
            **job_data,
            "job_body": job_body
        }
    
    async def _scrape_overall_info(self, tab: zd.Tab):
        """
        Gets data from overall-info part of the job offer
        (id, posting date, location, min salary, positions, company)

        """
        print("LF overall-info")
        overall_info = await safe_element_search(tab, selector="[class*=overall-info]")
        print("Found overall-info")

        overall_info_strings = []
        for oi in overall_info.children:
            if oi.child_node_count is not None:
                if oi.child_node_count > 1:
                    for oi2 in oi.children:
                        overall_info_strings.append(str(oi2))
                else:
                    overall_info_strings.append(str(oi))
            else:
                overall_info_strings.append(str(oi))

        data = {}

        # Iterate through the overall_info_list list
        i = 0
        while i < len(overall_info_strings):

            # Check for the ID field
            if 'ID:' in str(overall_info_strings[i]):
                data['ps_id'] = overall_info_strings[i + 1].strip().lower()  # Extract the ID value
                i += 2  # Move to the next element

            # Check for the posting date field
            elif 'Posting date:' in overall_info_strings[i]:
                # Extract the date from the next element (inside <span>)
                data['posted_at'] = re.sub(r'<[^>]*>', '', overall_info_strings[i + 1]).lower()
                i += 2  # Move to the next element
            
            elif 'location:' in overall_info_strings[i]:
                raw_location = overall_info_strings[i + 1].strip()
                if '>' in raw_location and '<' in raw_location:
                    location = raw_location.split('>')[1].split('<')[0]
                else:
                    location = raw_location.split('&')[0].strip()
                    if "Práca z domu" in location:
                        location = location.replace("Práca z domu", "Remote work")
                if location:
                    data['location'] = location.lower()
                i += 2

            # Check for the salary field
            elif 'Basic salary component (gross):' in overall_info_strings[i]:
                salary_str = overall_info_strings[i + 1].strip()
        
                # Use regex to extract the numeric part (supports spaces, commas, decimals)
                numeric_part = re.match(r'^[\d\s,.]+', salary_str)
                if numeric_part:
                    # Clean the numeric value (remove spaces and commas, handle decimals)
                    salary_min = numeric_part.group().replace(' ', '').replace(',', '')
                    data['salary_min'] = salary_min
                    
                    # Extract the unit (everything after the numeric part)
                    unit = salary_str[numeric_part.end():].strip(".").lower()
                    if "mesiac" in unit:
                        unit = unit.replace("mesiac", "month")
                    if "hod" in unit:
                        unit = unit.replace("hod", "hour")
                    data['salary_unit'] = unit
                else:
                    data['salary_min'] = None
                    data['salary_unit'] = None
                i += 2  # Move to the next element
            
            elif 'Position:' in overall_info_strings[i]:
                data['position'] = []
                while True:
                    position = overall_info_strings[i + 1].strip()
                    position = position.split('>')[1].split('<')[0]

                    if position in self.position_mapping:  # Check if the position exists in the mapping
                        mapped_position = self.position_mapping[position]  # Get the mapped value
                        data['position'].append(mapped_position.lower())
                    else:
                        data['position'].append(position.lower())

                    if ',' in overall_info_strings[i + 2]:
                        i += 2
                    else:
                        break
                i += 2
            
            elif 'Company:' in overall_info_strings[i]:
                company = overall_info_strings[i + 1].strip()
                company = company.split('>')[1].split('<')[0]
                if company:
                    data['company'] = company.lower()
                i += 2
                
            else:
                i += 1  # Skip irrelevant elements

        return data
    
    async def _scrape_job_body(self, tab: zd.Tab):
        """
        Gets text body of the job offer
        
        """
        main_text = await tab.query_selector(".maintextearea")   # maintextarea is for the custom templates
        if main_text:
            scripts = await main_text.query_selector_all("script")
            for script in scripts:
                    await script.remove_from_dom()
            body = await tab.select(".maintextearea")

        else:
            delete = ["[class*=overall-info]", "[class*=card-content] > script", "[class*=button-bar]", "[class*=company-info]", "[itemprop*=hiringOrganization]"]
            for d in delete:
                selector = await tab.query_selector(str(d))
                if selector:
                    await selector.remove_from_dom()
            body = await tab.select("[class*=card-content]")    # card-content is for the classic profesia template
            
        text = body.text_all
        text = "\n".join(
            line.strip() for line in text.splitlines() if line.strip()
        )

        return text
    
    async def next_page(self):
        """
        Navigates to next page of job offers
        Returns False if next page button not found

        """
        await self.tab.activate()

        next_page = await safe_element_search(self.tab, selector="[class*=next]")

        if next_page:
            await next_page.click()
            return True
        
        return False