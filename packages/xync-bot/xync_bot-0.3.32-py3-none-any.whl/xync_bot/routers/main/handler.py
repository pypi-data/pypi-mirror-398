import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    User,
    ChatMemberUpdated,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    WebAppInfo,
)
from aiogram.utils.deep_linking import create_start_link
from xync_schema import models

from xync_bot.shared import NavCallbackData

mr = Router(name="main")

txt = "Добро пожаловать в XyncPay, приветственный бонус: комиссия 0% на первые $10 000"
url = "https://pay.xync.net"
rm = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Pay", web_app=WebAppInfo(url=url))]])


class RrCallbackData(CallbackData, prefix="reg_res"):  # registration response
    to: int
    res: bool


home_btns = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Transfer", callback_data=NavCallbackData(to="transfer").pack()),
            InlineKeyboardButton(text="Invite", callback_data=NavCallbackData(to="ref_link").pack()),
            InlineKeyboardButton(text="Get VPN", callback_data=NavCallbackData(to="get_vpn").pack()),
        ]
    ]
)


# @mr.message(CommandStart(deep_link=True, deep_link_encoded=True))
# async def start_handler(msg: Message, command: CommandObject):
#     me: User = msg.from_user
#     ref_id: int = command.args.isnumeric() and int(command.args)
#     user = await models.User.get(username_id=me.id, blocked=False)
#     rm = None
#     logging.info(msg, {"src": "start"})
#     if user:
#         rs, rm = f"{me.full_name}, you have registered already😉", home_btns
#     elif not (ref := await models.User.get_or_none(id=ref_id)):
#         rs = f"No registered user #{ref_id}😬"
#     else:  # new user created
#         user, cr = await models.User.tg_upsert(me, False)
#         await user.update_from_dict({"ref": ref}).save()
#         approve_btns = InlineKeyboardMarkup(
#             inline_keyboard=[
#                 [
#                     InlineKeyboardButton(text="Отклонить", callback_data=RrCallbackData(to=user.id, res=False).pack()),
#                     InlineKeyboardButton(text="Одобрить", callback_data=RrCallbackData(to=user.id, res=True).pack()),
#                 ]
#             ]
#         )
#         await msg.bot.send_message(
#             ref.id, f"{me.full_name} просит что б Вы взяли за него/ее ответственность", reply_markup=approve_btns
#         )
#         return await msg.answer(f"Please wait for @{ref.username} approving...")
#     return await msg.answer(rs, reply_markup=rm)


@mr.message(CommandStart(deep_link=True))  # attempt to reg by fake link
async def arg_handler(msg: Message, command: CommandObject):
    logging.warning(f"Start: {msg.from_user.id}. Msg: {msg}")
    if command.args == "hot":
        return await msg.bot.go_hot()
    arg: dict[str, int | str] = {"id": int(command.args)} if command.args.isnumeric() else {"username": command.args}
    if ref := await models.Username.get_or_none(**arg):
        txt = f"Вас пригласил {ref.username and '@' + ref.username or ref.id}, бонус: комиссия 0% на первые $100 000"
    else:
        txt = f"Привет, {msg.from_user.full_name}! \nWelcome бонус: комиссия 0% на первые $10 000"
    await msg.answer(txt, reply_markup=rm, parse_mode="Markdown")


@mr.message(CommandStart())  # обычный /start
async def home(msg: Message):
    me = msg.from_user
    await models.User.tg_upsert(me, False)
    await msg.answer(txt, reply_markup=rm, parse_mode="Markdown")


@mr.callback_query(RrCallbackData.filter())
async def phrases_input_request(cb: CallbackQuery, callback_data: RrCallbackData) -> None:
    protege = await models.User[callback_data.to]
    if callback_data.res:
        # protege.status = UserStatus.RESTRICTED
        await protege.save()
        rs = f"{cb.from_user.full_name}, теперь Вы несете ответветвенность за {protege.username}"
    else:
        rs = f'Вы отклонили запрос юзера "{protege.username}" на Вашу протекцию'
    res = {True: "одобрил", False: "отклонил"}
    txt = f"{cb.from_user.full_name} {res[callback_data.res]} вашу регистрацию"
    txt, rm = (f"Поздравляем! {txt}💥", home_btns) if callback_data.res else (f"К сожалению {txt}😢", None)
    await cb.bot.send_message(protege.id, txt, reply_markup=rm)
    await cb.answer("👌🏼")
    await cb.message.edit_text(rs)


