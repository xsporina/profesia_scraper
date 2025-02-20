import zendriver as zd
from zendriver.core.connection import ProtocolException

async def safe_element_search(tab: zd.Tab, selector=None, text=None, retries=5) -> zd.Element:
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