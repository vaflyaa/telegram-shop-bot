import logging
import handlers
import filters
from aiogram import types, executor
from aiogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from loader import dp, bot
from settings import settings
# from settings import settings
# from keyboards import markups

user_message = 'Пользователь'
admin_message = 'Админ'

filters.setup(dp)

@dp.message_handler(commands='start')
async def start_handler(message: Message):

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(user_message, admin_message)

    await message.answer('''Привет!

Я бот-магазин по продаже товаров разных категорий. 

Выберите режим входа: ''', reply_markup=markup)


@dp.message_handler(text=user_message)
async def user_mode(message: Message):


    await message.answer('''Включен пользовательский режим. 

/menu - чтобы перейти в каталог и выбрать товар.

/info - получить информацию о нашей мастерской.

/help - поможет связаться с админами, если есть вопросы.''', reply_markup=ReplyKeyboardRemove())


@dp.message_handler(text=admin_message)
async def admin_mode(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(user_message, admin_message)

    u_id = message.from_user.id
    if u_id == settings.bots.admin_id:
        await message.answer('''Включен режим администратора.

/menu - чтобы выбрать дальнейшие действия''', reply_markup=ReplyKeyboardRemove())

    else:
        await message.answer('Вы не являетесь админом.', reply_markup=markup)

    
async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)


async def on_shutdown():
    logging.warning("Bot down")


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
