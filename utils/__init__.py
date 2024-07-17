import os
import re
import random

from python_socks import ProxyType
from datetime import datetime
from telethon import TelegramClient

class Utils:
    def randfloat(self, start, stop) -> float:
        return round(random.uniform(start, stop), 10)

    @property
    def timestamp(self) -> int:
        now = datetime.now()
        timestamp = datetime.timestamp(now)
        return round(timestamp)
    
    def is_session(self, phone_number: str) -> bool:
        return os.path.isfile(f"sctg/sessions/{phone_number}.session")
    
    async def stop_client(self, client: TelegramClient, phone_number: str = False) -> None:
        try:
            await client.disconnect()
        except:
            pass
            