import json
import random

import zendriver as zd

from zendriver.cdp.input_ import dispatch_key_event
from core.config import settings
from utils.browser_utils import handle_cookies, press_enter


class Deepseek:
    def __init__(self, browser: zd.Browser):
        # self.login_name = login_name
        # self.login_password = login_password
        self.logged_in = False
        self.browser = browser
        self.tab: zd.Tab
        self.prompt_base = """Extract info into this format in json, 
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
    
    async def initialize(self):
        self.tab = await self.browser.get(settings.DEEPSEEK_URL, new_tab=True)

        await self._login_with_credentials()
        await handle_cookies(self.tab, "Necessary cookies only")
    
    async def _login_with_credentials(self):
        email_field = await self.tab.find("Phone number / email address")
        password_field = await self.tab.select("[type*=password]")

        if not email_field or not password_field:
            raise RuntimeError("Could not find login fields")

        print("Logging in with credentials...")
        await email_field.mouse_click()
        await email_field.send_keys(settings.DEEPSEEK_NAME)
        await password_field.send_keys(settings.DEEPSEEK_PASSWORD)

        login_button = await self.tab.find("Log in")
        await login_button.click()
        
    async def send_prompt(self, job_body: str) -> dict:
        """
        Sends prompt to deepseek
        
        """
        # Opens new chat window
        await self._open_new_chat()

        # Sends message to chat
        await self._send_message(job_body)

        # Waits for answer and if found returns it
        if await self._wait_for_answer():
            ai_response = await self._grab_ai_response()
            ai_response = self._normalize_dict(ai_response)
            return ai_response
        
        raise Exception("Deepseek response not found")
    
    async def _open_new_chat(self):
        """
        Opens new chat windo in deepseek
        
        """
        new_chat_button = await self.tab.find("New chat")
        await new_chat_button.click()
    
    async def _send_message(self, job_body: str):
        """
        Writes and sends message to deepseek chat
        
        """
        message_field = await self.tab.find("Message DeepSeek")
        await message_field.mouse_click()
        await message_field.send_keys(self.prompt_base + job_body)
        await press_enter(self.tab)
    
    async def _wait_for_answer(self) -> bool:
        """
        Waits for answer
        Reloads if server busy
        
        """
        attempt = 1
        while attempt <= 3:
            try:
                answer_text = await self.tab.select_all('[class*=token]', timeout=random.randint(120,180))
                if "}" in answer_text[-1].text:
                    print("Answer found.")
                    return True

            except Exception as e:
                print(f"Error: {e}")
                
                try:
                    error_text = await self.tab.find('The server is busy. Please try again later.')
                    if error_text:
                        print("The server is busy...")
                        all_buttons = await self.tab.select_all('[class*=ds-icon-button]')
                        await all_buttons[4].mouse_click() # click 6th button (reload button)
                        print("Reloading answer.")

                except Exception as e:
                    print(f"[{attempt}]Reloading page...")
                    attempt += 1
                    await self.tab.reload()
        
        return False
    
    async def _grab_ai_response(self) -> dict:
        """
        Grabs response from Deepseek and turns it into dictionary
        
        """
        answer_block = await self.tab.select_all('[class*=token]')

        ai_response_string = ''
        for a in answer_block:
            ai_response_string += a.text.lower()
        
        ai_response = json.loads(ai_response_string)

        return ai_response

    def _normalize_dict(self, data) -> dict:
        """
        Normalizes dictionary values into lists

        For example:
            "technologies": None
        ->  "technologies": []

            "contract_type": "part-time"
        ->  "contract_type": ["part-time"]
        
        """
        for key, value in data.items():
            if key in ["contract_type", "technologies"]:
                if value is None:
                    data[key] = []
                elif isinstance(value, str):
                    data[key] = [value]
        return data