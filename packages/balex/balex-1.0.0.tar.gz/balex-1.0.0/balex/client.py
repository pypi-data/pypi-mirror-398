import aiohttp, asyncio
from .exceptions import BaleAPIError
from .logger import log

class AsyncBaleClient:
    BASE_URL = "https://tapi.bale.ai/bot"

    def __init__(self, token, timeout=10, retries=3):
        self.token = token
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retries = retries
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def _post(self, method, payload):
        for attempt in range(1, self.retries + 1):
            try:
                async with self.session.post(f"{self.BASE_URL}{self.token}/{method}", json=payload) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get("ok"):
                        return data["result"]
                    raise BaleAPIError(data)
            except Exception as e:
                log.warning(f"Attempt {attempt}/{self.retries} failed: {e}")
                await asyncio.sleep(attempt)
        raise BaleAPIError("Request failed after retries")

    # ===== ارسال پیام =====
    async def send_message(self, chat_id, text):
        payload = {"chat_id": chat_id, "text": text}
        return await self._post("sendMessage", payload)

    # ===== وب هوک =====
    async def set_webhook(self, url: str):
        """ثبت Webhook"""
        payload = {"url": url}
        return await self._post("setWebhook", payload)

    async def delete_webhook(self):
        """حذف Webhook"""
        payload = {}
        return await self._post("deleteWebhook", payload)

    async def get_webhook_info(self):
        """اطلاعات وب هوک فعلی"""
        return await self._post("getWebhookInfo", {})
