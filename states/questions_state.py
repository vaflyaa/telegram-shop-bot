from aiogram.dispatcher.filters.state import StatesGroup, State


class QuestionState(StatesGroup):
    question = State()
    submit = State()


class AnswerState(StatesGroup):
    answer = State()
    submit = State()
