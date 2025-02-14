import asyncio
import re
import time

import zendriver as zd

import inspect
# from parser import parse_with_ollama
from zendriver.cdp.input_ import dispatch_key_event

# def print_all_properties(obj):
#     # Get the class of the object to find its properties
#     cls = obj.__class__
    
#     # Find all properties defined in the class
#     properties = inspect.getmembers(cls, lambda attr: isinstance(attr, property))
    
#     for prop_name, prop in properties:
#         try:
#             # Get the value of the property using its getter method
#             value = prop.fget(obj)
#             print(f"{prop_name} = {repr(value)}")
#         except Exception as e:
#             print(f"{prop_name} = <Error: {str(e)}>")
    
def href_to_url(href):
    return "https://www.profesia.sk" + href

async def get_overall_info(tab: zd.Tab):
    overall_info = await tab.select("[class*=overall-info]")

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
    
    j=0
    for kokot in overall_info_strings:
        print(j, kokot)
        j+=1

    data = {}

    # Iterate through the overall_info_list list
    i = 0
    while i < len(overall_info_strings):
        print("CHECKING: ", i, overall_info_strings[i])

        # Check for the ID field
        if 'ID:' in str(overall_info_strings[i]):
            print("ID")
            data['id'] = overall_info_strings[i + 1].strip()  # Extract the ID value
            i += 2  # Move to the next element
            print("ID DONE")

        # Check for the posting date field
        elif 'Posting date:' in overall_info_strings[i]:
            print("POSTING DATE")
            # Extract the date from the next element (inside <span>)
            data['posted_at'] = re.sub(r'<[^>]*>', '', overall_info_strings[i + 1])
            i += 2  # Move to the next element
            print("POSTING DATE DONE")
        
        elif 'location:' in overall_info_strings[i]:
            print("LOC")
            location = overall_info_strings[i + 1].strip()
            location = location.split('>')[1].split('<')[0]
            data['location'] = location
            i += 2
            print("LOC DONE")

        # Check for the salary field
        elif 'Basic salary component (gross):' in overall_info_strings[i]:
            print("BASIC SALARY")
            salary_str = overall_info_strings[i + 1].strip()
    
            # Use regex to extract the numeric part (supports spaces, commas, decimals)
            numeric_part = re.match(r'^[\d\s,.]+', salary_str)
            if numeric_part:
                # Clean the numeric value (remove spaces and commas, handle decimals)
                pay_min = numeric_part.group().replace(' ', '').replace(',', '')
                data['pay_min'] = pay_min
                
                # Extract the unit (everything after the numeric part)
                unit = salary_str[numeric_part.end():].strip()
                data['pay_unit'] = unit.strip(".")
            else:
                data['pay_min'] = None
                data['pay_unit'] = None
            i += 2  # Move to the next element
            print("BASIC SALARY DONE")
        
        elif 'Position:' in overall_info_strings[i]:
            print("POSITION")
            data['categories'] = []
            while True:
                position = overall_info_strings[i + 1].strip()
                position = position.split('>')[1].split('<')[0]
                data['categories'].append(position)
                if ',' in overall_info_strings[i + 2]:
                    i += 2
                else:
                    break
            i += 2
            print("POSITIONDONE")
        
        elif 'Company:' in overall_info_strings[i]:
            print("COMP")
            company = overall_info_strings[i + 1].strip()
            company = company.split('>')[1].split('<')[0]
            data['company'] = company
            i += 2
            print("COMP DONE")
            
        else:
            i += 1  # Skip irrelevant elements


    return data

async def get_job_body(tab: zd.Tab):
    check = await tab.query_selector("[class*=maintextarea]")
    if check:
        body = check
    else:
        delete = ["[class*=overall-info]", "[class*=card-content] > script", "[class*=button-bar]", "[class*=company-info]", "[itemprop*=hiringOrganization]"]
        for d in delete:
            selector = await tab.query_selector(str(d))
            if selector:
                await selector.remove_from_dom()
        body = await tab.select("[class*=card-content]")
        
    text = body.text_all
    text = "\n".join(
        line.strip() for line in text.splitlines() if line.strip()
    )
    print(text)

    # dom_chunks = split_dom_content(text)

    # print(len(text))
    # print(len(text.split()))

    # parse_description = "return json with these fields:\
    #     job_title: \
    #     contract_type: \
    #     home_office: \
    #     salary_max: \
    #     knowledge(ignore level of knowledge): \
    #     min_experience_years: \
    # "
    # result = parse_with_ollama(dom_chunks, parse_description)
    # print(result)

# def split_dom_content(dom_content, max_length=6000):
#     return [
#         dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)
#     ]

# find all jobs listed on the page
async def get_jobs_on_page(tab: zd.Tab):
    jobs = await tab.select_all('a[id*=offer]')
    jobs.pop(0)
    return jobs

async def next_page(tab: zd.Tab):
    pass

async def scrape_website():
    browser = await zd.start()
    tab = await browser.get("https://www.profesia.sk/en/work/information-technology/")
    
    # accept necessary cookies
    await tab.sleep(0.5)
    accept_cookies = await tab.find("Accept necessary")
    await accept_cookies.click()

    jobs = get_jobs_on_page(tab)


    # tab_job = await browser.get(href_to_url(jobs[0].href), new_tab=True)
    # data = await get_overall_info(tab_job)
    test = await browser.get("https://www.profesia.sk/en/work/saiworx/O5014782?search_id=d6b95e97-28e5-4b5a-98f9-40fbb7b90bcf", new_tab=True)
    await get_job_body(test)
    # print(data)

    
    await tab.sleep(30)
    await browser.stop()

# if __name__ == '__main__':
#     asyncio.run(scrape_website())