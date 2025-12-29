from aiogram.filters.callback_data import CallbackData

from xync_bot.routers.pay.dep import PayStep, ActionType


class MoneyType(CallbackData, prefix="target"):
    is_fiat: int  # bool
    is_target: int  # bool


class Cur(CallbackData, prefix="cur"):
    id: int
    is_target: int  # bool


class Coin(CallbackData, prefix="coin"):
    id: int
    is_target: int  # bool


class Cred(CallbackData, prefix="cred"):
    id: int


class Ex(CallbackData, prefix="ex"):
    id: int
    is_target: int  # bool


class Pm(CallbackData, prefix="pm"):
    pmcur_id: int
    is_target: bool


class Ppo(CallbackData, prefix="ppo"):
    num: int
    is_target: int  # bool


class PayNav(CallbackData, prefix="pay_nav"):
    to: PayStep


class Time(CallbackData, prefix="time"):
    minutes: int  # время в минутах


class Action(CallbackData, prefix="action"):
    act: ActionType  # "received" или "not_received"
