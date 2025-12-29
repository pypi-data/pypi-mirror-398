import logging
from aiogram.types import Message
from tortoise.functions import Min
from x_model.func import ArrayAgg
from x_auth.enums import Role
from xync_schema.models import Addr, Asset, Cred, Coin, PmCur, Cur, User, Ex, PmEx

from xync_bot.shared import flags


class SingleStore(type):
    _store = None

    async def __call__(cls):
        if not cls._store:
            cls._store = super(SingleStore, cls).__call__()
            cls._store.coins = {k: v for k, v in await Coin.all().order_by("ticker").values_list("id", "ticker")}
            curs = {c.id: c for c in await Cur.filter(ticker__in=flags.keys()).order_by("ticker")}
            cls._store.curs = curs
            cls._store.exs = {k: v for k, v in await Ex.all().values_list("id", "name")}
            cls._store.pmcurs = {
                k: v
                for k, v in await PmEx.filter(pm__pmcurs__cur_id__in=cls._store.curs.keys())
                .annotate(sname=Min("name"))
                .group_by("pm__pmcurs__id")
                .values_list("pm__pmcurs__id", "sname")
            }
            cls._store.coinexs = {
                c.id: [ex.ex_id for ex in c.coinexs] for c in await Coin.all().prefetch_related("coinexs")
            }
            cls._store.curpms = {
                cur_id: ids
                for cur_id, ids in await PmCur.filter(cur_id__in=curs.keys())
                .annotate(ids=ArrayAgg("id"))
                .group_by("cur_id")
                .values_list("cur_id", "ids")
            }
            cls._store.curpms = {
                cur_id: ids
                for cur_id, ids in await PmCur.filter(cur_id__in=curs.keys())
                .annotate(ids=ArrayAgg("id"))
                .group_by("cur_id")
                .values_list("cur_id", "ids")
            }

        return cls._store


class Store:
    class Global(metaclass=SingleStore):
        coins: dict[int, str]  # id:ticker
        curs: dict[int, Cur]  # id:Cur
        exs: dict[int, str]  # id:name
        coinexs: dict[int, list[int]]  # id:[ex_ids]
        pmcurs: dict[int, str]  # pmcur_id:name
        curpms: dict[int, list[int]]  # id:[pmcur_ids]

    class Personal:
        class Current:
            is_target: bool = True
            is_fiat: bool = None
            msg_to_del: Message = None

        msg_id: int = None
        actors: dict[int, int] = None  # key=ex_id
        creds: dict[int, Cred] = None  # key=cred_id
        cur_creds: dict[int, list[int]] = None  # pmcur_id:[cred_ids]

        def __init__(self, user: User):
            self.user: User = user
            self.curr = self.Current()

    class Pr:
        t_cur_id: int = None
        s_cur_id: int = None
        t_coin_id: int = None
        s_coin_id: int = None
        t_pmcur_id: int = None
        s_pmcur_id: int = None
        t_ex_id: int = None
        s_ex_id: int = None
        amount: int | float = None
        ppo: int = 1
        addr_id: int = None
        cred_dtl: str = None
        cred_id: int = None
        urg: int = 5
        pr_id: int = None

        def __init__(self, uid: int):
            self.uid = uid

        async def xync_have_coin_amount(self) -> bool:
            assets = await Asset.filter(
                addr__coin_id=self.t_coin_id, addr__ex_id=self.t_ex_id, addr__actor__user__role__in=Role.ADMIN
            )
            return self.amount <= sum(a.free for a in assets)

        async def client_have_coin_amount(self) -> bool:
            assets = await Asset.filter(addr__coin_id=self.t_coin_id, addr__actor_id__in=self.perm.actors.values())
            return self.amount <= sum(a.free for a in assets)

        async def need_ppo(self):
            cur_id = getattr(self, ("t" if self.curr.is_target else "s") + "_cur_id")
            usd_amount = self.amount * self.glob.curs[cur_id].rate
            if usd_amount < 50:
                return 0
            elif usd_amount > 100:
                return 2
            else:
                return 1

        async def client_target_repr(self) -> tuple[Addr | Cred, str]:
            if self.t_ex_id:
                addr_to = (
                    await Addr.filter(actor__ex_id=self.t_ex_id, coin_id=self.t_coin_id, actor__user=self.perm.user)
                    .prefetch_related("actor")
                    .first()
                )
                ex, coin = self.glob.exs[self.s_ex_id], self.glob.coins[self.s_coin_id]
                if not addr_to:
                    logging.error(f"No {coin} addr in {ex} for user: {self.perm.user.username_id}")
                return addr_to, f"{coin} на {ex} по id: `{addr_to.actor.exid}`"
            # иначе: реквизиты для фиата
            cur, pm = self.glob.curs[self.t_cur_id], self.glob.pmcurs[self.t_pmcur_id]
            cred = self.perm.creds[self.cred_id]
            return cred, f"{cur.ticker} на {pm} по номеру: {cred.repr()}"

        async def get_merch_target(self) -> tuple[Addr | Cred, str]:
            if self.s_ex_id:
                addr_in = (
                    await Addr.filter(
                        actor__ex_id=self.s_ex_id, coin_id=self.s_coin_id, actor__user__role__gte=Role.ADMIN
                    )
                    .prefetch_related("actor")
                    .first()
                )
                ex, coin = self.glob.exs[self.s_ex_id], self.glob.coins[self.s_coin_id]
                if not addr_in:
                    logging.error(f"No {coin} addr in {ex}")
                return addr_in, f"{coin} на {ex} по id: `{addr_in.actor.exid}`"
            # иначе: реквизиты для фиатной оплаты
            s_pmcur = await PmCur.get(id=self.s_pmcur_id).prefetch_related("pm__grp")
            cred = await Cred.filter(
                **({"pmcur__pm__grp": s_pmcur.pm.grp} if s_pmcur.pm.grp else {"pmcur_id": self.s_pmcur_id}),
                person__user__role__gte=Role.ADMIN,
            ).first()  # todo: payreq by fiat.target-fiat.amount
            cur, pm = self.glob.curs[self.s_cur_id], self.glob.pmcurs[self.s_pmcur_id]
            if not cred:
                logging.error(f"No {cur.ticker} cred for {pm}")
            return cred, f"{cur.ticker} на {pm} по номеру: {cred.repr()}"
