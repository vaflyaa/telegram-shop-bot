from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message
from config import ADMINS


class IsUser(BoundFilter):
    
    async def check(self, message: Message):
        return message.from_user.id not in ADMINS
