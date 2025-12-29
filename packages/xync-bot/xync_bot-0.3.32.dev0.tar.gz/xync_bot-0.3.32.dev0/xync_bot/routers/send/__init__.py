from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from xync_schema import models
from aiogram.filters.callback_data import CallbackData
from aiogram import types

sd = Router()


class SendStates(StatesGroup):
    waiting_for_recipient = State()
    waiting_for_amount = State()


class Cur(CallbackData, prefix="Сur"):
    id: int


@sd.message(Command("send"))
async def start(message: Message, state: FSMContext):
    await message.answer(
        "Введите ID/username получателя:",
    )

    await state.set_state(SendStates.waiting_for_recipient)


@sd.message(SendStates.waiting_for_recipient)
async def process_recipient(message: Message, state: FSMContext):
    recipient = message.text

    if recipient.isdigit():
        user_id = int(recipient)
        user_receiver = await models.User.get_or_none(username_id=user_id)

        if not user_receiver:
            my_id = message.from_user.id
            await message.answer(
                f"Такого пользователя еще нет в XyncPay, вот ссылка для регистрации с вашим реферальным бонусом: \n"
                f"https://t.me/XyncPayBot?start={my_id}"
            )
            return
        else:
            await state.update_data(receiver=user_receiver)
    else:
        user_receiver = await models.User.get_or_none(username__username=recipient)

        if not user_receiver:
            my_id = message.from_user.id
            await message.answer(
                f"Такого пользователя еще нет в XyncPay, вот ссылка для регистрации с вашим реферальным бонусом: \n"
                f"https://t.me/XyncPayBot?start={my_id}"
            )
            return
        await state.update_data(receiver=user_receiver)

    # Продолжаем процесс выбора валюты
    builder = InlineKeyboardBuilder()
    curs = await models.Cur.filter(
        ticker__in=[
            "CNY",
            "HKD",
            "USD",
            "VND",
            "MYR",
            "TWD",
            "RUB",
            "AUD",
            "CAD",
            "SGD",
            "GBP",
            "EUR",
            "PHP",
            "INR",
            "CHF",
            "IDR",
            "BRL",
            "SAR",
            "AED",
            "TRY",
            "THB",
        ]
    )

    for cur in curs:
        builder.button(text=cur.ticker, callback_data=Cur(id=cur.id).pack())

    builder.adjust(3, 3, 3)
    await message.answer("Выбери валюту", reply_markup=builder.as_markup())


@sd.callback_query(Cur.filter())
async def waiting_for_amount(query: types.CallbackQuery, state: FSMContext, callback_data: Cur):
    await state.update_data(cur=callback_data.id)
    await query.message.answer("Введите сумму: ")
    await state.set_state(SendStates.waiting_for_amount)


@sd.message(SendStates.waiting_for_amount)
async def waiting_for_recipient(message: Message, state: FSMContext):
    amount = int(message.text)
    if amount < 0:
        await message.answer("Введите положительное число")
    else:
        await state.update_data(amount=amount)
        my_id = message.from_user.id
        await state.update_data(sender=my_id)
        data = await state.get_data()
        await state.clear()
        me = await models.User.get(username_id=my_id)
        await models.Transfer.create(
            amount=data["amount"], cur_id=data["cur"], receiver_id=data["receiver"].id, sender=me
        )
