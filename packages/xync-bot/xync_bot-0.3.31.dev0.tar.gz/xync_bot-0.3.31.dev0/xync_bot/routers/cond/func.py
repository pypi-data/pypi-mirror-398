import re
from enum import IntEnum
from inspect import isclass
from typing import Coroutine

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from cyrtranslit import to_latin
from xync_schema import models
from xync_schema.enums import SynonymType, Boundary, Party, Slip, AbuserType, NameType


class SynTypeCd(CallbackData, prefix="st"):
    typ: str
    val: int


class CondCd(CallbackData, prefix="cond"):
    act: str


async def wrap_cond(cond: models.Cond):
    bnks = await models.Synonym.filter(typ=SynonymType.bank)
    bnks = "|".join("\\b" + b.txt + ("\\b" if b.boundary & Boundary.right else "") for b in bnks)
    ad = await models.Ad.filter(cond=cond).order_by("-updated_at").prefetch_related("ex", "pair_side").first()
    hdr = ("SELL" if ad.pair_side.is_sell else "BUY") + f":{ad.price} [{ad.min_fiat}]"
    if (mx := (ad.max_fiat or ad.amount)) > ad.min_fiat:
        hdr += f"->[{mx}]"
    txt = cond.raw_txt
    for syn in await models.Synonym.all():
        lb, rb = "\\b" if syn.boundary & Boundary.left else "", "\\b" if syn.boundary & Boundary.right else ""
        if syn.typ == SynonymType.bank_side:
            syn.txt.replace("#banks#", f"({bnks})")
        if syn.is_re or syn.txt in txt:
            pattern = re.compile(lb + syn.txt + rb)
            if match := re.search(pattern, txt):
                g = match.group()
                val, hval = await get_val(syn.typ, syn.val)
                val = syn.typ.name + (f'="{hval}"' if hval else "")
                txt = re.sub(pattern, f"<code>{g}</code><tg-spoiler>[{val}]</tg-spoiler>", txt)
    return f"<blockquote>{hdr} {ad.ex.name}</blockquote>{txt}"


async def cbanks(bnid: str) -> list[tuple[int, str]]:
    beginning = to_latin(bnid[:2], lang_code="ru")
    return await models.Pm.filter(norm__startswith=beginning, bank=True).values_list("id", "norm")


async def cppo(txt: str) -> list[tuple[int, str]]:
    opts = re.findall(r"\d+", txt) or [1, 1000, 5000]
    return [(o, str(o)) for o in opts]


async def contact(txt: str) -> list[tuple[int, str]]: ...


synopts: dict[SynonymType, list[str] | type(IntEnum) | None | Coroutine] = {
    SynonymType.name: ["not_slavic", "slavic"],
    SynonymType.ppo: cppo,
    SynonymType.from_party: Party,
    SynonymType.to_party: Party,
    SynonymType.slip_req: Slip,
    SynonymType.slip_send: Slip,
    SynonymType.abuser: AbuserType,
    SynonymType.scale: ["1", "100", "1000", "5000"],
    SynonymType.slavic: NameType,
    SynonymType.mtl_like: None,
    SynonymType.bank: cbanks,
    SynonymType.bank_side: ["except", "only"],
    SynonymType.sbp_strict: ["no", "sbp", "card"],
    SynonymType.contact: contact,
}

rkm = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ppo"), KeyboardButton(text="abuser")],
        [KeyboardButton(text="from_party"), KeyboardButton(text="to_party")],
        [KeyboardButton(text="slip_send"), KeyboardButton(text="slip_req")],
        [KeyboardButton(text="name"), KeyboardButton(text="slavic")],
        [KeyboardButton(text="scale"), KeyboardButton(text="mtl_like")],
        [KeyboardButton(text="bank"), KeyboardButton(text="bank_side")],
        [KeyboardButton(text="sbp_strict"), KeyboardButton(text="contact")],
    ],
    # one_time_keyboard=True,
)
ikm = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Обновить", callback_data="cond:refresh"),
            InlineKeyboardButton(text="Пропустить", callback_data="cond:pass"),
        ]
    ]
)


async def get_val(typ: SynonymType.__class__, val: str | int) -> tuple[SynonymType | int | bool, str]:
    if isinstance(val, str) and val.isnumeric():
        val = int(val)
    if isclass(lst := synopts[typ]) and issubclass(lst, IntEnum):
        return (v := lst(val)), v.name
    elif isinstance(lst, list):
        return val, lst[val]
    elif typ == SynonymType.bank:
        return val, (await models.Pm[val]).norm
    return val, val


async def btns(typ: SynonymType.__class__, txt: str = None) -> InlineKeyboardMarkup | None:
    if lst := synopts[typ]:
        if isinstance(lst, list):
            kb = [[InlineKeyboardButton(text=n, callback_data=f"st:{typ.name}:{i}")] for i, n in enumerate(lst)]
        elif isclass(lst) and issubclass(lst, IntEnum):
            kb = [[InlineKeyboardButton(text=i.name, callback_data=f"st:{typ.name}:{i.value}")] for i in lst]
        else:
            kb = [[InlineKeyboardButton(text=n, callback_data=f"st:{typ.name}:{i}")] for i, n in await lst(txt)]
        return InlineKeyboardMarkup(inline_keyboard=kb)
    else:
        return lst
