from datetime import timedelta
from typing import Literal

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery
from tortoise.timezone import now

from xync_bot.shared import BoolCd
from xync_schema import models
from xync_schema.enums import HotStatus

hot = Router(name="hot")


class HotCd(CallbackData, prefix="hot"):
    typ: Literal["sell", "buy"]
    cex: int = 4


async def get_hot_db(uid: int) -> models.Hot:
    if not (
        hot_db := await models.Hot.filter(
            user__username_id=uid, updated_at__gt=now() - timedelta(hours=1), status=HotStatus.opened
        )
        .order_by("-created_at")
        .first()
        .prefetch_related("actors")
    ):
        hot_db = await models.Hot.create(user=await models.User.get(username_id=uid))
    return hot_db


async def find_hot_by_actor(aid: int) -> models.Hot | None:
    return (
        await models.Hot.filter(actors__id=aid, updated_at__gt=now() - timedelta(hours=1), status=HotStatus.opened)
        .order_by("-created_at")
        .first()
    )


@hot.message(Command("hot"))
async def start(msg: Message, xbt: "XyncBot"):  # noqa: F821
    await xbt.go_hot(msg.from_user.id, [4])


@hot.callback_query(BoolCd.filter(F.req.__eq__("is_you")))
async def is_you(query: CallbackQuery, callback_data: BoolCd, xbt: "XyncBot"):  # noqa: F821
    if not callback_data.res:
        return await query.answer("ok, sorry")
    person = await models.Person.get(user__username_id=query.from_user.id).prefetch_related("user")
    order = await models.Order.get(id=callback_data.xtr).prefetch_related("ad__pair_side__pair", "ad__my_ad")
    old_person: models.Person = await models.Person.get(actors=order.taker_id).prefetch_related(
        "actors", "user", "creds"
    )
    await order.taker.update(person=person)
    if old_person.user:
        raise ValueError(old_person)
    for actor in old_person.actors:
        actor.person = person
        await actor.save(update_fields=["person_id"])
    for cred in old_person.creds:
        cred.person = person
        await cred.save(update_fields=["person_id"])

    err, res = await order.hot_process(person.user)
    if err == 0:
        txt = f"bro, you can't buy more than {res * 0.01:.2f} now! Deposit to XyncPay or Sell more at first."
    elif err == 1:
        txt = "Accept the order now, bro!"
    elif err == 2:
        txt = f"Your XyncPay balance: {res * 0.01:.2f}"
        await xbt.go_hot(query.from_user.id, [4])

    await query.message.answer(txt)
    return await query.answer("ok")
