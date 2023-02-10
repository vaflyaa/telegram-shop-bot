from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from keyboards.default_markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message
from states.questions_state import QuestionState
from filters import IsUser
from loader import dp, db


@dp.message_handler(IsUser(), commands='help')
async def cmd_help(message: Message):
    await QuestionState.question.set()
    await message.answer('Опишите проблему как можно детальнее или задайте вопрос на интересующую Вас тему.\n\n'
                         'Администратор обязательно Вам ответит.', reply_markup=ReplyKeyboardRemove())


@dp.message_handler(state=QuestionState.question)
async def process_question(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text

    await message.answer('Убедитесь, что все верно.', reply_markup=submit_markup())
    await QuestionState.next()


@dp.message_handler(lambda message: message.text not in [cancel_message, all_right_message], state=QuestionState.submit)
async def invalid_message(message: Message):
    await message.answer('Такого варианта не было.')


@dp.message_handler(text=cancel_message, state=QuestionState.submit)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(text=all_right_message, state=QuestionState.submit)
async def process_submit(message: Message, state: FSMContext):

    chat_id = message.chat.id

    if db.fetchone('SELECT * FROM questions WHERE chat_id=?', (chat_id, )) is None:
        async with state.proxy() as data:
            db.query('INSERT INTO questions(chat_id, question) VALUES (?, ?)', (chat_id, data['question']))

        await message.answer('Отправлено!', reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer('Превышен лимит на количество задаваемых вопросов.', reply_markup=ReplyKeyboardRemove())

    await state.finish()