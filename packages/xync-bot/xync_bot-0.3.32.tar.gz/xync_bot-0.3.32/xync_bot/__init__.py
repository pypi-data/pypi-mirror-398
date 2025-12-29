import random
from datetime import timedelta
from itertools import groupby

from PGram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import UpdateType
from aiogram.types import InlineKeyboardButton
from tortoise.timezone import now
from xync_schema.enums import HotStatus

from xync_bot.shared import BoolCd
from xync_schema.models import Order, MyAd, User, Hot, CurEx

from xync_bot.store import Store
from xync_bot.routers import last
from xync_bot.routers.main.handler import mr
from xync_bot.routers.pay.handler import pr
from xync_bot.routers.cond import cr
from xync_bot.routers.send import sd
from xync_bot.routers.hot import hot


au = [
    UpdateType.MESSAGE,
    UpdateType.CALLBACK_QUERY,
    UpdateType.CHAT_MEMBER,
    UpdateType.MY_CHAT_MEMBER,
]  # , UpdateType.CHAT_JOIN_REQUEST


class XyncBot(Bot):
    def __init__(self, token, cn):
        super().__init__(token, cn, [hot, sd, cr, pr, mr, last], Store(), DefaultBotProperties(parse_mode="HTML"))

    async def start(self, wh_host: str = None):
        self.dp.workflow_data["xbt"] = self  # todo: refact?
        # self.dp.workflow_data["store"].glob = await Store.Global()  # todo: refact store loading
        await super().start(au, wh_host)
        return self

    # итерация: предоставляем юзеру кнопки для перехода на hot объявления
    async def go_hot(self, username_id: int, ex_ids: list[int]):
        ex_ids = ex_ids or [4]
        adq = MyAd.hot_mads_query(ex_ids)
        if not (ads := await adq.filter(ad__pair_side__is_sell=False)):
            raise ValueError({1: ex_ids})
        user = await User.get(username_id=username_id)
        hot_db, _ = await Hot.get_or_create(
            {}, user=user, updated_at__gt=now() - timedelta(hours=1), status=HotStatus.opened
        )
        ads = {cur: random.choice(list(g)) for cur, g in groupby(ads, key=lambda x: x.ad.pair_side.pair.cur_id)}
        await hot_db.ads_shared.add(*ads.values())
        btns = [
            [
                InlineKeyboardButton(text=ad.ad.pair_side.pair.cur.ticker + " 🌐", url=ad.get_url()[0]),
                InlineKeyboardButton(text=ad.ad.pair_side.pair.cur.ticker + " 📱", url=ad.get_url()[1]),
            ]
            for ad in ads.values()
        ]
        await self.send(username_id, "🟥Sell USDT", btns)

        if balances := await user.balances():
            curexs = await CurEx.filter(cur_id__in=balances.keys(), ex_id__in=ex_ids)
            minimums = {cx.cur_id: cx.minimum for cx in curexs}
            balances = {cur_id: b for cur_id, b in balances.items() if b >= minimums[cur_id]}
            if ads := await adq.filter(
                ad__pair_side__is_sell=True, ad__pair_side__pair__cur_id__in=balances.keys()
            ).all():
                ads = {cur: random.choice(list(g)) for cur, g in groupby(ads, key=lambda x: x.ad.pair_side.pair.cur_id)}
                await hot_db.ads_shared.add(*ads.values())
                btns = [
                    [
                        InlineKeyboardButton(text=rng + ad.ad.pair_side.pair.cur.ticker + " 🌐", url=ad.get_url()[0]),
                        InlineKeyboardButton(text=rng + ad.ad.pair_side.pair.cur.ticker + " 📱", url=ad.get_url()[1]),
                    ]
                    for cur_id, ad in ads.items()
                    if (rng := f"≤ {balances[cur_id]} ")
                ]
                await self.send(username_id, "🟩Buy USDT", btns)

    async def def_actor(self, uid: int, order: Order):
        """
        Если актор прилетевшего ордера по прогреву еще не связан ни с одним юзером, спрашиваем hot-юзера он ли это
        """
        txt = f"{order.taker.name}:{order.taker.exid} is you?"
        btns = [
            [
                InlineKeyboardButton(text="Yes", callback_data=BoolCd(req="is_you", res=True, xtr=order.id).pack()),
                InlineKeyboardButton(text="No", callback_data=BoolCd(req="is_you", res=False, xtr=order.id).pack()),
            ]
        ]
        await self.send(uid, txt, btns)
