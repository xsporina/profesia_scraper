import asyncio
import json
import random
import re
import time

import zendriver as zd

import inspect
# from parser import parse_with_ollama
from zendriver.cdp.input_ import dispatch_key_event


login_name = "2lolacc1795@gmail.com"
login_password = "lolacc1795"
PROMPT_BASE = """Extract info into this format in json, 
            if a field has multiple answers, turn them into a list ['like', 'this'].
            Don't add additional fields to the json other than specified by my prompt!!!!!
            Leave field empty if no answer!!!!!
            Strip of useless info(for example: 'Software engineer for our company' => 'Software engineer'), 
            translate all words to english,
            in a json format:
                {
                job_title: 
                contract_type: 
                home_office(make sure to recognize 'yes', 'no' or 'partial'): 
                salary_max(only numeric value, no letters): 
                technologies: 
                }

            """

tmp_text = """
                Software Engineer SAP Abap (Junior, Medior, Senior) Miesto práce Nivy Tower, Mlynské nivy, Ružinov, Slovensko, Bratislava (Pozícia umožňuje občasnú prácu z domu) Druh pracovného pomeru plný úväzok, skrátený úväzok Group 8 Created with Sketch. Mzdové podmienky (brutto) 1 900 - 6 000 EUR/mesiac We offer a competitive gross annual salary with the ranges below based on your skills and qualification:
                Junior (0 -1 year of experience): min. 1900 / month + bonus ;
                Medior (1 - 4 years of experience): min. 2400 / month + bonus ;
                Senior (5+ years of experience): min. 3300 / month + bonus Informácie o pracovnom mieste Náplň práce, právomoci a zodpovednosti We are looking for a skilled  Software Engineer – ABAP Developer  to join our dynamic IT team. The 
                ideal candidate will be responsible for designing, developing, and maintaining SAP applications using ABAP or UI5 programming. You will work closely with business analysts, functional consultants, and other developers to enhance SAP solutions that drive business success. Key Responsibilities: Develop, enhance, and maintain SAP applications using ABAP-OO, ODATA, RAP and related technologies. Collaborate with business and functional teams to understand requirements and translate them into technical solutions. Write clean, efficient, and well-documented code following best practices and SAP development standards. Perform unit testing, debugging, and troubleshooting to ensure 
                optimal application performance. Work on SAP enhancements, user exits, BADI, BAPI, and custom ABAP Objects. Develop and optimize SAP outputs via Adobe Forms Integrate SAP applications with external systems via RFCs, IDOCs, Web 
                Services, REST or ODATA interfaces. Support SAP system upgrades, patches, and performance tuning. Provide technical documentation and support knowledge transfer to relevant stakeholders. Zamestnanecké výhody, benefity Engaging 
                projects with top-tier national and international companies, providing exposure to cutting-edge SAP solutions. A strong focus on professional growth, including mentorship and coaching programs for aspiring talent. Clear career 
                progression opportunities within a network of experienced SAP consultants. Continuous learning and development through industry-leading training programs. Flexible working options, including remote and part-time arrangements to support work-life balance. A modern, vibrant office space located in business tower near a shopping center with easy access to public transport. State-of-the-art work equipment, including high-end smartphones and laptops for both professional and personal use. Special holiday incentives, including 30 days of vacation per year. Enhanced well-being benefits, including three additional sick days per year. Full salary coverage during illness (up to 14 days annually). Performance-based bonuses ranging from 10% to 20% on top of base salary. Free public transport ticket provided upon request. Požiadavky na zamestnanca Pozícii vyhovujú uchádzači so vzdelaním študent vysokej školyvysokoškolské I. stupňa
                vysokoškolské II. stupňa
                vysokoškolské III. stupňa Vzdelanie v odbore IT, Economy, Business Jazykové znalosti Anglický jazyk - Stredne pokročilý (B2)  a  Nemecký jazyk - Stredne pokročilý (B2) Ostatné znalosti ABAP - Základy Programovanie - Pokročilý Microsoft Office 365 - Pokročilý Pozícia je vhodná pre absolventa Áno Osobnostné predpoklady a zručnosti Are you ready to embark on an exciting journey in software development? Join our team and bring your skills to the table:  
                • Previous exposure to software development or SAP is advantageous
                • Thrive in the dynamic realm of IT solution development, particularly in a production environment
                • Possess strong communication and teamwork abilities, coupled with high self-motivation and initiative
                • Demonstrate active listening skills and a willingness to consider and incorporate diverse perspectives
                • Showcase the ability to think swiftly and devise innovative solutions to challenges
                If you're passionate about software development and eager to contribute to a collaborative team environment, we encourage you to apply today and be part of our innovative projects!
"""

