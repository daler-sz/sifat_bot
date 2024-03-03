import asyncio
import logging
import re
import sys

from seminar_bot.keyboards import get_meu_kb, cancel_kb, cancel_kb_btn

try:
    from asyncio import WindowsSelectorEventLoopPolicy
except ImportError:
    pass

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, InputMediaPhoto
from aiogram.utils.i18n import FSMI18nMiddleware, I18n
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from seminar_bot.config import load_config, Config, ConfigMiddleware
from seminar_bot.db import DatabaseMiddleware, User as DbUser
from seminar_bot.forum import router as forum_router
from seminar_bot.state import Menu

NAME_MAX_LENGTH = 512

PHONE_NUMBER_REGEX = re.compile("^([+]998)([0-9]{9})$")

dp = Dispatcher(storage=RedisStorage(redis=Redis()))


@dp.message(or_f(CommandStart(), F.text == __("Изменить язык")))
async def start_command(
    message: Message,
    state: FSMContext
) -> None:
    await state.set_state(Menu.choose_language)
    await message.answer(
        _("Выберите, пожалуйста, язык"),
        reply_markup=types.ReplyKeyboardMarkup(keyboard=[
            [types.KeyboardButton(text="🇷🇺Русский")],
            [types.KeyboardButton(text="🇺🇿O'zbekcha")],
        ], resize_keyboard=True)
    )


@dp.message(F.text == __("Отмена"))
async def cancel(message: types.Message, state: FSMContext):
    await message.answer(_("Отмена"), reply_markup=get_meu_kb())
    await state.set_state(Menu.menu)


@dp.message(Menu.choose_language)
async def choose_language(
    message: types.Message,
    i18n_middleware: FSMI18nMiddleware,
    state: FSMContext
) -> None:
    languages = {
        "🇷🇺Русский": "ru",
        "🇺🇿O'zbekcha": "uz",
    }
    chosen_language = languages.get(message.text)
    if not chosen_language:
        await message.answer(_("Пожалуйста, выберите корректное значение"))
    await i18n_middleware.set_locale(state=state, locale=chosen_language)
    await state.set_state(Menu.menu)
    await message.answer(
        _('Семинар «Современные вызовы в птицеводстве Узбекистана I» '
          'Ташкент 2024.'
          ),
        reply_markup=get_meu_kb()
    )


@dp.message(Menu.menu, F.text == __("Зарегистрироваться"))
async def register(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext
) -> None:
    if await is_registered(session, message.from_user):
        await message.answer(_("Вы уже зарегистрированы"))
        return
    await message.answer(
        _("Пожалуйста, введите Ваше имя"),
        reply_markup=cancel_kb()
    )
    await state.set_state(Menu.send_name)


@dp.message(Menu.send_name, F.text)
async def send_name(
    message: types.Message,
    state: FSMContext
) -> None:
    text = message.text
    if len(text) > NAME_MAX_LENGTH:
        await message.answer(_("Имя слишком длинное"))
        return

    data = await state.get_data()
    await state.set_data({
        **data,
        "name": text
    })

    await message.answer(
        _("Введите название организации"),
        reply_markup=cancel_kb()
    )
    await state.set_state(Menu.send_organization)


@dp.message(Menu.send_organization)
async def send_organization(message: Message, state: FSMContext):
    text = message.text
    if len(text) > NAME_MAX_LENGTH:
        await message.answer(_("Название слишком длинное"))
        return

    data = await state.get_data()
    await state.set_data({
        **data,
        "organization": text
    })

    await message.answer(
        _("Пожалуйста, отправьте контакт нажав на кнопку ниже или "
          "номер телефона в формате +998XXXXXXXXX"),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[
                types.KeyboardButton(
                    text=_("Отправить контакт"), request_contact=True
                )
            ], [cancel_kb_btn()]],
            resize_keyboard=True
        ),
    )
    await state.set_state(Menu.send_phone_number)


