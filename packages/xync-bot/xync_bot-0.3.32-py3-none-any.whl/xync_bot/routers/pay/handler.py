from asyncio import gather
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from xync_bot.routers.pay.dep import fill_creds, fill_actors, dlt, ans
from xync_schema import models

from xync_bot.routers.pay import cd, dep, window
from xync_bot.store import Store

pr = Router(name="pay")


@pr.message(Command("pay"))
async def h_start(msg: Message, store: Store, **kwargs):
    """Step 1: Select a target type"""
    uid = msg.from_user.id
    store.pers[uid] = Store.Personal(1)
    store.pers[uid].curr.is_target = True
    await gather(window.type_select(msg, store), dlt(msg))
    store.pers[uid].user = await models.User.get(username_id=msg.from_user.id)
    store.pers[uid].creds, store.pers[uid].cur_creds = await fill_creds(store.pers[uid].user.person_id)
    store.pers[uid].actors = await fill_actors(store.pers[uid].user.person_id)


@pr.callback_query(cd.MoneyType.filter(F.is_fiat))
async def h_got_fiat_type(query: CallbackQuery, store: Store):
    """Step 2f: Select cur"""
    uid = query.from_user.id
    store.pers[uid].curr.is_fiat = True
    await gather(window.cur_select(query.message, store), ans(query, "Понял, фиат"))


@pr.callback_query(cd.MoneyType.filter(F.is_fiat.__eq__(0)))
async def h_got_crypto_type(query: CallbackQuery, store: Store):
    """Step 2c: Select coin"""
    store.pers.curr.is_fiat = False
    await gather(window.coin_select(query.message, store), ans(query, "Понял, крипта"))


@pr.callback_query(cd.Coin.filter())
async def h_got_coin(query: CallbackQuery, callback_data: cd.Coin, store: Store):
    """Step 3c: Select target ex"""
    setattr(store.pay, ("t" if store.pers.curr.is_target else "s") + "_coin_id", callback_data.id)
    await gather(window.ex_select(query.message, store), ans(query, "Эта монета есть на следующих биржах"))


@pr.callback_query(cd.Cur.filter())
async def h_got_cur(query: CallbackQuery, callback_data: cd.Cur, store: Store):
    """Step 3f: Select target pm"""
    setattr(store.pay, ("t" if store.pers.curr.is_target else "s") + "_cur_id", callback_data.id)
    await gather(window.pm(query.message, store), ans(query, "Вот платежные системы доступные для этой валюты"))


@pr.callback_query(cd.Pm.filter(F.is_target))
async def h_got_target_pm(query: CallbackQuery, callback_data: cd.Pm, state: FSMContext, store: Store):
    """Step 4f: Fill target cred.detail"""
    store.pay.t_pmcur_id = callback_data.pmcur_id
    await gather(
        window.fill_cred_dtl(query.message, store),
        ans(query, "Теперь нужны реквизиты"),
        state.set_state(dep.CredState.detail),
    )


@pr.callback_query(cd.Cred.filter())
async def h_got_cred(query: CallbackQuery, callback_data: cd.Cred, state: FSMContext, store: Store):
    store.pay.cred_id = callback_data.id
    await gather(
        window.amount(query.message, store), ans(query, "Теперь нужна сумма"), state.set_state(dep.PaymentState.amount)
    )


@pr.message(dep.CredState.detail)
async def h_got_cred_dtl(msg: Message, state: FSMContext, store: Store):
    """Step 4.1f: Fill target cred.name"""
    store.pay.cred_dtl = msg.text
    await gather(window.fill_cred_name(msg, store), dlt(msg), state.set_state(dep.CredState.name))


@pr.message(dep.CredState.name)
async def h_got_cred_name(msg: Message, state: FSMContext, store: Store):
    """Step 5f: Save target cred"""
    uid = msg.from_user.id
    cred, _ = await models.Cred.update_or_create(
        {"name": msg.text},
        detail=store.pay.cred_dtl,
        person_id=store.pers[uid].user.person_id,
        pmcur_id=store.pay.t_pmcur_id,
    )
    store.pay.cred_id = cred.id
    store.pers[uid].creds[cred.id] = cred
    await gather(window.amount(msg, store), dlt(msg), state.set_state(dep.PaymentState.amount))


@pr.callback_query(cd.Ex.filter())
async def h_got_ex(query: CallbackQuery, callback_data: cd.Ex, state: FSMContext, store: Store):
    """Step 4c: Save target"""
    uid = query.from_user.id
    ist = store.pers.curr.is_target
    setattr(store.pay, ("t" if ist else "s") + "_ex_id", callback_data.id)
    if ist:
        await window.amount(query.message, store)
        actor_id = store.pers[uid].actors[store.pay.t_ex_id]
        addr = await models.Addr.get(coin_id=store.pay.t_coin_id, actor_id=actor_id)
        store.pay.addr_id = addr.id
    else:
        await window.set_ppo(query.message, store)
    await ans(query, f"Биржа {store.glob.exs[callback_data.id]} выбрана")
    await state.set_state(dep.PaymentState.amount)


@pr.message(dep.PaymentState.amount)
async def h_got_amount(msg: Message, state: FSMContext, store: Store):
    """Step 6: Save a target amount"""
    if not msg.text.isnumeric():
        store.pers.curr.msg_to_del = await msg.answer("Пожалуйста, введите корректное число")
        return
    if store.pers.curr.msg_to_del:
        await store.pers.curr.msg_to_del.delete()
    store.pay.amount = float(msg.text)
    """Step 7: Select source type"""
    store.pers.curr.is_target = False
    await gather(
        (window.type_select if store.pers.curr.is_fiat else window.cur_select)(msg, store), dlt(msg), state.clear()
    )


