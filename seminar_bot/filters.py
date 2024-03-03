from aiogram import types
from aiogram.filters import BaseFilter

from seminar_bot.config import Config


class IsAdmin(BaseFilter):
    async def __call__(
        self,
        message: types.Message,
        config: Config
    ):
        return message.chat.id == config.admin_chat_id
