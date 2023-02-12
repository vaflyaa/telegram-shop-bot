from aiogram.types import Message, CallbackQuery
from keyboards.categories import categories_markup, category_cb
from keyboards.products_from_catalog import product_markup, product_cb
from aiogram.types.chat import ChatActions
from filters import IsUser
from loader import dp, db, bot
from .menu import catalog


@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    await message.answer('Выберите раздел, чтобы вывести список товаров:',
                         reply_markup=categories_markup())


@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):

    products = db.fetchall('''SELECT * FROM products p
    WHERE p.tag = (SELECT title FROM categories WHERE idx=?) 
    AND p.idx NOT IN (SELECT idx FROM cart WHERE chat_id = ?)''',
                           (callback_data['id'], query.message.chat.id))

    await query.answer('Все доступные товары.')
    await show_products(query.message, products)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery, callback_data: dict):

    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))

    await query.answer('Товар добавлен в корзину!')
    await query.message.delete()


async def show_products(m, products):

    if len(products) == 0:

        await m.answer('Здесь ничего нет 😢')

    else:

        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        for idx, _, title, descr, image, price, in products:

            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{descr}'

            await m.answer_photo(photo=image, caption=text, reply_markup=markup)


