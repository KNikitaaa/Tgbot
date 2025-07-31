from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Dict, Any, Callable, Awaitable

class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:

        data['user'] = {
            'id': event.from_user.id,
            'username': event.from_user.username,
            'full_name': event.from_user.full_name
        }
        return await handler(event, data)