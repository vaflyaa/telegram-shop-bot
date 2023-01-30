from aiogram import Bot, Dispatcher
from settings import settings

bot = Bot(token=settings.bots.bot_token)
dp = Dispatcher(bot)