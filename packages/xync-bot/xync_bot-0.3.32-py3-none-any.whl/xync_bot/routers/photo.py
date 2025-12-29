from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import User as TgUser, Message
from x_auth.enums import Role
from xync_schema.models import User, Ex

photo = Router()
exns = State("ex_name")


@photo.message(F.photo | F.sticker)
async def photo_upload(msg: Message, state: FSMContext):
    u: TgUser = msg.from_user
    if not await User.get_or_none(id=u.id, blocked=False, role=Role.ADMIN):
        return await msg.answer("No user")
    if f := msg.sticker:
        await state.set_data({"fid": f.file_id})
        await state.set_state(exns)
        return await msg.answer("Ex name pls")
    res = await set_ex_name(msg.caption, msg.photo[-1].file_id)
    return await msg.answer(res or "No ex", parse_mode="HTML")


async def set_ex_name(name: str, fid: str) -> str | None:
    if ex := await Ex.get_or_none(name=name):
        ex.logo = fid
        await ex.save()
        return fid
    return None


@photo.message(exns)
async def ex_name(msg: Message, state: FSMContext):
    res = await set_ex_name(msg.text, await state.get_value("fid"))
    return await msg.answer(res or "No ex" + msg.text, parse_mode="HTML")
