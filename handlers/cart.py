from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from states.order_state import OrderState
from aiogram.types.chat import ChatActions
from keyboards.default_markups import *
from keyboards.products_from_cart import product_markup, product_cb
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

                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart]

                markup = product_markup(idx, count_in_cart)
                text = f'<b>{title}</b>\n\n{descr}\n\nЦена: {price}₽.'

                await message.answer_photo(photo=image, caption=text, reply_markup=markup)

        if order_cost != 0:
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('📦 Оформить заказ')

            await message.answer('Перейти к оформлению?', reply_markup=markup)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='count'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='decrease'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='increase'))
async def change_quantity(query: CallbackQuery, callback_data: dict, state: FSMContext):
    idx = callback_data['id']
    action = callback_data['action']

    if action == 'count':

        async with state.proxy() as data:

            if 'products' not in data.keys():
                await show_cart(query.message, state)
            else:
                await query.answer('Количество – ' + str(data['products'][idx][2]))

    else:

        async with state.proxy() as data:

            if 'products' not in data.keys():
                await show_cart(query.message, state)
            else:
                if action == 'increase':
                    data['products'][idx][2] += 1
                else:
                    data['products'][idx][2] -= 1
                count_id_cart = data['products'][idx][2]

                if count_id_cart == 0:
                    db.query('DELETE FROM cart WHERE chat_id=? AND idx=?', (query.message.chat.id, idx))
                    await query.message.delete()
                else:
                    db.query('UPDATE cart SET quantity=? WHERE chat_id=? AND idx=?', (count_id_cart, query.message.chat.id, idx))
                    await query.message.edit_reply_markup(product_markup(idx, count_id_cart))


@dp.message_handler(IsUser(), text='📦 Оформить заказ')
async def making_order(message: Message, state: FSMContext):
    await OrderState.check.set()

    answer = ''
    total_price = 0

    async with state.proxy() as data:

        for title, price, count_in_cart in data['products'].values():

            tp = count_in_cart * price
            answer += f'<b>{title}</b> * {count_in_cart}шт. = {tp}₽\n'
            total_price += tp

    await message.answer(f'{answer}\nОбщая сумма заказа: {total_price}₽.', reply_markup=check_markup())


@dp.message_handler(IsUser(), lambda message: message.text not in [all_right_message, back_message], state=OrderState.check)
async def check_invalid(message: Message):
    await message.reply('Такого варианта не было.')


@dp.message_handler(IsUser(), text=back_message, state=OrderState.check)
async def back_from_check(message: Message, state: FSMContext):
    await state.finish()
    await show_cart(message, state)


@dp.message_handler(IsUser(), text=all_right_message, state=OrderState.check)
async def check_all_right(message: Message, state: FSMContext):
    await OrderState.next()
    await message.answer('Укажите свое имя.', reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=OrderState.name)
async def back_from_name(message: Message, state: FSMContext):
    await making_order(message, state)


@dp.message_handler(IsUser(), state=OrderState.name)
async def add_name(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['name'] = message.text

        if 'address' in data.keys():

            await confirm(message)
            await OrderState.confirm.set()

        else:

            await OrderState.next()
            await message.answer('Укажите Ваш адрес.', reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=OrderState.address)
async def back_from_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        await message.answer('Изменить имя с <b>' + data['name'] + '</b> на ...', reply_markup=back_markup())

    await OrderState.name.set()


@dp.message_handler(IsUser(), state=OrderState.address)
async def add_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['address'] = message.text

    await confirm(message)
    await OrderState.next()


async def confirm(message):
    await message.answer('Убедитесь, что все правильно оформлено и подтвердите заказ.', reply_markup=confirm_markup())


@dp.message_handler(IsUser(), lambda message: message.text not in [confirm_message, back_message], state=OrderState.confirm)
async def confirm_invalid(message: Message):
    await message.reply('Такого варианта не было.')


@dp.message_handler(IsUser(), text=back_message, state=OrderState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    await OrderState.address.set()

    async with state.proxy() as data:
        await message.answer('Изменить адрес с <b>' + data['address'] + '</b> на ...', reply_markup=back_markup())


@dp.message_handler(IsUser(), text=confirm_message, state=OrderState.confirm)
async def final_confirm(message: Message, state: FSMContext):

    markup = ReplyKeyboardRemove()

    async with state.proxy() as data:

        chat_id = message.chat.id
        cart_prods = db.fetchall('SELECT idx, quantity FROM cart WHERE chat_id=?''', (chat_id,))

        products = [idx + '=' + str(quantity) for idx, quantity in cart_prods]

        db.query('INSERT INTO orders VALUES (?, ?, ?, ?)', (chat_id, data['name'], data['address'], ' '.join(products)))

        db.query('DELETE FROM cart WHERE chat_id=?', (chat_id,))

        await message.answer('Ок! Ваш заказ уже в пути 🚀\nИмя: <b>' + data['name'] + '</b>\nАдрес: <b>' + data['address'] + '</b>',
                             reply_markup=markup)

    await state.finish()