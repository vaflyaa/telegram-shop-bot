from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message
from settings import settings


class IsUser(BoundFilter):
    
    async def check(self, message: Message):
        return message.from_user.id != settings.bots.admin_id
