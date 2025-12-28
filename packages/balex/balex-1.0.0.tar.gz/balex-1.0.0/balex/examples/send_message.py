import asyncio
from balex import AsyncBaleClient

async def main():
    async with AsyncBaleClient("BOT_TOKEN") as bot:
        await bot.send_message(123456789, "سلام از Balex v1.0 🚀")
asyncio.run(main())
