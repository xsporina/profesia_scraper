import asyncio
from datetime import datetime
import json
import random
import re
import time

from sqlalchemy import Engine
import zendriver as zd
from . import AIscraper as ais

import inspect
# from parser import parse_with_ollama
from zendriver.cdp.input_ import dispatch_key_event
from zendriver.core.connection import ProtocolException
from sqlalchemy.orm import Session
from ..core.db import sessionLocal
from app.scraper.safe_search import safe_element_search

from ..models import Contract, Job, Position, Technology


CHROME_ARGS = [
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]
IS_LOGGED_IN = False
    
def href_to_url(href):
    return "https://www.profesia.sk" + href

# async def safe_element_search(tab: zd.Tab, selector='', text='', retries=5) -> zd.Element:
#     for attempt in range(retries):
#         try:
#             await tab.sleep(2)
#             return await tab.wait_for(selector=selector, text=text)
#         except ProtocolException as e:
#             if attempt < retries - 1:
#                 print("Reloading")
#                 await tab.reload()
#                 await tab.sleep(5)
#                 continue
#             raise

async def handle_cookies(tab: zd.Tab):
    await tab.sleep(1)
    accept_button = await safe_element_search(tab, text="Accept necessary")
    await accept_button.click()

async def get_overall_info(tab: zd.Tab):
    with  open('app\scraper\position_tl.json', 'r', encoding='utf-8') as file:
        position_mapping = json.load(file)

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

                if position in position_mapping:  # Check if the position exists in the mapping
                    mapped_position = position_mapping[position]  # Get the mapped value
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

async def get_job_body(tab: zd.Tab):
    check = await tab.query_selector(".maintextearea")   # maintextarea is for the custom templates
    if check:
        while True:
            javascript = await tab.query_selector(".maintextearea > script")
            if javascript:
                await javascript.remove_from_dom()
                javascript = None
            else:
                break
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

# find all jobs listed on the page
async def get_jobs_on_page(tab: zd.Tab):
    jobs = await tab.select_all('a[id*=offer]')
    jobs.pop(0)
    print("Got jobs on page.")
    return jobs

def save_job_data(session: Session, data: dict):
    # Convert and parse basic fields
    ps_id = int(data['ps_id'])
    posted_at = datetime.strptime(data['posted_at'], '%d.%m.%Y')
    salary_min = float(data['salary_min']) if data.get('salary_min') not in (None, '') else None
    salary_max = float(data['salary_max']) if data.get('salary_max') not in (None, '') else None

    # Create a new Job instance
    job = Job(
        ps_id=ps_id,
        posted_at=posted_at,
        location=data.get('location'),
        company=data.get('company'),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_unit=data.get('salary_unit'),
        job_title=data.get('job_title'),
        home_office=data.get('home_office'),
        url=data.get('url')
    )

    # Process positions (many-to-many)
    for pos_name in data.get('position', []):
        pos = session.query(Position).filter_by(name=pos_name).first()
        if not pos:
            pos = Position(name=pos_name)
            session.add(pos)
            session.flush()  # flush to generate id if needed
        job.position.append(pos)

    # Process contract type (many-to-many)
    # If contract_type is a single string, convert it to a list.
    contract_names = data.get('contract_type', [])
    for contract_name in contract_names:
        contract = session.query(Contract).filter_by(name=contract_name).first()
        if not contract:
            contract = Contract(name=contract_name)
            session.add(contract)
            session.flush()
        job.contract_type.append(contract)

    # Process technologies (many-to-many)
    for tech_name in set(data.get('technologies', [])):
        tech = session.query(Technology).filter_by(name=tech_name).first()
        if not tech:
            tech = Technology(name=tech_name)
            session.add(tech)
            session.flush()
        job.technologies.append(tech)

    # Add the job to the session and commit the transaction
    session.add(job)
    session.commit()
    print("Job saved to database.")

def check_duplicate(href, session):
    print("Checking duplicate...")
    # Extract ps_id using regex
    match = re.search(r'/O(\d+)\?', href)

    if match:
        ps_id = int(match.group(1))
        existing_job = session.query(Job).filter_by(ps_id=ps_id).first()
        if existing_job:
            print(f"Job with ps_id {ps_id} already exists, skipping.")
            return True  # Skip to the next iteration in the loop
    
    return False

async def process_single_job(browser: zd.Browser, job_tab: zd.Tab, ai_tab: zd.Tab, url):
    print("Processing job...")
    global IS_LOGGED_IN
    job_data = await get_overall_info(job_tab)
    job_body = await get_job_body(job_tab)

    await job_tab.close()
    await ai_tab.activate()
    await ai_tab.reload()
    await ai_tab.sleep(random.randint(40,60))
    # await ai_tab.sleep(1)
    
    ai_data = await ais.AI_scrape_website(browser, ai_tab, job_body, IS_LOGGED_IN)
    IS_LOGGED_IN = True
    
    return {
        **job_data,
        **ai_data,
        "url": url
    }

async def process_all_jobs(browser: zd.Browser, main_tab: zd.Tab, ai_tab: zd.Tab, session):    
    for job in await get_jobs_on_page(main_tab):
        if check_duplicate(job.href, session):
            continue

        url = href_to_url(job.href)

        async with await browser.get(url, new_tab=True) as job_tab:
            job_data = await process_single_job(browser, job_tab, ai_tab, url)

            save_job_data(session, job_data)

async def process_all_pages(browser: zd.Browser, main_tab: zd.Tab, ai_tab: zd.Tab, session):
    while True:
        await process_all_jobs(browser, main_tab, ai_tab, session)

        next_page = await safe_element_search(main_tab, selector="[class*=next]")
        await next_page.click()
        await main_tab.sleep(1)

async def scrape_website():
    browser = await zd.start(chrome_args=CHROME_ARGS)

    try:
        main_tab = await browser.get("https://www.profesia.sk/en/work/information-technology/")
        await handle_cookies(main_tab)

        ai_tab = await browser.get('https://chat.deepseek.com/', new_tab=True)

        with sessionLocal() as session:
            await process_all_pages(browser, main_tab, ai_tab, session)
    
    finally:
        await browser.stop()

if __name__ == '__main__':
    asyncio.run(scrape_website())