from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from states.product_state import ProductState, CategoryState
from aiogram.types.chat import ChatActions
from keyboards.products_from_cart import product_markup
from handlers.menu import cart
from loader import dp, db, bot
from filters import IsUser


@dp.message_handler(IsUser(), text=cart)
async def show_cart(message: Message, state: FSMContext):

    cart_data = db.fetchall('SELECT * FROM cart WHERE chat_id=?', (message.chat.id,))

    if len(cart_data) == 0:
        await message.answer('Ваша корзина пуста.')
    else:
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        async with state.proxy() as data:
            data['products'] = {}

        order_cost = 0

        for _, idx, count_in_cart in cart_data:
            product = db.fetchone('SELECT * FROM products WHERE idx=?', (idx,))

            if product is None:
                db.query('DELETE FROM cart WHERE idx=?', (idx,))
            else:
                _, _, title, descr, image, price = product
                order_cost += price

                markup = product_markup(idx, count_in_cart)
                text = f'<b>{title}</b>\n\n{descr}\n\nЦена: {price}₽.'

                await message.answer_photo(photo=image, caption=text, reply_markup=markup)