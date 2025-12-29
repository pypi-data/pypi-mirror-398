from asyncio import sleep
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from xync_schema import models

from xync_bot.routers.pay.dep import edt, fmt_sec
from xync_bot.routers.pay import cd, dep
from xync_bot.store import Store


async def type_select(msg: Message, store: Store):
    """Step 1: Select type"""
    uid = msg.from_user.id
    ist: bool = store.pers[uid].curr.is_target
    rm = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Банковская валюта", callback_data=cd.MoneyType(is_fiat=1, is_target=ist).pack()
                ),
                InlineKeyboardButton(
                    text="Крипта",
                    callback_data=cd.MoneyType(is_fiat=0, is_target=store.pers[uid].curr.is_target).pack(),
                ),
            ]
        ]
    )
    if store.pers[uid].curr.is_target:
        txt = "Что нужно?"
    else:
        if store.pers[uid].pay.t_coin_id:
            inf = f"{store.glob.coins[store.pers[uid].pay.t_coin_id]} на {store.glob.exs[store.pers[uid].pay.t_ex_id]}:{store.pay.addr_id}"
        else:
            cur = store.glob.curs[store.pay.t_cur_id].ticker
            cred: models.Cred = store.pers[uid].creds[store.pay.cred_id]
            inf = f"{cur} на {store.glob.pmcurs[store.pay.t_pmcur_id]}: {cred.repr()}"
        txt = f"Нужен платеж: {store.pay.amount} {inf}\nЧем будете платить?"
    if store.pers[uid].msg_id:
        await edt(msg, txt, rm)
    else:
        msg = await msg.answer(txt, reply_markup=rm)
        store.pers[uid].msg_id = msg.message_id


async def cur_select(msg: Message, store: Store):
    """Common using cur func"""
    builder = InlineKeyboardBuilder()
    ist: bool = store.curr.is_target
    for cur_id, cur in store.glob.curs.items():
        builder.button(text=cur.ticker + dep.flags[cur.ticker], callback_data=cd.Cur(id=cur_id, is_target=ist))
    builder.button(text="Назад к выбору типа", callback_data=cd.PayNav(to=cd.PayStep.t_type))
    builder.adjust(3, 3, 3, 3, 3, 1)
    sfx = "ую нужно" if ist else "ой платишь"
    await edt(msg, "Выбери валюту котор" + sfx, builder.as_markup())


async def coin_select(msg: Message, store: Store):
    """Common using coin func"""
    builder = InlineKeyboardBuilder()
    for coin_id, ticker in store.glob.coins.items():
        builder.button(text=ticker, callback_data=cd.Coin(id=coin_id, is_target=store.curr.is_target))
    builder.button(
        text="Назад к выбору типа",
        callback_data=cd.PayNav(to=cd.PayStep.t_type if store.curr.is_target else cd.PayStep.s_type),
    )
    builder.adjust(1)
    sfx = "ую нужно" if store.curr.is_target else "ой платишь"
    await msg.edit_text("Выберите монету котор" + sfx, reply_markup=builder.as_markup())


async def ex_select(msg: Message, store: Store):
    ist = store.curr.is_target
    coin_id = getattr(store.pay, ("t" if ist else "s") + "_coin_id")
    builder = InlineKeyboardBuilder()
    for ex_id in store.glob.coinexs[coin_id]:
        builder.button(text=store.glob.exs[ex_id], callback_data=cd.Ex(id=ex_id, is_target=ist))
    builder.button(
        text="Назад к выбору монеты", callback_data=cd.PayNav(to=cd.PayStep.t_coin if ist else cd.PayStep.s_coin)
    )
    builder.button(text="Домой", callback_data=cd.PayNav(to=cd.PayStep.t_type))
    builder.adjust(1)
    keyboard = builder.as_markup()
    await msg.edit_text("На какую биржу?" if ist else "С какой биржи?", reply_markup=keyboard)


async def pm(msg: Message, store: Store):
    ist = store.curr.is_target
    cur_id = getattr(store.pay, ("t" if ist else "s") + "_cur_id")
    builder = InlineKeyboardBuilder()
    for pmcur_id in store.glob.curpms[cur_id]:
        builder.button(text=store.glob.pmcurs[pmcur_id], callback_data=cd.Pm(pmcur_id=pmcur_id, is_target=ist))
    builder.button(
        text="Назад к выбору валюты", callback_data=cd.PayNav(to=cd.PayStep.t_cur if ist else cd.PayStep.s_cur)
    )
    builder.button(text="Домой", callback_data=cd.PayNav(to=cd.PayStep.t_type))
    builder.adjust(1)
    keyboard = builder.as_markup()
    await msg.edit_text("На какую платежную систему?" if ist else "C какой платежной системы?", reply_markup=keyboard)


async def fill_cred_dtl(msg: Message, store: Store):
    uid = msg.from_user.id
    builder = InlineKeyboardBuilder()
    txt = "В"
    if cred_ids := store.pers[uid].cur_creds.get(store.pay.t_pmcur_id):
        for cred_id in cred_ids:
            cred = store.pers[uid].creds[cred_id]
            builder.button(text=cred.repr(), callback_data=cd.Cred(id=cred_id))
        txt = "Выберите реквизиты куда нужно получить деньги, если в списке нет нужных, то\nв"

    builder.button(text="Назад к выбору платежной системы", callback_data=cd.PayNav(to=cd.PayStep.t_pm))
    builder.button(text="Домой", callback_data=cd.PayNav(to=cd.PayStep.t_type))
    builder.adjust(2)

    await msg.edit_text(
        f"{txt}ведите номер для {store.glob.pmcurs[store.pay.t_pmcur_id]}:", reply_markup=builder.as_markup()
    )


