from asyncio import gather
from enum import IntEnum

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup
from pyrogram.types import CallbackQuery
from x_model.func import ArrayAgg
from xync_schema import models


class Report(StatesGroup):
    text = State()


class CredState(StatesGroup):
    detail = State()
    name = State()


class PaymentState(StatesGroup):
    amount = State()
    timer = State()
    timer_active = State()


class ActionType(IntEnum):
    """Цель (назначение) платежа (target)"""

    sent = 1  # Отправил
    received = 2  # Получил
    not_received = 3  # Не получил


class PayStep(IntEnum):
    """Цель (назначение) платежа (target)"""

    t_type = 1  # Выбор типа
    t_cur = 2  # Выбор валюты
    t_coin = 3  # Выбор монеты
    t_pm = 4  # Выбор платежки
    t_ex = 5  # Выбор биржи
    t_cred_dtl = 6  # Ввод номера карты
    t_cred_name = 7  # Ввод имени
    # t_addr = 8 # todo: позже добавим: Выбор/ввод крипто кошелька
    t_amount = 9  # Ввод суммы
    """ Источник платежа (source) """
    s_type = 10  # Выбор типа
    s_cur = 11  # Выбор типа
    s_pm = 12  # Выбор типа
    s_coin = 13  # Выбор типа
    s_ex = 14  # Выбор типа
    ppo = 15  # Выбор возможности разбивки платежа
    urgency = 16  # Выбор срочности получения платежа
    pending_send = 17  # Ожидание отправки (если мы платим фиатом)
    pending_confirm = 18  # Ожидание пока на той стороне подтвердят получение нашего фиата (если мы платим фиатом)
    pending_receive = 19  # Ожидание поступления (если мы получаем фиат)


async def fill_creds(person_id: int) -> tuple[dict[int, models.Cred], dict[int, list[int]]]:
    cq = models.Cred.filter(person_id=person_id)
    creds = {c.id: c for c in await cq}
    cur_creds = {
        pci: ids
        for pci, ids in await cq.annotate(ids=ArrayAgg("id")).group_by("pmcur_id").values_list("pmcur_id", "ids")
    }
    return creds, cur_creds


async def fill_actors(person_id: int) -> dict[int, int]:
    ex_actors = {
        # todo: check len(ids) == 1
        exi: ids[0]
        for exi, ids in await models.Actor.filter(person_id=person_id)
        .annotate(ids=ArrayAgg("id"))
        .group_by("ex_id")
        .values_list("ex_id", "ids")
    }
    return ex_actors


async def edit(msg: Message, txt: str, rm: InlineKeyboardMarkup):
    await gather(msg.edit_text(txt), msg.edit_reply_markup(reply_markup=rm))


async def ans(cbq: CallbackQuery, txt: str = None):
    await cbq.answer(txt, cache_time=0)


async def dlt(msg: Message):
    await msg.delete()


async def edt(msg: Message, txt: str, rm: InlineKeyboardMarkup):
    if msg.message_id == msg.bot.store.perm.msg_id:
        await msg.edit_text(txt, reply_markup=rm)
    else:  # окно вызвано в ответ на текст, а не кнопку
        try:
            await msg.bot.edit_message_text(
                txt, chat_id=msg.chat.id, message_id=msg.bot.store.perm.msg_id, reply_markup=rm
            )
        except TelegramBadRequest as e:
            print(msg.bot.store.perm.msg_id, e)


def fmt_sec(sec: int):
    days = sec // (24 * 3600)
    sec %= 24 * 3600
    hours = sec // 3600
    sec %= 3600
    minutes = sec // 60
    sec %= 60

    if days > 0:
        return f"{days}д {hours:02d}:{minutes:02d}:{sec:02d}"
    elif hours > 0:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    else:
        return f"{minutes:02d}:{sec:02d}"
