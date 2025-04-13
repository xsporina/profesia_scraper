from typing import Optional
import zendriver as zd
from zendriver.core.connection import ProtocolException
from zendriver.cdp.input_ import dispatch_key_event


def href_to_url(
    base_url: str, 
    href: str
) -> str:
    return base_url + href

async def safe_element_search(
    tab: zd.Tab, 
    selector: Optional[str] = None, 
    text: Optional[str] = None, 
    retries: int = 5
) -> zd.Element | None:
    """
    Element search with retries
    Reloads website if element not found {retries} amount of times
    
    """
    for attempt in range(retries):
        try:
            await tab.sleep(2)
            return await tab.wait_for(selector=selector, text=text)
        except ProtocolException as e:
            if attempt < retries - 1:
                print("Reloading")
                await tab.reload()
                await tab.sleep(5)
                continue
            raise

async def handle_cookies(
    tab: zd.Tab,
    accept_text: str = "Accept"
    ):
    """
    Accepts cookies
    
    """
    await tab.sleep(1)

    try:
        accept_button = await safe_element_search(tab, text=accept_text)

        if accept_button:
            await accept_button.click()
    except Exception as e:
        print(f"Error while handling cookies: {e}")

async def press_enter(tab: zd.Tab):
    await tab.send(dispatch_key_event(type_='rawKeyDown', key='Enter', code='Enter', windows_virtual_key_code=13))
    await tab.send(dispatch_key_event(type_='keyUp', key='Enter', code='Enter', windows_virtual_key_code=13))