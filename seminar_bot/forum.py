from aiogram import Router, F, types, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from seminar_bot.config import Config
from seminar_bot.filters import IsAdmin
from seminar_bot.keyboards import get_meu_kb
from seminar_bot.state import Menu

router = Router()

speakers = (
    "Hosameldin Abdelhafez",
    "Mohamed Ali",
    "Gintaras Budginas",
    "Tigran Aydinyan",
    "Norbert Mischke",
    "Slausgalvis Virginijus"
)


def extract_id(message: types.Message) -> int:

    entities = message.entities or message.caption_entities

    if not entities or entities[-1].type != "hashtag":
        raise ValueError("Не удалось извлечь ID для ответа!")

    hashtag = entities[-1].extract_from(message.text or message.caption)
    if len(hashtag) < 4 or not hashtag[3:].isdigit():
        raise ValueError("Некорректный ID для ответа!")

    return int(hashtag[3:])


@router.message(Menu.menu, F.text == __("Задать вопрос"))
async def ask_question(
    message: types.Message,
    state: FSMContext
):

    await message.answer(
        _("Выберите спикера, которому вы хотите задать вопрос"),
        reply_markup=types.ReplyKeyboardMarkup(keyboard=[
            *[[types.KeyboardButton(text=speaker)] for speaker in speakers],
            [types.KeyboardButton(text=_("Отмена"))]
        ], resize_keyboard=True)
    )

    await state.set_state(Menu.choose_speaker)


@router.message(Menu.choose_speaker)
async def choose_speaker(
    message: types.Message,
    state: FSMContext
):
    text = message.text
    if text not in speakers:
        await message.answer(_(
            "Некорректный ввод. Выберите спикера из списка ниже"
        ))
        return
    data = await state.get_data()
    await state.set_data({
        **data,
        "speaker": text
    })
    await message.answer(
        _("Введите свой вопрос"),
        reply_markup=types.ReplyKeyboardMarkup(keyboard=[
            [types.KeyboardButton(text=_("Отмена"))]
        ], resize_keyboard=True)
    )

    await state.set_state(Menu.send_question)


@router.message(Menu.send_question, F.text)
async def text_question(
    message: types.Message,
    config: Config,
    bot: Bot,
    state: FSMContext
):
    if len(message.text) > 4000:
        return await message.reply(
            _("Сообщение слишком длинное")
        )

    speaker = (await state.get_data())["speaker"]
    await bot.send_message(
        config.admin_chat_id,
        f"Спикер: {speaker}\n\n"
        + message.html_text
        + f"\n\n#id{message.from_user.id}",
        parse_mode="HTML"
    )
    await message.answer(
        _("Сообщение отправлено. Скоро мы ответим"),
        reply_markup=get_meu_kb()
    )
    await state.set_state(Menu.menu)


@router.message(
    F.reply_to_message,
    IsAdmin()
)
async def reply_to_user(
    message: types.Message,
    config: Config
):
    if message.chat.id != config.admin_chat_id:
        pass

    try:
        user_id = extract_id(message.reply_to_message)
    except ValueError as ex:
        return await message.reply(str(ex))

    try:
        await message.copy_to(user_id)
    except TelegramAPIError as ex:
        await message.reply("Не удалось ответить на сообщение")
    else:
        await message.reply("Сообщение доставлено")
