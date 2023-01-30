from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from loader import dp
from filters import IsUser, IsAdmin

catalog = 'Каталог'
get_order = 'Заказать работу'

settings = 'Настройка каталога'
orders = 'Заказы'
questions = 'Вопросы'


@dp.message_handler(IsUser(), commands='menu')
async def menu_user(message: Message):
    user_buttons = ReplyKeyboardMarkup(selective=True)
    user_buttons.add(catalog, get_order)

    await message.answer('Меню', reply_markup=user_buttons)


@dp.message_handler(IsAdmin(), commands='menu')
async def menu_user(message: Message):
    admin_buttons = ReplyKeyboardMarkup(selective=True)
    admin_buttons.add(settings, orders, questions)

    await message.answer('Меню', reply_markup=admin_buttons)