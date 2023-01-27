from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from loader import bot, dp


user_message = 'Пользователь'
admin_message = 'Админ'


@dp.message_handler(commands='start')
async def start_handler(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(user_message, admin_message)

    await message.answer('''Привет!

Я бот-магазин по продаже товаров разных категорий. 

/menu - чтобы перейти в каталог и выбрать товар.

/help - поможет связаться с админами, если есть вопросы.''')

if __name__ == '__main__':
    executor.start_polling(dp)
