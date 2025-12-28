import asyncio
from balex import AsyncBaleClient

async def main():
    async with AsyncBaleClient("BOT_TOKEN") as bot:
        webhook_url = "https://yourserver.com/balex_webhook"
        result = await bot.set_webhook(webhook_url)
        print("Webhook set:", result)

        
        info = await bot.get_webhook_info()
        print("Webhook info:", info)
asyncio.run(main())
