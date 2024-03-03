from aiogram import types
from aiogram.utils.i18n import gettext as _


def get_meu_kb() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(
                text=_("Программа семинара"),
            )],
            [types.KeyboardButton(
                text=_("Зарегистрироваться")
            )],
            [types.KeyboardButton(
                text=_("Задать вопрос")
            )],
            [types.KeyboardButton(
                text=_("Изменить язык")
            )]
        ],
        resize_keyboard=True
    )


def cancel_kb_btn():
    return types.KeyboardButton(text=_("Отмена"))


def cancel_kb():
    return types.ReplyKeyboardMarkup(keyboard=[
        [cancel_kb_btn()],
    ], resize_keyboard=True)
