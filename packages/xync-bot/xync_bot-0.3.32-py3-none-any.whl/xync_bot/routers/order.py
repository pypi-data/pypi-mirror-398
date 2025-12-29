from aiogram import Router, F
from aiogram.types import Message
from xync_schema.models import User

r = Router()


# @main.message(F.chat.is_forum)
@r.message(F.is_topic_message)
async def order_msg(msg: Message):
    await User[msg.from_user.id]
    msg.message_thread_id