@mr.callback_query(NavCallbackData.filter(F.to.__eq__("ref_link")))
async def ref_link_handler(cbq: CallbackQuery):
    me = cbq.from_user
    if not (u := await models.User.get_or_none(id=me.id, blocked=False).prefetch_related("ref")):
        return await cbq.answer(f"{me.full_name}, сначала сами получите одобрение поручителя😉")
    link = await create_start_link(cbq.bot, str(u.id), encode=True)
    logging.info(f"Start: {me.id}. Msg: {cbq}")
    await cbq.message.answer(
        f"Your referrer is {u.ref_id and u.ref.username}"
        f"\nThis is your invite link: {link}"
        f"\nGive it to your protege, and approve his request"
    )
    await cbq.answer("Wait for your protege request..")


@mr.my_chat_member(F.chat.type == "private")  # my_chat_member is fired on adding bot to any chat. filter for preventing
async def my_user_set_status(my_chat_member: ChatMemberUpdated):
    logging.info({"my_chat_member": my_chat_member.model_dump(exclude_none=True)})
    u: User = my_chat_member.from_user
    blocked = my_chat_member.new_chat_member.status in ("left", "kicked")
    await models.User.tg_upsert(u, blocked)


@mr.my_chat_member()
async def user_set_status(my_chat_member: ChatMemberUpdated):
    if my_chat_member.new_chat_member.user.username == "XyncNetBot":  # удалена группа, где бот был добавлен админом
        if forum := await models.Forum.get_or_none(id=my_chat_member.chat.id):
            await forum.delete()
        res = f"I {my_chat_member.new_chat_member.status} from {my_chat_member.chat.id}:{my_chat_member.chat.title}"
        return logging.info(res)
    logging.info({"my_chat_member": my_chat_member.model_dump(exclude_none=True)})
    u: User = my_chat_member.from_user
    blocked = my_chat_member.new_chat_member.status in ("left", "kicked")
    if blocked:
        if forum := await models.Forum.get_or_none(id=my_chat_member.chat.id, user_id=u.id):
            if forum.joined:
                forum.joined = False
                await forum.save()
    return await models.User.tg_upsert(u, blocked)


@mr.chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))  # юзер покинул группу Ордеров
async def on_user_leave(member: ChatMemberUpdated):
    logging.info({"user_leave": member.model_dump(exclude_none=True)})
    if forum := await models.Forum[member.chat.id]:
        if forum.joined:
            forum.joined = False
            await forum.save()
            resp = "Bye!"
    return await member.bot.send_message(member.new_chat_member.user.id, resp)


@mr.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))  # Юзер добавился в группу Ордеров
async def on_user_join(member: ChatMemberUpdated, app_url: str):
    logging.info({"user_join": member.model_dump(exclude_none=True)})
    if forum := await models.Forum.get_or_none(id=member.chat.id):
        if not forum.joined:
            forum.joined = True
            await forum.save()
    else:
        return
    resp = "Welcome to XyncNetwork"
    rm = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Go!", web_app=WebAppInfo(url=app_url))]])
    return await member.bot.send_message(member.new_chat_member.user.id, resp, reply_markup=rm)


@mr.message(F.is_topic_message)
async def order_msg(msg: Message):
    sender = await models.User[msg.from_user.id]
    cid = msg.chat.shifted_id
    assert sender.forum == cid, "sender is not client"
    if order := await models.Order.get_or_none(taker__user_id=sender.id, taker_topic=msg.message_thread_id):
        is_taker = True
    elif order := await models.Order.get_or_none(ad__agent__user_id=sender.id, maker_topic=msg.message_thread_id):
        is_taker = False
    else:
        return await msg.answer("No such order")
        # raise Exception("No such order")
    receiver: models.User = await (order.ad.maker.user if is_taker else order.taker.user)
    rcv_topic = order.taker_topic if is_taker else order.maker_topic
    await models.Msg.create(tgid=msg.message_id, txt=msg.text, order_id=order.id, receiver=receiver)
    logging.info(msg, {"src": "order_msg"})
    return await msg.send_copy(receiver.forum, message_thread_id=rcv_topic)
