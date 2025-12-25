import asyncio
from pytimebudget import pytimebudget

async def work():
    async with pytimebudget("async_test", max_ms=50):
        await asyncio.sleep(0.01)

def test_async():
    asyncio.run(work())
