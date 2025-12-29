from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from xync_schema import models
from xync_schema.enums import SynonymType

from xync_bot.routers.cond.func import wrap_cond, get_val, btns, rkm, ikm, SynTypeCd, CondCd

cr = Router(name="cond")


@cr.message(Command("cond"))
async def start(msg: Message, state: FSMContext):
    await msg.reply('Заполняем синонимы признаков условий объявлений: "ссылка на инструкцию"', reply_markup=rkm)
    await show_new_cond(msg, state)


async def show_new_cond(msg: Message, state: FSMContext):
    cond = await models.Cond.filter(parsed__isnull=True).order_by("-created_at").first().prefetch_related("parsed")
    await state.set_data({"cond": cond})
    await show_cond(msg, cond)


async def show_cond(msg: Message, cond: models.Cond):
    await msg.answer(await wrap_cond(cond), reply_markup=ikm)


@cr.message(F.quote)
async def got_synonym(msg: Message, state: FSMContext):
    if not (msg.text in {st.name for st in SynonymType} and SynonymType[msg.text]):
        return await msg.reply_text(
            f'Нет раздела "{msg.text}", не пиши текст сам, выдели кусок из моего сообщения,'
            f"ответь на него, выбери кнопку раздела"
        )
    if not msg.quote:
        return await msg.reply_text(f"Вы забыли выделить кусок текста для {msg.text}")
    if typ := SynonymType[msg.text]:
        await state.update_data({"syntext": msg.quote.text, "cmsg": msg.reply_to_message})
        await models.Synonym.update_or_create({"typ": typ}, txt=msg.quote.text)
        if rm := await btns(typ, msg.quote.text):
            return await msg.answer("Уточните", reply_markup=rm, reply_to_message_id=msg.message_id)
        await syn_result(msg, SynTypeCd(typ=typ.name, val=1), state)
    return None


@cr.callback_query(SynTypeCd.filter())
async def got_synonym_val(cbq: CallbackQuery, callback_data: SynTypeCd, state: FSMContext):
    await syn_result(cbq.message, callback_data, state)


async def syn_result(msg: Message, cbd: SynTypeCd, state: FSMContext):
    cond: models.Cond = await state.get_value("cond")
    typ = SynonymType[cbd.typ]
    val, hval = await get_val(typ, cbd.val)
    syntext = await state.get_value("syntext")
    syn, _ = await models.Synonym.update_or_create({"val": val}, typ=typ, txt=syntext)
    await models.CondParsed.update_or_create({typ.name: val}, cond_id=cond.id)
    await msg.answer(
        f'Текст "{syntext}" определен как синоним для `{typ.name}` со значением {hval}',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Готово! Давай новый", callback_data="cond:complete"),
                    InlineKeyboardButton(text="Продолжить с этим текстом", callback_data="cond:continue"),
                ]
            ]
        ),
    )


@cr.callback_query(CondCd.filter())
async def got_action(cbq: CallbackQuery, callback_data: CondCd, state: FSMContext):
    cond: models.Cond = await state.get_value("cond")
    if callback_data.act == "complete":
        await models.CondParsed.update_or_create({"parsed": True}, cond=cond)
        await show_new_cond(cbq.message, state)
    elif callback_data.act == "pass":
        await show_new_cond(cbq.message, state)
    elif callback_data.act == "refresh":
        try:
            await cbq.message.edit_text(await wrap_cond(cond), reply_markup=ikm)
        except TelegramBadRequest as e:
            if "message is not modified:" in e.message:
                return await cbq.answer("Текст не изменился")
            raise e
    elif callback_data.act == "continue":
        await (await state.get_value("cmsg")).delete()
        await show_cond(cbq.message, cond)
    return await cbq.answer(callback_data.act)
