from configparser import ConfigParser
from dataclasses import dataclass
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


@dataclass(frozen=True)
class Config:
    token: str
    db_uri: str
    plan_ru_file_id: str
    plan_uz_file_id: str


def load_config() -> Config:
    parser = ConfigParser()
    with open('config.ini') as f:
        parser.read_file(f)

    return Config(
        token=parser["bot"].get("token"),
        db_uri=parser["bot"].get("db_uri"),
        plan_ru_file_id=parser["bot"].get("plan_ru_file_id"),
        plan_uz_file_id=parser["bot"].get("plan_uz_file_id")
    )


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config: Config):
        self.config = config

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["config"] = self.config
        result = await handler(event, data)
        return result
