from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ContentType
from aiogram.utils.callback_data import CallbackData
from aiogram.types.chat import ChatActions

from states.product_state import ProductState, CategoryState
from keyboards.default_markups import *
from handlers.menu import settings
from loader import dp, db, bot
from filters import IsAdmin


category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'


@dp.message_handler(IsAdmin(), text=settings)
async def main_settings(message: Message):

    markup = InlineKeyboardMarkup()

    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton('+ Добавить категорию', callback_data='add_category'))

    await message.answer('Настройка категорий:', reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):

    category_idx = callback_data['id']

    products = db.fetchall('''SELECT * FROM products p
    WHERE p.tag = (SELECT title FROM categories WHERE idx=?)''', (category_idx,))

    await query.message.delete()
    await query.answer('Все товары, добавленные в эту категорию.')
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products, category_idx)


# add_category

@dp.callback_query_handler(IsAdmin(), text='add_category')
async def add_category_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Название категории?')
    await CategoryState.title.set()


@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):

    category = message.text
    await message.answer(f'{category}')
    db.query('INSERT INTO categories(title) VALUES (?)', (category,))

    await state.finish()
    await main_settings(message)


# delete_category

@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):

    async with state.proxy() as data:

        if 'category_index' in data.keys():

            idx = data['category_index']

            db.query(
                'DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)', (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await main_settings(message)


# add product

@dp.message_handler(IsAdmin(), text=add_product)
async def process_add_product(message: Message):
    await ProductState.title.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)

    await message.answer('Введите название товара.', reply_markup=markup)


@dp.message_handler(IsAdmin(), text=cancel_message, state=ProductState.title)
async def cancel_add_product(message: Message, state: FSMContext):

    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await main_settings(message)


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.title)
async def back_from_title(message: Message, state: FSMContext):
    await process_add_product(message)


@dp.message_handler(IsAdmin(), state=ProductState.title)
async def add_title_product(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['title'] = message.text

    await ProductState.next()
    await message.answer('Введите описание товара.', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.descr)
async def back_from_descr(message: Message, state: FSMContext):

    await ProductState.title.set()

    async with state.proxy() as data:
        await message.answer(f"Меняем название с <b>{data['title']}</b> на ...", reply_markup=back_markup())


@dp.message_handler(IsAdmin(), state=ProductState.descr)
async def add_descr_product(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['descr'] = message.text

    await ProductState.next()
    await message.answer('Отправьте фото товара.', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO, state=ProductState.image)
async def add_img_product(message: Message, state: FSMContext):

    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    async with state.proxy() as data:
        data['image'] = downloaded_file

    await ProductState.next()
    await message.answer('Введите цену.', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.TEXT, state=ProductState.image)
async def invalid_image_or_back_to_descr(message: Message, state: FSMContext):

    if message.text == back_message:
        await ProductState.descr.set()

        async with state.proxy() as data:
            await message.answer(f"Изменить описание с <b>{data['descr']}</b> на ...", reply_markup=back_markup())
    else:
        await message.answer('Вам нужно прислать ФОТО товара.')


@dp.message_handler(IsAdmin(), lambda message: not message.text.isdigit(), state=ProductState.price)
async def invalid_price_or_back_to_image(message: Message, state: FSMContext):

    if message.text == back_message:
        await ProductState.image.set()

        async with state.proxy() as data:
            await message.answer("Другое изображение?", reply_markup=back_markup())
    else:
        await message.answer('Укажите цену в виде числа!')


@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(), state=ProductState.price)
async def add_price_product(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['price'] = message.text

        title = data['title']
        descr = data['descr']
        price = data['price']

        await ProductState.next()

        text = f'<b>{title}</b>\n\n{descr}\n\nЦена: {price} рублей.'
        markup = check_markup()

        await message.answer_photo(photo=data['image'], caption=text, reply_markup=markup)


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.confirm)
async def back_from_confirm(message: Message, state: FSMContext):

    await ProductState.price.set()

    async with state.proxy() as data:
        await message.answer(f"Изменить цену с <b>{data['price']}</b> на ...", reply_markup=back_markup())


@dp.message_handler(IsAdmin(), lambda message: message.text not in [back_message, all_right_message], state=ProductState.confirm)
async def invalid_confirm(message: Message, state: FSMContext):
    await message.answer('Такого варианта не было.')


@dp.message_handler(IsAdmin(), state=ProductState.confirm)
async def confirm_add_product(message: Message, state: FSMContext):

    async with state.proxy() as data:
        title = data['title']
        descr = data['descr']
        image = data['image']
        price = int(data['price'])
        tag = db.fetchone('SELECT title FROM categories WHERE idx=?', (data['category_index'],))[0]

        db.query('INSERT INTO products(tag, title, descr, photo, price) VALUES (?, ?, ?, ?, ?)',
                 (tag, title, descr, image, price))

    await state.finish()
    await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
    await main_settings(message)


# delete product

@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict):

    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Удалено!')
    await query.message.delete()


async def show_products(m, products, category_idx):

    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

    for idx, tag, title, descr, image, price in products:

        text = f'<b>{title}</b>\n\n{descr}\n\nЦена: {price} рублей.'

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('🗑️ Удалить', callback_data=product_cb.new(id=idx, action='delete')))

        await m.answer_photo(photo=image, caption=text, reply_markup=markup)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(add_product) 
    markup.add(delete_category)

    await m.answer('Хотите что-нибудь добавить или удалить?', reply_markup=markup)
