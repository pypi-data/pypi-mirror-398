# -*- coding: utf-8 -*-
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject

from aiogram_smart_messages.message_engine import MessageEngine

class MessageEngineMiddleware(BaseMiddleware):
    """
    Middleware для получения msg_adapter
    """

    def __init__(self, bot: Bot):
        self.msg_adapter = MessageEngine(bot)

    async def __call__(self, handler, event: TelegramObject, data: dict):
        data["msg_engine"] = self.msg_adapter
        return await handler(event, data)
