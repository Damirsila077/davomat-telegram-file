import os
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Dict, Any, Awaitable


ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AllowedAccountMiddleware(BaseMiddleware):
    def __init__(self, allowed_repo):
        self.allowed_repo = allowed_repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user = event.from_user
            if user and is_admin(user.id):
                return await handler(event, data)

            username = user.username if user else None
            if not username or not await self.allowed_repo.is_allowed(username):
                if event.text and event.text.startswith('/'):
                    await event.answer(
                        "⛔ Access denied.\nThis account is not authorized to use this bot."
                    )
                return
        return await handler(event, data)