def normalize_json(data):
    for key, value in data.items():
        if key in ["contract_type", "technologies"]:
            if value is None:
                data[key] = []
            elif isinstance(value, str):
                data[key] = [value]
    return data

async def check_server_busy():
    pass

async def login_with_credentials(tab: zd.Tab):
    email_field = await tab.find("Phone number / email address")
    password_field = await tab.select("[type*=password]")

    if not email_field or not password_field:
        return False

    print("Logging in with credentials...")
    await email_field.mouse_click()
    await email_field.send_keys(login_name)
    await password_field.send_keys(login_password)

    login_checkbox = await tab.find("[class*=ds-checkbox]")
    if login_checkbox:
        await login_checkbox.mouse_click()

    login_button = await tab.find("Log in")
    if login_button:
        await login_button.click()
        return True

    return False

async def press_enter(tab: zd.Tab):
    await tab.send(dispatch_key_event(type_='rawKeyDown', key='Enter', code='Enter', windows_virtual_key_code=13))
    await tab.send(dispatch_key_event(type_='keyUp', key='Enter', code='Enter', windows_virtual_key_code=13))

async def wait_answer(tab: zd.Tab, max_attempts=3):
    attempt = 1
    while attempt <= max_attempts:
        try:
            check = await tab.select_all('[class*=token]', timeout=random.randint(120,180))
            if "}" in check[-1].text:
                print("Answer found.")
                return True

        except Exception as e:
            print(f"Error: {e}")
            
            try:
                check = await tab.find('The server is busy. Please try again later.')
                if check:
                    print("The server is busy...")
                    all_buttons = await tab.select_all('[class*=ds-icon-button]')
                    await all_buttons[4].mouse_click() # click 6th button (reload button)
                    print("Reloading answer.")

            except Exception as e:
                print(f"[{attempt}]Reloading page...")
                attempt += 1
                await tab.reload()
    
    return False

async def write_message(tab: zd.Tab, job_body: str):
    print("Writing Message...")
    message_field = await tab.find("Message DeepSeek")
    await message_field.mouse_click()
    await message_field.send_keys(PROMPT_BASE + job_body)

    await press_enter(tab)

    # wait for answer
    if await wait_answer(tab):
        return True
    return False

async def get_info(tab: zd.Tab, job_body: str):
    while True:
        # click new chat
        new_chat_button = await tab.find("New chat")
        await new_chat_button.click()
        
        if await write_message(tab, job_body):
            break

    answer_block = await tab.select_all('[class*=token]')
    dict_string = ''
    for a in answer_block:
        dict_string += a.text.lower()
    
    dict_data = json.loads(dict_string)

    return dict_data

async def AI_scrape_website(browser: zd.Browser, ai_tab: zd.Tab, job_body: str, LOGGED_IN=False):
    try:
        if not LOGGED_IN:
            if not await login_with_credentials(ai_tab):
                print("Login failed.")
                return False
            print("Logged in with credentials.")

        job_dict = await get_info(ai_tab, job_body)
        job_dict = normalize_json(job_dict)
        return(job_dict)

    except Exception as e:
        print(f"Error during login: {e}")


    # # SEND MESSAGE
    # field = await tab.find("Message DeepSeek")
    # await field.mouse_click()
    # await field.send_keys(prompt)
    # # Simulate key down event for Enter key
    # await tab.send(dispatch_key_event(type_='rawKeyDown', key='Enter', code='Enter', windows_virtual_key_code=13))

    # # Simulate key up event for Enter key
    # await tab.send(dispatch_key_event(type_='keyUp', key='Enter', code='Enter', windows_virtual_key_code=13))

    # await tab.sleep(10)

    # field = await tab.find('"job_title:"')
    # print(field.text)

# if __name__ == '__main__':
#     asyncio.run(AI_scrape_website(tmp_text))