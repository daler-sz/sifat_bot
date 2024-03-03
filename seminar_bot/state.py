from aiogram.fsm.state import StatesGroup, State


class Menu(StatesGroup):
    choose_language = State()
    menu = State()
    choose_speaker = State()
    send_question = State()
    send_name = State()
    send_organization = State()
    send_phone_number = State()
    send_hotel_info = State()
    send_date = State()
    main_menu = State()