@pr.callback_query(cd.Pm.filter(F.is_target.__eq__(0)))
async def h_got_source_pm(query: CallbackQuery, callback_data: cd.Pm, store: Store):
    store.pay.s_pmcur_id = callback_data.pmcur_id
    await gather(
        window.set_ppo(query.message, store),
        ans(query, store.glob.pmcurs[callback_data.pmcur_id]),
    )


@pr.callback_query(cd.Ppo.filter())
async def h_got_ppo(query: CallbackQuery, callback_data: cd.Ppo, store: Store):
    store.pay.ppo = callback_data.num
    await gather(window.set_urgency(query.message, store), ans(query, str(callback_data.num)))


@pr.callback_query(cd.Time.filter())
async def h_got_urgency(query: CallbackQuery, callback_data: cd.Time, store: Store):
    # payreq_id = store.pers[query.from_user.id].
    store.pay.urg = callback_data.minutes
    await window.create_payreq(query.message, store)
    await ans(query, f"Ok {callback_data.minutes} min.")


# ACTIONS
@pr.callback_query(cd.Action.filter(F.act.__eq__(cd.ActionType.received)))
async def payment_confirmed(query: CallbackQuery, state: FSMContext):
    await ans(query, None)
    payed_at = datetime.now()
    await state.update_data(timer_active=False, payed_at_formatted=payed_at)
    data = await state.get_data()
    if data.get("pay_req_id"):
        pay_req = await models.PayReq.get(id=data["pay_req_id"])
        pay_req.payed_at = payed_at
        await pay_req.save()
    await state.clear()
    await window.success(query.message)


@pr.callback_query(cd.Action.filter(F.act.__eq__(cd.ActionType.not_received)))
async def no_payment(query: CallbackQuery, state: FSMContext):
    await ans(query, None)
    await state.update_data(timer_active=False)
    await query.message.edit_text("Платеж не получен!")
    await query.message.answer("укажите детали платежа")
    await state.clear()
    await state.set_state(dep.Report.text)


@pr.message(dep.Report.text)
async def payment_not_specified(msg: Message, state: FSMContext):
    await state.update_data(text=msg.text)
    data = await state.get_data()
    complaint_text = (
        f"Жалоба на неполученный платеж:\n"
        f"Пользователь: @{msg.from_user.username or msg.from_user.id}\n"
        f"Детали платежа: {data['text']}\n"
        f"Время: {msg.date.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await msg.bot.send_message(chat_id="xyncpay", text=complaint_text)


# NAVIGATION
@pr.callback_query(cd.PayNav.filter(F.to.in_([cd.PayStep.t_type, cd.PayStep.s_type])))
async def handle_home(query: CallbackQuery, state: FSMContext, store: Store):
    await gather(window.type_select(query.message, store), state.clear(), ans(query, "Создаем платеж заново"))


@pr.callback_query(cd.PayNav.filter(F.to.in_([cd.PayStep.t_coin, cd.PayStep.s_coin])))
async def to_coin_select(query: CallbackQuery, state: FSMContext, store: Store):
    await ans(query, None)
    is_target = await state.get_value("is_target")
    pref = "t" if is_target else "s"
    await state.update_data({pref + "_ex_id": None, pref + "_coin_id": None})
    await window.coin_select(query.message, store)


@pr.callback_query(cd.PayNav.filter(F.to.in_([cd.PayStep.t_cur, cd.PayStep.s_cur])))
async def to_cur_select(query: CallbackQuery, state: FSMContext, store: Store):
    await ans(query, None)
    is_target = await state.get_value("is_target")
    pref = "t" if is_target else "s"
    await state.update_data({pref + "_pmcur_id": None, pref + "_cur_id": None})
    await window.cur_select(query.message, store)


@pr.callback_query(cd.PayNav.filter(F.to.in_([cd.PayStep.t_pm, cd.PayStep.s_pm])))
async def to_pm_select(query: CallbackQuery, store: Store):
    await ans(query, None)
    await window.pm(query.message, store)


@pr.callback_query(cd.PayNav.filter(F.to.__eq__(cd.PayStep.t_cred_dtl)))
async def back_to_cred_detail(query: CallbackQuery, state: FSMContext, store: Store):
    await ans(query, None)
    await state.update_data(detail=None)
    await window.fill_cred_dtl(query.message, store)


@pr.callback_query(cd.PayNav.filter(F.to.__eq__(cd.PayStep.t_cred_name)))
async def back_to_cred_name(query: CallbackQuery, state: FSMContext, store: Store):
    await ans(query, None)
    await state.update_data(name=None)
    await window.fill_cred_name(query.message, store)


@pr.callback_query(cd.PayNav.filter(F.to.in_([cd.PayStep.t_ex, cd.PayStep.s_ex])))
async def back_to_ex_select(query: CallbackQuery, state: FSMContext, store: Store):
    await ans(query, None)
    await state.update_data({("t" if await state.get_value("is_target") else "s") + "ex_id": None})
    await window.ex_select(query.message, store)


@pr.callback_query(cd.PayNav.filter(F.to.__eq__(cd.PayStep.t_amount)))
async def back_to_amount(query: CallbackQuery, state: FSMContext, store: Store):
    await ans(query, None)
    await state.update_data(amount=None)
    await window.amount(query.message, store)
    await state.set_state(dep.PaymentState.amount)


@pr.callback_query(cd.PayNav.filter(F.to.in_([cd.PayStep.t_pm])))
async def back_to_payment(query: CallbackQuery, state: FSMContext, store: Store):
    await ans(query, None)
    await state.update_data(payment=None)
    await window.pm(query.message, store)