@dp.message(Menu.send_phone_number)
async def send_phone_number(
    message: types.Message,
    state: FSMContext
) -> None:
    phone_number = None
    if contact := message.contact:
        phone_number = contact.phone_number
    elif text := message.text:
        if re.fullmatch(PHONE_NUMBER_REGEX, text):
            phone_number = text

    if not phone_number:
        await message.answer(
            _("Некорректные данные, пожалуйста, попробуйте снова. "
              "Отправьте номер телефона в формате +998XXXXXXXXX либо "
              "отправьте контакт.")
        )
        return
    data = await state.get_data()
    await state.set_data({
        **data,
        "phone_number": phone_number
    })
    await message.answer(
        _("Пожалуйста, выберите дату семинара"),
        reply_markup=types.ReplyKeyboardMarkup(keyboard=[
            [
                types.KeyboardButton(text=_("5 марта")),
                types.KeyboardButton(text=_("6 марта"))
            ],
            [cancel_kb_btn()]
        ], resize_keyboard=True)
    )
    await state.set_state(Menu.send_date)


@dp.message(Menu.send_date)
async def send_date(
    message: Message,
    state: FSMContext
):
    text = message.text
    if text not in (_("5 марта"), _("6 марта")):
        await message.answer(_("Пожалуйста, выберите корректный вариант"))
        return
    data = await state.get_data()
    await state.set_data({
        **data,
        "date": text
    })
    await message.answer(
        _("Нужен ли Вам номер в гостинице?"),
        reply_markup=types.ReplyKeyboardMarkup(keyboard=[
            [
                types.KeyboardButton(text=_("Да")),
                types.KeyboardButton(text=_("Нет")),
            ],
            [cancel_kb_btn()]
        ],
            resize_keyboard=True
        )
    )
    await state.set_state(Menu.send_hotel_info)


@dp.message(Menu.send_hotel_info)
async def send_hotel_info(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    text = message.text
    if text not in (_("Да"), _("Нет")):
        await message.answer("Пожалуйста, выберите корректный вариант")
        return

    hotel_info = False
    if text == _("Да"):
        hotel_info = True

    data = await state.get_data()
    await process_registered(
        session=session,
        user=message.from_user,
        name=data["name"],
        phone_number=data["phone_number"],
        organization=data["organization"],
        date=data["date"],
        hotel_info=hotel_info
    )
    await message.answer(
        _("Ваша заявка принята. Спасибо за регистрацию!"),
        reply_markup=get_meu_kb()
    )
    await state.set_state(Menu.menu)


@dp.message(Menu.menu, F.text == __("Программа семинара"))
async def plan(
    message: Message,
    i18n: I18n,
    config: Config,
) -> None:
    lang = i18n.current_locale

    media_list = config.plan_files_id_uz
    if lang == 'ru':
        media_list = config.plan_files_id_ru

    await message.answer_media_group(
        media=[InputMediaPhoto(media=media) for media in media_list]
    )


async def main() -> None:
    config = load_config()

    bot = Bot(config.token, parse_mode=ParseMode.HTML)
    i18n = I18n(path="locales", default_locale="ru", domain="messages")
    dp.message.middleware(DatabaseMiddleware(config.db_uri))
    dp.message.outer_middleware(ConfigMiddleware(config))
    dp.message.outer_middleware(FSMI18nMiddleware(i18n=i18n))

    dp.include_router(forum_router)
    await dp.start_polling(bot)


async def process_registered(
    session: AsyncSession,
    user: types.User,
    organization: str,
    name: str,
    phone_number: str,
    date: str,
    hotel_info: bool
):
    db_user = DbUser(
        tg_id=user.id,
        username=user.username,
        organization=organization,
        name=name,
        phone_number=phone_number,
        date=date,
        hotel_info=hotel_info
    )
    session.add(db_user)
    await session.flush([db_user])


async def is_registered(
    session: AsyncSession,
    user: types.User
) -> bool:
    stmt = select(DbUser).filter(DbUser.tg_id == user.id)
    result = await session.scalars(stmt)
    return bool(result.all())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