async def fill_cred_name(msg: Message, store: Store):
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад к вводу реквизитов", callback_data=cd.PayNav(to=cd.PayStep.t_cred_dtl))
    builder.button(text="Домой", callback_data=cd.PayNav(to=cd.PayStep.t_type))
    builder.adjust(2)
    cur = store.glob.curs[store.pay.t_cur_id]
    payment = store.glob.pmcurs[store.pay.t_pmcur_id]
    detail = store.pay.cred_dtl
    await edt(msg, f"{cur.ticker}:{payment}:{detail}: Введите имя получателя", builder.as_markup())


async def amount(msg: Message, store: Store):
    """Step 5: Filling target amount"""
    builder = InlineKeyboardBuilder()
    if store.curr.is_fiat:
        cur_coin = store.glob.curs[store.pay.t_cur_id].ticker
        builder.button(text="Назад к вводу имени", callback_data=cd.PayNav(to=cd.PayStep.t_cred_name))
        t_name = store.glob.pmcurs[store.pay.t_pmcur_id]
    else:
        cur_coin = store.glob.coins[store.pay.t_coin_id]
        builder.button(text="Назад к выбору биржи", callback_data=cd.PayNav(to=cd.PayStep.t_ex))
        t_name = store.glob.exs[store.pay.t_ex_id]

    builder.button(text="Домой", callback_data=cd.PayNav(to=cd.PayStep.t_type))
    builder.adjust(2)

    await edt(msg, f"Введите нужную сумму {cur_coin} для {t_name}", builder.as_markup())


async def set_ppo(msg: Message, store: Store):
    ist = store.curr.is_target
    if nppo := await store.need_ppo():
        builder = InlineKeyboardBuilder()
        builder.button(text="Нет", callback_data=cd.Ppo(num=1, is_target=ist)).button(
            text="Да", callback_data=cd.Ppo(num=2, is_target=ist)
        )
        if nppo > 1:
            builder.button(text="Да хоть 3мя", callback_data=cd.Ppo(num=3, is_target=ist))
        builder.adjust(2)
        await edt(msg, f"2мя платежами сможете {'принять' if ist else 'отравить'}?", builder.as_markup())
    elif ist:
        store.curr.is_target = False
        await type_select(msg)
    else:
        await set_urgency(msg)


async def set_urgency(msg: Message, store: Store):
    if not store.curr.is_fiat or await store.client_have_coin_amount():
        return await create_payreq(msg)  # next
    builder = InlineKeyboardBuilder()
    (
        builder.button(text="1 мин", callback_data=cd.Time(minutes=1))
        .button(text="5 мин", callback_data=cd.Time(minutes=5))
        .button(text="30 мин", callback_data=cd.Time(minutes=30))
        .button(text="3 часа", callback_data=cd.Time(minutes=180))
        .button(text="сутки", callback_data=cd.Time(minutes=60 * 24))
        .button(text="Назад к выбору платежной\nсистемы для отправки", callback_data=cd.PayNav(to=cd.PayStep.s_pm))
        .button(text="Домой", callback_data=cd.PayNav(to=cd.PayStep.t_type))
        .adjust(2, 2, 1, 1, 1)
    )
    return await edt(msg, "Сколько можешь ждать?", builder.as_markup())


async def create_payreq(msg: Message, store: Store):
    uid = msg.from_user.id
    pay_req, _ = await models.PayReq.update_or_create(
        {"pay_until": datetime.now() + timedelta(minutes=store.pay.urg)},
        amount=store.pay.amount,
        parts=store.pay.ppo,
        addr_id=store.pay.addr_id,
        cred_id=store.pay.cred_id,
        user=store.pers[uid].user,
    )
    store.pay.pr_id = pay_req.id
    inp, txt = await store.get_merch_target()
    ccred, ctxt = await store.client_target_repr()
    txt += f"\nИ получите {store.pay.amount} {ctxt} в течение {fmt_sec(store.pay.urg * 60)}"
    if store.pay.ppo > 1:
        txt += f" максимум {store.pay.ppo} платежами"
    rm = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отправил", callback_data=cd.Action(act=cd.ActionType.sent).pack())],
        ]
    )
    await edt(msg, f"Отправьте {100500} " + txt, rm)  # todo: get rate

    # create_task(window.run_timer(msg))В


async def run_timer(msg, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="Платеж получен", callback_data=cd.Action(act=cd.ActionType.received))

    seconds = await state.get_value("timer") * 60

    try:
        await msg.edit_text(f"⏳ Осталось {fmt_sec(seconds)}", reply_markup=builder.as_markup())
    except Exception:
        return

    while seconds > 0:
        await sleep(1)
        seconds -= 1
        try:
            await msg.edit_text(f"⏳ Осталось {fmt_sec(seconds)}", reply_markup=builder.as_markup())
            await state.update_data(timer=seconds)
        except Exception:
            break

    if seconds <= 0:
        builder = InlineKeyboardBuilder()
        builder.button(text="Платеж получен", callback_data=cd.Action(act=cd.ActionType.received))
        builder.button(text="Денег нет", callback_data=cd.Action(act=cd.ActionType.not_received))
        try:
            await msg.edit_text("⏳ Время вышло!", reply_markup=builder.as_markup())
        except Exception:
            pass


async def success(msg: Message):
    rm = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Новый платеж💸", callback_data=cd.PayNav(to=cd.PayStep.t_type).pack())]
        ]
    )
    await msg.edit_text("✅ Платеж успешно подтвержден", reply_markup=rm)
