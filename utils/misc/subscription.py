from typing import Union
from aiogram import Bot
from loader import channel_db

from aiogram.utils.exceptions import ChatNotFound, Unauthorized
from loader import bot

async def check(user_id: int, channel: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status in ['left', 'kicked']:
            return False
        else:
            return True
    except (ChatNotFound, Unauthorized):
        return False
