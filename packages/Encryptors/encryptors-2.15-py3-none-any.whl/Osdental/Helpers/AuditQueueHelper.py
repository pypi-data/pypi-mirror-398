import asyncio

class AuditQueueHelper:
    _lock = asyncio.Lock()

    @staticmethod
    async def send(coro):
        async with AuditQueueHelper._lock:
            await coro
