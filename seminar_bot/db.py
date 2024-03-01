from enum import StrEnum
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    declarative_base,
    Mapped,
    mapped_column,
)

Base = declarative_base()


class User(Base):
    __tablename__ = "tg_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column()
    username: Mapped[str | None] = mapped_column()
    name: Mapped[str] = mapped_column()
    phone_number: Mapped[str] = mapped_column()
    date: Mapped[str | None] = mapped_column()
    organization: Mapped[str | None] = mapped_column()
    hotel_info: Mapped[bool] = mapped_column(default=False)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db_uri):
        engine = create_async_engine(db_uri)
        self.session_factory = async_sessionmaker(bind=engine)

    async def __call__(
            self,
            handler: Callable[
                [TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            data["session"] = session
            result = await handler(event, data)
            await session.commit()
        return result
