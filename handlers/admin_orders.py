from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from filters import IsAdmin
from handlers.menu import orders
from loader import dp, db


@dp.message_handler(IsAdmin(), text=orders)
async def show_orders(message: Message):

    db_orders = db.fetchall('SELECT * FROM orders')

    if len(db_orders) == 0:
        await message.answer('У Вас нет заказов.')
    else:
        answer = ''
        for order in db_orders:
            answer += f'Заказ <b>№{order[3]}</b>\n\n'

        await message.answer(answer)