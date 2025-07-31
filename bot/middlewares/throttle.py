from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Dict, Any, Callable, Awaitable
import asyncio


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, delay: float = 0.5):
        self.delay = delay

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        await asyncio.sleep(self.delay)
        return await handler(event, data)