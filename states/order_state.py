from aiogram.dispatcher.filters.state import StatesGroup, State


class OrderState(StatesGroup):
    check = State()
    name = State()
    address = State()
    confirm = State()