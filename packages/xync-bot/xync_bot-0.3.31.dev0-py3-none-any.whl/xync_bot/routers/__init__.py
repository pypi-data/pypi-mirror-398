import logging

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

last = Router(name="last")


@last.message(
    F.content_type.not_in(
        {
            ContentType.NEW_CHAT_MEMBERS,
            # ContentType.LEFT_CHAT_MEMBER,
            # ContentType.SUPERGROUP_CHAT_CREATED,
            # ContentType.NEW_CHAT_PHOTO,
            # ContentType.FORUM_TOPIC_CREATED,
            # ContentType.FORUM_TOPIC_EDITED,
            ContentType.FORUM_TOPIC_CLOSED,
            # ContentType.GENERAL_FORUM_TOPIC_HIDDEN, # deletable
        }
    )
)
async def del_cbq(msg: Message):
    try:
        await msg.delete()
        logging.info({"DELETED": msg.model_dump(exclude_none=True)})
    except TelegramBadRequest:
        logging.error({"NOT_DELETED": msg.model_dump(exclude_none=True)})


@last.message()
async def all_rest(msg: Message):
    logging.warning(
        {
            "NO_HANDLED": msg.model_dump(
                exclude_none=True,
            )
        }
    )
