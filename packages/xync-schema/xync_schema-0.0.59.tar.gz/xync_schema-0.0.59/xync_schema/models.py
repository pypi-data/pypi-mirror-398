import re
import struct
import sys
from uuid import UUID
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from asyncpg.pgproto.pgproto import utc
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from tortoise.fields import (
    SmallIntField,
    BigIntField,
    CharField,
    BooleanField,
    IntEnumField,
    FloatField,
    JSONField,
    ForeignKeyField,
    OneToOneField,
    ManyToManyField,
    ForeignKeyRelation,
    OneToOneRelation,
    ForeignKeyNullableRelation,
    OneToOneNullableRelation,
    ManyToManyRelation,
    UUIDField,
    CASCADE,
    BinaryField,
)
from tortoise.fields.relational import BackwardFKRelation, BackwardOneToOneRelation
from tortoise.functions import Sum
from tortoise.queryset import QuerySet
from tortoise import Model as BaseModel
from tortoise.signals import pre_save
from tortoise.timezone import now

# noinspection PyUnresolvedReferences
from x_auth.models import (
    Model,
    Username as Username,
    User as TgUser,
    Proxy as Proxy,
    Dc as Dc,
    Fcm as Fcm,
    App as App,
    Session as Session,
    Peer as Peer,
    UpdateState as UpdateState,
    Version as Version,
    Country as BaseCountry,
    UniqBinaryField,
)
from x_model.field import UInt1Field, UInt2Field, UInt4Field, UInt8Field
from x_model.models import TsTrait, DatetimeSecField

from xync_schema.enums import (
    ExType,
    AdStatus,
    OrderStatus,
    ExAction,
    ExStatus,
    PersonStatus,
    UserStatus,
    PmType,
    FileType,
    AddrExType,
    DepType,
    Party,
    Slip,
    SynonymType,
    AbuserType,
    Boundary,
    SbpStrict,
    TransactionStatus as TS,
    HotStatus,
    TaskType,
    TransactionStatus,
)


class Country(BaseCountry):
    cur: ForeignKeyRelation["Cur"] = ForeignKeyField("models.Cur", "countries", on_update=CASCADE)
    curexs: ManyToManyRelation["CurEx"]
    forbidden_exs: ManyToManyRelation["Ex"]
    fiats: BackwardFKRelation["Fiat"]


class Cur(Model):
    id = UInt1Field(True)
    ticker: str = CharField(3, unique=True)
    scale: int = UInt1Field(default=2)
    rate: float | None = FloatField(null=True)

    pms: ManyToManyRelation["Pm"] = ManyToManyField("models.Pm", "pmcur", on_update=CASCADE)
    exs: ManyToManyRelation["Ex"] = ManyToManyField("models.Ex", "curex", on_update=CASCADE)
    pairs: BackwardFKRelation["Pair"]
    countries: BackwardFKRelation[Country]
    synonyms: ManyToManyRelation["Synonym"]

    _name = {"ticker"}

    class Meta:
        table_description = "Fiat currencies"


class Coin(Model):
    id: int = SmallIntField(True)
    ticker: str = CharField(15, unique=True)
    rate: float | None = FloatField(default=0)
    is_fiat: bool = BooleanField(default=False)
    scale: int = UInt1Field()
    exs: ManyToManyRelation["Ex"] = ManyToManyField("models.Ex", "coinex", on_update=CASCADE)

    assets: BackwardFKRelation["Asset"]
    nets: BackwardFKRelation["Net"]
    pairs: BackwardFKRelation["Pair"]
    # deps: BackwardFKRelation["Dep"]
    # deps_reward: BackwardFKRelation["Dep"]
    # deps_bonus: ReverseRelation["Dep"]

    _name = {"ticker"}


class Net(Model):
    id: int = UInt1Field(True)
    name: str = CharField(63)
    native_coin: ForeignKeyRelation[Coin] = ForeignKeyField("models.Coin", "nets", on_update=CASCADE)
    native_coin_id: int


class Ex(Model):
    id: int = UInt1Field(True)
    name: str = CharField(31)
    host: str | None = CharField(63, null=True, description="With no protocol 'https://'")
    host_p2p: str | None = CharField(63, null=True, description="With no protocol 'https://'")
    url_login: str | None = CharField(63, null=True, description="With no protocol 'https://'")
    typ: ExType = IntEnumField(ExType)
    status: ExStatus = IntEnumField(ExStatus, default=ExStatus.plan)
    logo: str = CharField(511, default="")

    ads: ManyToManyRelation["Ad"]
    pms: ManyToManyRelation["Pm"]
    curs: ManyToManyRelation[Cur]
    # pmcurs: ManyToManyRelation["PmCur"] = ManyToManyField("models.PmCur", through="pmcurex")
    coins: ManyToManyRelation[Coin]
    forbidden_countries: ManyToManyRelation[Country] = ManyToManyField(
        "models.Country", related_name="forbidden_exs", on_update=CASCADE
    )

    actors: BackwardFKRelation["Actor"]
    pmexs: BackwardFKRelation["PmEx"]
    pm_reps: BackwardFKRelation["PmRep"]
    pairexs: BackwardFKRelation["PairEx"]
    deps: BackwardFKRelation["Dep"]
    stats: BackwardFKRelation["ExStat"]

    class Meta:
        table_description = "Exchanges"
        unique_together = (("name", "typ"),)

    class PydanticMeta(Model.PydanticMeta):
        include = "name", "logo"

    def client(self, bot, **kwargs):
        module_name = f"xync_client.{self.name}.ex"
        __import__(module_name)
        client = sys.modules[module_name].ExClient
        return client(self, bot, **kwargs)

    def etype(self):
        module_name = f"xync_client.{self.name}.etype"
        __import__(module_name)
        return sys.modules[module_name]


class CurEx(BaseModel):
    cur: ForeignKeyRelation[Cur] = ForeignKeyField("models.Cur", on_update=CASCADE)
    cur_id: int
    ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex", on_update=CASCADE)
    ex_id: int
    exid: str = CharField(32)
    minimum: int = UInt4Field(null=True)  # /10^cur.scale
    scale: int = UInt1Field(null=True)

    # countries: ManyToManyRelation[Country] = ManyToManyField (
    #     "models.Country", through="curex_country", backward_key="curexs"
    # )

    class Meta:
        table_description = "Currency in Exchange"
        unique_together = (("ex_id", "cur_id"), ("ex_id", "exid"))


class CoinEx(BaseModel):
    coin: ForeignKeyRelation[Coin] = ForeignKeyField("models.Coin", on_update=CASCADE)
    coin_id: int
    ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex", on_update=CASCADE)
    ex_id: int
    minimum: int = BigIntField(null=True)  # /10^self.scale
    scale: int = UInt1Field()

    exid: str = CharField(32)
    p2p: bool = BooleanField(default=True)

    class Meta:
        table_description = "Currency in Exchange"
        unique_together = (("ex_id", "coin_id"), ("ex_id", "exid"))


class Pair(Model):
    id = SmallIntField(True)
    coin: ForeignKeyRelation[Coin] = ForeignKeyField("models.Coin", "pairs", on_update=CASCADE)
    cur: ForeignKeyRelation[Cur] = ForeignKeyField("models.Cur", "pairs", on_update=CASCADE)

    _name = {"coin__ticker", "cur__ticker"}

    class Meta:
        table_description = "Coin/Currency pairs"
        unique_together = (("coin_id", "cur_id"),)


class PairSide(Model):  # Way
    id = SmallIntField(True)
    pair: ForeignKeyRelation[Pair] = ForeignKeyField("models.Pair", "pair_sides", on_update=CASCADE)
    pair_id: int
    is_sell: bool = BooleanField()

    class Meta:
        table = "pair_side"
        unique_together = (("pair_id", "is_sell"),)


class NetAddr(Model):  # Way
    net: ForeignKeyRelation[Net] = ForeignKeyField("models.Net", "net_addrs", on_update=CASCADE)
    net_id: int
    addr: ForeignKeyRelation["Addr"] = ForeignKeyField("models.Addr", "net_addrs", on_update=CASCADE)
    addr_id: int
    val: str = CharField(200)
    memo: str | None = CharField(54, null=True)
    qr: str | None = CharField(255, null=True)

    class Meta:
        table = "net_addr"
        unique_together = (("net_id", "addr_id"),)


class PairEx(Model, TsTrait):  # todo: refact to PairSideEx?
    # todo: различаются ли комиссии на buy/sell по одной паре хоть на одной бирже? если да, то переделать
    pair: ForeignKeyRelation[Pair] = ForeignKeyField("models.Pair", "pairexs", on_update=CASCADE)
    pair_id: int
    fee: int = SmallIntField(default=0)  # /10_000
    ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex", "pairs", on_update=CASCADE)
    ex_id: int
    pair_sides: BackwardFKRelation["PairSide"]

    _name = {"pair__coin__ticker", "pair__cur__ticker", "ex__name"}

    class Meta:
        table_description = "Pairs on Exs"
        unique_together = (("pair_id", "ex_id"),)


class Person(Model, TsTrait):
    status: PersonStatus = IntEnumField(PersonStatus, default=PersonStatus.DEFAULT)
    name: str | None = CharField(127, null=True)
    note: bool = CharField(255, null=True)

    tg: OneToOneNullableRelation[Username] = OneToOneField("models.Username", "person", on_update=CASCADE, null=True)
    tg_id: int

    user: BackwardOneToOneRelation["User"]
    creds: BackwardFKRelation["Cred"]
    actors: BackwardFKRelation["Actor"]
    pm_agents: BackwardFKRelation["PmAgent"]

    class Meta:
        unique_together = (("name", "note", "tg_id"),)


class User(TgUser, TsTrait):
    status: UserStatus = IntEnumField(UserStatus, null=True)
    person: OneToOneRelation[Person] = OneToOneField("models.Person", "user", on_update=CASCADE)
    person_id: int
    ref: ForeignKeyNullableRelation["User"] = ForeignKeyField("models.User", "proteges", on_update=CASCADE, null=True)
    ref_id: int | None
    tz: int = SmallIntField(default=3)

    actors: BackwardFKRelation["Actor"]
    contacts: BackwardFKRelation["User"]
    created_forums: BackwardFKRelation["Forum"]
    creds: BackwardFKRelation["Cred"]
    pm_agents: BackwardFKRelation["PmAgent"]
    gmail: BackwardOneToOneRelation["Gmail"]
    forum: BackwardOneToOneRelation["Forum"]
    limits: BackwardFKRelation["Limit"]
    msgs: BackwardFKRelation["Msg"]
    proteges: BackwardFKRelation["User"]
    sends: BackwardFKRelation["Transaction"]
    receives: BackwardFKRelation["Transaction"]
    validates: BackwardFKRelation["Transaction"]
    vpn: BackwardOneToOneRelation["Vpn"]
    invite_requests: BackwardFKRelation["Invite"]
    invite_approvals: BackwardFKRelation["Invite"]
    lends: BackwardFKRelation["Credit"]
    borrows: BackwardFKRelation["Credit"]
    investments: BackwardFKRelation["Investment"]

    # def __init__(self, **kwargs: Any) -> None:
    #     super().__init__(**kwargs)
    #     self.pm_clients = {pma.pm_id: pma.client() for pma in self.pm_agents}
    #     self.agent_clients = {a.id: a.client() for a in self.person.actor.agents}

    async def free_assets(self):
        assets = await Asset.filter(agent__actor__person__user__id=self.id).values("free", "addr__coin__rate")
        return sum(asset["free"] * asset["addr__coin__rate"] for asset in assets)

    async def fiats_sum(self):
        fiats = await Fiat.filter(cred__person__user__id=self.id).values("amount", "cred__pmcur__cur__rate")
        return sum(fiat["amount"] * Decimal(fiat["cred__pmcur__cur__rate"]) for fiat in fiats)

    async def balance_sum(self) -> int:
        return int(await self.free_assets()) + int(await self.fiats_sum())

    async def balances(self, ctd: bool = True) -> dict[int, int | float]:  # ctd - convert to decimal
        dbt = {1: 0, 2: 0, 3: 0} | {
            c: v * 10 ** (-s) if ctd else v
            for c, v, s in await Transaction.filter(receiver=self, status__gte=TS.signed)
            .prefetch_related("cur")
            .group_by("cur_id", "cur__scale")
            .annotate(debit=Sum("amount"))
            .values_list("cur_id", "debit", "cur__scale")
        }
        crd = {
            c: v * 10 ** (-s) if ctd else v
            for c, v, s in await Transaction.filter(sender=self, status__gte=TS.signed)
            .prefetch_related("cur")
            .group_by("cur_id", "cur__scale")
            .annotate(credit=Sum("amount"))
            .values_list("cur_id", "credit", "cur__scale")
        }
        top = {
            c: v * 10 ** (-s) if ctd else v
            for c, v, s in await TopUp.filter(user=self, completed_at__isnull=False)
            .prefetch_related("cur")
            .group_by("cur_id", "cur__scale")
            .annotate(topup=Sum("amount"))
            .values_list("cur_id", "topup", "cur__scale")
        }
        return {c: dbt.get(c, 0) - crd.get(c, 0) + top.get(c, 0) for c in dbt.keys() | crd.keys() | top.keys()}

    async def balance(self, cur_id: int) -> int:
        dbt = (
            await Transaction.filter(receiver=self, cur_id=cur_id, status__gte=TS.signed)
            .group_by("cur_id")
            .annotate(debit=Sum("amount"))
            .values_list("debit", flat=True)
        ) or [0]
        crd = (
            await Transaction.filter(sender_id=self.id or None, cur_id=cur_id, status__gte=TS.signed)
            .group_by("cur_id")
            .annotate(credit=Sum("amount"))
            .values_list("credit", flat=True)
        ) or [0]
        top = (
            await TopUp.filter(user=self, cur_id=cur_id, completed_at__isnull=False)
            .group_by("cur_id")
            .annotate(topup=Sum("amount"))
            .values_list("topup", flat=True)
        ) or [0]
        return dbt[0] - crd[0] + top[0]

    # async def keygen(self):  # moved to front
    #     prv = Ed25519PrivateKey.generate()
    #     self.prv = prv.private_bytes_raw()
    #     self.pub = prv.public_key().public_bytes_raw()
    #     # await self.save(update_fields=["prv", "pub"])

    async def get_validator(self, amount: int, cur_id: int, receiver_id: int) -> "User":
        r = {
            c: v
            for c, v in await Transaction.filter(  # todo: rm ` or receiver_id` - is hack for first trans
                receiver_id__not_in={receiver_id, self.id or receiver_id}, status=TS.valid, cur_id=cur_id
            )
            .group_by("receiver_id")
            .annotate(debit=Sum("amount"))
            .values_list("receiver_id", "debit")
        }
        s = {
            c: v
            for c, v in await Transaction.filter(
                sender_id__not_in={self.id, receiver_id}, status=TS.valid, cur_id=cur_id
            )
            .group_by("sender_id")
            .annotate(credit=Sum("amount"))
            .values_list("sender_id", "credit")
            if c is not None  # todo: rm `if c is not None` - is hack
        }
        val_ids = r.keys() | s.keys()
        # noinspection PyUnboundLocalVariable
        vals = {c: am for c in val_ids if c is not None and (am := r.get(c, 0) - s.get(c, 0)) > amount}
        val_id, _ = sorted(vals.items(), key=lambda x: x[1], reverse=True)[0]
        if val_id is None:
            raise ValueError("No available validators:(")
        validator = await User[val_id]
        return validator

    async def req(self, amount: int, cur_id: int, sender_id: int = None, ts: int = None) -> "Transaction":
        ts = {"ts": datetime.now(utc) + timedelta(minutes=ts)} if ts else {}
        return await Transaction.create(
            receiver=self,
            sender_id=sender_id,
            amount=amount,
            cur_id=cur_id,
            status=TS.request,
            **ts,
        )

    async def send(
        self, uid: UUID, ts: int, cur_id: int, receiver_id: int, amount: int, sign: bytes
    ) -> "Transaction":  # | int
        b = await self.balance(cur_id)
        if self.id and b < amount:
            return b
        # validator = await self.get_validator(amount, cur_id, receiver_id)
        transaction = await Transaction.create(
            id=uid,
            sender=self,
            receiver_id=receiver_id,
            amount=amount,
            cur_id=cur_id,
            # validator=validator,
            proof=sign,
            status=TS.signed,
            ts=ts,
        )
        return transaction

    async def send_by_req(self, req: "Transaction") -> "Transaction":
        assert req.status == TS.request, "its not a request"
        assert not req.sender_id or self.id == req.sender_id, "sender id is incorrect"
        b = await self.balance(req.cur_id)
        assert b >= req.amount, "not enough balance"
        sender_prv = Ed25519PrivateKey.from_private_bytes(self.prv)
        req.sender = self
        req.validator = await self.get_validator(req.amount, req.cur_id, req.receiver_id)
        req.ts = datetime.now()
        req.proof = sender_prv.sign(req.pack)
        req.status = TS.signed
        await req.save()
        return req
        # async with in_transaction():
        #     await req.fetch_related("sender", "validator")
        #     req.proof = req.validator.proof_trans(req, sender_sig)
        #     if not req.check():
        #         raise ValueError("Transaction check failed")
        #     req.status = TS.valid
        #     await req.save(update_fields=["proof", "status"])
        # return transaction

    def name(self):
        return f"{self.first_name} {self.last_name}".rstrip()

    class PydanticMeta(Model.PydanticMeta):
        max_recursion = 0
        include = "role", "status"
        # computed = ["balance"]


@pre_save(User)
async def person(_meta, user: User, _db, _updated: dict) -> None:
    if user.person_id is None:
        user.person = await Person.create(name=f"{user.first_name} {user.last_name or ''}".strip())


class Gmail(Model):
    login: str = CharField(127)
    auth: dict = JSONField(default={})
    token: bytes = BinaryField(null=True)
    updated_at: datetime | None = DatetimeSecField(auto_now=True)

    user: OneToOneRelation[User] = OneToOneField("models.User", "gmail", on_update=CASCADE)


class Forum(Model, TsTrait):
    id: int = BigIntField(True)
    joined: bool = BooleanField(default=False)
    user: OneToOneRelation[User] = OneToOneField("models.User", "forum", on_update=CASCADE)
    user_id: int
    # created_by: BackwardFKRelation[User] = ForeignKeyField("models.User", "created_forums")


class Actor(Model):
    exid: int = UInt8Field()
    name: int = CharField(63)
    ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex", "actors", on_update=CASCADE)
    ex_id: int
    person: ForeignKeyRelation[Person] = ForeignKeyField("models.Person", "actors", on_update=CASCADE)
    person_id: int

    agent: BackwardOneToOneRelation["Agent"]
    conds: BackwardFKRelation["Cond"]
    my_ads: BackwardFKRelation["Ad"]
    taken_orders: BackwardFKRelation["Order"]

    def asset_client(self):
        module_name = f"xync_client.{self.ex.name}.asset"
        __import__(module_name)
        client = sys.modules[module_name].AssetClient
        return client(self)

    class Meta:
        table_description = "Actors"
        unique_together = (("ex_id", "exid"), ("ex_id", "person_id"))

    async def get_credexs_by(self, pm_ids: list[int], cur_id: int) -> list["CredEx"]:
        return await CredEx.filter(
            ex_id=self.ex_id,
            cred__pmcur__pm_id__in=pm_ids,
            cred__person_id=self.person_id,
            cred__pmcur__cur_id=cur_id,
        )


class Agent(Model, TsTrait):
    auth: dict = JSONField(default={})
    actor: OneToOneRelation[Actor] = OneToOneField("models.Actor", "agent", on_update=CASCADE)
    actor_id: int
    expire_at: datetime | None = DatetimeSecField(null=True)
    status: int = SmallIntField(default=0)

    assets: BackwardFKRelation["Asset"]

    _name = {"actor__name"}

    # def balance(self) -> int:
    #     return sum(asset.free * (asset.coin.rate or 0) for asset in self.assets)

    # class PydanticMeta(Model.PydanticMeta):
    # max_recursion = 3
    # include = "id", "actor__ex", "auth", "updated_at"
    # computed = ["balance"]

    def client(self, ex_cl, fbot, bbot, pm_clients=None, proxy=None):
        module_name = f"xync_client.{self.actor.ex.name}.agent"
        __import__(module_name)
        client = sys.modules[module_name].AgentClient
        return client(
            self,
            ex_cl,
            fbot,
            bbot,
            pm_clients or {},
            headers=self.auth.get("headers"),
            cookies=self.auth.get("cookies"),
            proxy=proxy,
        )


class Cond(Model, TsTrait):
    raw_txt: str = CharField(4095, unique=True)
    last_ver: str = CharField(4095, null=True)

    ads: BackwardFKRelation["Ad"]
    parsed: BackwardOneToOneRelation["CondParsed"]
    sim: BackwardOneToOneRelation["Cond"]

    async def sims(self):
        return {self.raw_txt: await self.sim.sims()} if await self.sim else self.raw_txt


class Synonym(BaseModel):
    typ: SynonymType = IntEnumField(SynonymType, db_index=True)
    txt: str = CharField(255, unique=True)
    boundary: Boundary = IntEnumField(Boundary, default=Boundary.no)
    curs: ManyToManyRelation[Cur] = ManyToManyField(
        "models.Cur", "synonym_cur", related_name="synonyms", on_update=CASCADE
    )
    val: int | None = UInt2Field(null=True)  # SynonymType dependent (e.g., no-slavic for name, approx for ppo.)
    is_re: bool = BooleanField(default=False)


class CondSim(BaseModel):
    cond: OneToOneRelation[Cond] = OneToOneField("models.Cond", "sim", primary_key=True, on_update=CASCADE)
    cond_id: int  # new
    similarity: int = UInt2Field(db_index=True)  # /1000
    cond_rel: ForeignKeyRelation[Cond] = ForeignKeyField("models.Cond", "sims_rel", on_update=CASCADE)
    cond_rel_id: int  # old

    class Meta:
        table = "cond_sim"


class PmGroup(Model):
    id: int = SmallIntField(True)
    name: str = CharField(127)
    pms: BackwardFKRelation["Pm"]

    class Meta:
        table = "pm_group"


class Pm(Model):
    # name: str = CharField(63)  # mv to pmex cause it diffs on each ex
    norm: str | None = CharField(63)
    acronym: str | None = CharField(7, null=True)
    country: ForeignKeyNullableRelation[Country] = ForeignKeyField(
        "models.Country", "pms", on_update=CASCADE, null=True
    )
    df_cur: ForeignKeyNullableRelation[Cur] = ForeignKeyField("models.Cur", "df_pms", on_update=CASCADE, null=True)
    grp: ForeignKeyNullableRelation[PmGroup] = ForeignKeyField("models.PmGroup", "pms", on_update=CASCADE, null=True)
    alias: str | None = CharField(63, null=True)
    extra: str | None = CharField(63, null=True)
    ok: bool = BooleanField(default=True)
    bank: bool | None = BooleanField(null=True)
    qr: bool = BooleanField(default=False)
    fee: int | None = UInt2Field(null=True)  # /10_000

    typ: PmType | None = IntEnumField(PmType, null=True)

    ads: ManyToManyRelation["Ad"]
    curs: ManyToManyRelation[Cur]
    no_conds: ManyToManyRelation[Cond]
    only_conds: ManyToManyRelation[Cond]
    exs: ManyToManyRelation[Ex] = ManyToManyField("models.Ex", "pmex", on_update=CASCADE)  # no need. use pmexs[.exid]
    conds: BackwardFKRelation["CondParsed"]
    orders: BackwardFKRelation["Order"]
    pmcurs: BackwardFKRelation["PmCur"]  # no need. use curs
    pmexs: BackwardFKRelation["PmEx"]
    agents: BackwardFKRelation["PmAgent"]
    topupable: BackwardFKRelation["TopUpAble"]

    class Meta:
        table_description = "Payment methods"
        unique_together = (("norm", "country_id"), ("alias", "country_id"))

    # class PydanticMeta(Model.PydanticMeta):
    #     max_recursion = 3
    #     backward_relations = True
    #     include = "id", "name", "logo", "pmexs__sbp"

    # def epyd(self):
    #     module_name = f"xync_client.{self.ex.name}.pyd"
    #     __import__(module_name)
    #     return sys.modules[module_name].PmEpyd


class CondParsed(Model, TsTrait):
    cond: OneToOneNullableRelation[Cond] = OneToOneField("models.Cond", "parsed", on_update=CASCADE, null=True)
    cond_id: int  # new
    to_party: Party = IntEnumField(Party, null=True)
    from_party: Party = IntEnumField(Party, null=True)
    ppo: int = UInt1Field(null=True)  # Payments per order
    slip_req: Slip = IntEnumField(Slip, null=True)
    slip_send: Slip = IntEnumField(Slip, null=True)
    abuser: AbuserType = IntEnumField(AbuserType, default=AbuserType.no)
    slavic: bool = BooleanField(null=True)
    mtl_like: bool = BooleanField(null=True)
    scale: int = SmallIntField(null=True)
    bank_side: bool = BooleanField(null=True)  # False - except these banks, True - only this banks
    sbp_strict: SbpStrict = IntEnumField(SbpStrict, default=SbpStrict.no)
    contact: str | None = CharField(127, null=True)
    done: bool = BooleanField(default=False, db_index=True)
    banks: ManyToManyRelation[Pm] = ManyToManyField("models.Pm", "cond_banks", related_name="conds", on_update=CASCADE)

    class Meta:
        table = "cond_parsed"


class Ad(Model, TsTrait):
    exid: int = UInt8Field(db_index=True)  # todo: спарить уникальность с биржей, тк на разных биржах могут совпасть
    pair_side: ForeignKeyRelation[PairSide] = ForeignKeyField("models.PairSide", "ads", on_update=CASCADE)
    price: int = UInt4Field()  # /10^cur.scale
    premium: int = SmallIntField(null=True)  # /10_000
    amount: int = UInt4Field()  # /10^cur.scale
    quantity: int = UInt8Field(null=True)  # /10^coinex.scale
    min_fiat: int = UInt4Field()  # /10^cur.scale
    max_fiat: int | None = UInt4Field(null=True)  # /10^cur.scale
    auto_msg: str | None = CharField(4095, null=True)
    status: AdStatus = IntEnumField(AdStatus, default=AdStatus.active)

    cond: ForeignKeyNullableRelation[Cond] = ForeignKeyField("models.Cond", "ads", on_update=CASCADE, null=True)
    cond_id: int
    maker: ForeignKeyRelation[Actor] = ForeignKeyField("models.Actor", "my_ads", on_update=CASCADE)
    maker_id: int

    pms: ManyToManyRelation["Pm"] = ManyToManyField("models.Pm", "ad_pm", related_name="ads", on_update=CASCADE)
    my_ad: BackwardOneToOneRelation["MyAd"]
    orders: BackwardFKRelation["Order"]

    _icon = "ad"
    _name = {"pair_side__pairex__coin__ticker", "pair_side__pairex__cur__ticker", "pair_side__sell", "price"}

    class Meta:
        table_description = "P2P Advertisements"
        unique_together = (("exid", "maker_id"),)

    # def epyds(self) -> tuple[PydModel, PydModel, PydModel, PydModel, PydModel, PydModel]:
    #     module_name = f"xync_client.{self.maker.ex.name}.pyd"
    #     __import__(module_name)
    #     return (
    #         sys.modules[module_name].AdEpyd,
    #         sys.modules[module_name].AdFullEpyd,
    #         sys.modules[module_name].MyAdEpydPurchase,
    #         sys.modules[module_name].MyAdInEpydPurchase,
    #         sys.modules[module_name].MyAdEpydSale,
    #         sys.modules[module_name].MyAdInEpydSale,
    #     )


class MyAd(Model):  # Road
    WEB = "https://www.bybit.com/ru-RU/p2p/{side}/{coin}/{cur}?share="
    MOB = "https://app.bybit.com/inapp?by_dp=bybitapp://open/route?targetUrl=by-mini://p2p/home?share="

    ad: OneToOneRelation[Ad] = OneToOneField("models.Ad", "my_ad", on_update=CASCADE)
    ad_id: int  # new
    target_place: int = UInt1Field(default=1)
    hex: bytes = BinaryField(null=True)
    shared_at: datetime | None = DatetimeSecField(null=True)

    pay_req: ForeignKeyNullableRelation["PayReq"] = ForeignKeyField(
        "models.PayReq", "maked_ads", on_update=CASCADE, null=True
    )
    credexs: ManyToManyRelation["CredEx"] = ManyToManyField(
        "models.CredEx", through="myad_cred", related_name="my_ads", on_update=CASCADE
    )
    race: BackwardFKRelation["Cred"]

    class Meta:
        table = "my_ad"

    def get_url(self):
        # if not self.hex:
        #     return None
        hx = self.hex.hex()
        side = "buy" if self.ad.pair_side.is_sell else "sell"
        coin, cur = self.ad.pair_side.pair.coin.ticker, self.ad.pair_side.pair.cur.ticker
        mob_pref = self.WEB.format(side=side, coin=coin, cur=cur)
        return mob_pref + hx, self.MOB + hx

    @classmethod
    # запрос для получения объяв всех агентов этой биржи для разогрева
    def hot_mads_query(cls, ex_ids: list[int]):
        return cls.filter(
            ad__maker__ex_id__in=ex_ids, ad__status=AdStatus.active, credexs__cred__ovr_pm_id=0
        ).prefetch_related("ad__pair_side__pair__coin", "ad__pair_side__pair__cur")


class Hot(Model, TsTrait):
    user: ForeignKeyNullableRelation[User] = ForeignKeyField("models.User", "hots", on_update=CASCADE)
    user_id: int
    actors: ManyToManyRelation[Actor] = ManyToManyField("models.Actor", related_name="hots", on_update=CASCADE)
    orders: ManyToManyRelation["Order"] = ManyToManyField("models.Order", related_name="hots", on_update=CASCADE)
    ads_shared: ManyToManyRelation[MyAd] = ManyToManyField("models.MyAd", related_name="hots", on_update=CASCADE)
    status = IntEnumField(HotStatus, default=HotStatus.opened)


class Race(Model):
    road: ForeignKeyRelation[MyAd] = ForeignKeyField("models.MyAd", "race", on_update=CASCADE)
    road_id: int
    ceil: int = UInt4Field(null=True)  # /10^cur.scale
    target_place: int = SmallIntField(default=1)
    vm_filter: bool = BooleanField(default=True)
    started: bool = BooleanField(default=True)
    filter_amount: int = UInt4Field()  # /10^cur.scale
    updated_at: datetime | None = DatetimeSecField(auto_now=True)

    stats: BackwardFKRelation["RaceStat"]

    # def overprice_filter(self, ads: list[BaseAd]):
    #     ads[0]
    #     # вырезаем ads с ценами выше потолка
    #     if ads and (self.ceil - Decimal(ads[0].price)) * k > 0:
    #         if int(ads[0].userId) != self.actor.exid:
    #             ads.pop(0)
    #             self.overprice_filter(ads, self.ceil, k)


class RaceStat(Model):
    race: ForeignKeyRelation[Race] = ForeignKeyField("models.Race", "stats", on_update=CASCADE)
    race_id: int
    rivals: ManyToManyRelation[Ad] = ManyToManyField("models.Ad", "rivals", related_name="stats", on_update=CASCADE)
    rival_id: int
    price: int = UInt4Field()  # /10^cur.scale
    premium: int = SmallIntField(null=True)  # /10_000
    place: int = UInt1Field()
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)

    class Meta:
        table = "race_stat"


class PmRep(Model):
    ex: ForeignKeyNullableRelation[Ex] = ForeignKeyField("models.Ex", "pm_reps", on_update=CASCADE, null=True)
    ex_id: int
    src: str | None = CharField(63, unique=True)
    target: str | None = CharField(63)
    used_at: datetime | None = DatetimeSecField(null=True)

    class Meta:
        table = "pm_rep"
        # unique_together = (("src", "target"),)


class PmAgent(Model):
    pm: ForeignKeyRelation[Pm] = ForeignKeyField("models.Pm", "agents", on_update=CASCADE)
    pm_id: int
    user: ForeignKeyRelation[User] = ForeignKeyField("models.User", "pm_agents", on_update=CASCADE)
    user_id: int
    auth: dict = JSONField(default={})
    state: dict = JSONField(default={})
    active: bool = BooleanField(null=True, default=False)

    class Meta:
        table = "pm_agent"
        unique_together = (("pm_id", "user_id"),)

    def client(self, bot=None, browser=None):
        module_name = f"xync_client.Pms.{self.pm.norm.capitalize()}.agent"
        __import__(module_name)
        kwargs = {}
        if bot:
            kwargs["bot"] = bot
        if browser:
            kwargs["browser"] = browser
        return sys.modules[module_name].PmAgentClient(self, **kwargs)


class PmCur(Model):  # for fiat with no exs tie
    pm: ForeignKeyRelation[Pm] = ForeignKeyField("models.Pm", on_update=CASCADE)
    pm_id: int
    cur: ForeignKeyRelation[Cur] = ForeignKeyField("models.Cur", on_update=CASCADE)
    cur_id: int

    creds: BackwardFKRelation["Cred"]
    sends: BackwardFKRelation["Transfer"]
    exs: ManyToManyRelation[Ex]

    class Meta:
        table_description = "Payment methods - Currencies"
        unique_together = (("pm_id", "cur_id"),)

    class PydanticMeta(Model.PydanticMeta):
        max_recursion: int = 2  # default: 3
        include = "cur_id", "pm"


class PmEx(BaseModel):  # existence pm in ex with no cur tie
    ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex", "pmexs", on_update=CASCADE)
    ex_id: int
    pm: ForeignKeyRelation[Pm] = ForeignKeyField("models.Pm", "pmexs", on_update=CASCADE)
    pm_id: int
    logo: ForeignKeyNullableRelation["File"] = ForeignKeyField(
        "models.File", "pmex_logos", on_update=CASCADE, null=True
    )
    logo_id: int
    exid: str = CharField(63)
    name: str = CharField(63)

    banks: BackwardFKRelation["PmExBank"]

    class Meta:
        unique_together = (("ex_id", "exid"),)  # , ("ex", "pm"), ("ex", "name")  # todo: tmp removed for HTX duplicates


class PmExBank(BaseModel):  # banks for SBP
    pmex: ForeignKeyRelation[PmEx] = ForeignKeyField("models.PmEx", "banks", on_update=CASCADE)
    pmex_id: int
    exid: str = CharField(63)
    name: str = CharField(63)

    creds: ManyToManyRelation["Cred"]

    class Meta:
        table = "pmex_bank"
        unique_together = (("pmex", "exid"),)


# class PmCurEx(BaseModel):  # existence pm in ex for exact cur, with "blocked" flag
#     pmcur: ForeignKeyRelation[PmCur] = ForeignKeyField("models.PmCur")
#     pmcur_id: int
#     ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex")
#     ex_id: int
#     blocked: bool = BooleanField(default=False)  # todo: move to curex or pmex?
#
#     # class Meta:
#     #     unique_together = (("ex_id", "pmcur_id"),)


class Cred(Model):
    pmcur: ForeignKeyRelation[PmCur] = ForeignKeyField("models.PmCur", on_update=CASCADE)
    pmcur_id: int
    detail: str = CharField(255)
    name: str | None = CharField(127, null=True)
    extra: str | None = CharField(255, null=True)
    person: ForeignKeyRelation[Person] = ForeignKeyField("models.Person", "creds")
    person_id: int
    from_chat: int  # todo: ForeignKeyNullableRelation["Order"] = ForeignKeyField("models.Order", null=True)

    ovr_pm: ForeignKeyRelation[Pm] = ForeignKeyField("models.Pm", on_update=CASCADE, null=True)
    ovr_pm_id: int
    banks: ManyToManyRelation[PmExBank] = ManyToManyField("models.PmExBank", related_name="creds", on_update=CASCADE)

    fiat: BackwardOneToOneRelation["Fiat"]
    receives: BackwardOneToOneRelation["Transfer"]
    credexs: BackwardFKRelation["CredEx"]
    orders: BackwardFKRelation["Order"]
    pay_reqs: BackwardFKRelation["PayReq"]

    _name = {"detail"}

    def repr(self):
        xtr = f" ({self.extra})" if self.extra else ""
        name = f", имя: {self.name}" if self.name else ""
        return f"`{self.detail}`{name}{xtr}"

    class Meta:
        table_description = "Currency accounts"
        unique_together = (("person_id", "pmcur_id", "ovr_pm_id"),)


@pre_save(Cred)
async def cred_ovr_pm(_meta, cred: Cred, _db, _updated: dict) -> None:
    # payeer
    op = None
    if "payeer" in cred.extra.lower() or "payeer" in cred.detail.lower():
        op = 366
    elif re.match(r"[PpРр]\d{7,10}\b", cred.detail):
        op = 366
    elif re.match(r"[PpРр]\d{7,10}\b", cred.extra):
        op = 366
    # volet
    if (
        "volet" in cred.detail.lower()
        or "advcash" in cred.detail.lower()
        or "volet" in cred.extra.lower()
        or "advcash" in cred.extra.lower()
    ):
        op = 545
    elif re.match(r"[REUTLD]\d{4} ?\d{4} ?\d{4}\b", cred.detail):
        op = 545
    elif re.match(r"[REUTLD]\d{4} ?\d{4} ?\d{4}\b", cred.extra):
        op = 545

    if op and op != (await cred.pmcur).pm_id:
        cred.ovr_pm_id = op


class CredEx(Model):
    exid: int = UInt8Field()
    cred: ForeignKeyRelation[Cred] = ForeignKeyField("models.Cred", "credexs", on_update=CASCADE)
    cred_id: int
    ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex", "credexs", on_update=CASCADE)
    ex_id: int

    _name = {"exid"}

    class Meta:
        table_description = "Credential on Exchange"
        unique_together = (("ex_id", "exid"),)


class Fiat(Model):
    cred: OneToOneRelation[Cred] = OneToOneField("models.Cred", "fiat", on_update=CASCADE)
    cred_id: int
    amount: int = UInt4Field()  # /10^cur.scale
    target: int = UInt4Field(null=True)  # /10^cur.scale
    min_deposit: int = UInt4Field(null=True)  # /10^cur.scale

    class Meta:
        table_description = "Currency balances"

    class PydanticMeta(Model.PydanticMeta):
        # max_recursion: int = 2
        backward_relations = False
        include = "id", "cred__pmcur", "cred__detail", "cred__name", "amount"

    @staticmethod
    def epyd(ex: Ex):
        module_name = f"xync_client.{ex.name}.pyd"
        __import__(module_name)
        return sys.modules[module_name].FiatEpyd


class Limit(Model):
    pmcur: ForeignKeyRelation[PmCur] = ForeignKeyField("models.PmCur", on_update=CASCADE)
    pmcur_id: int
    amount: int = UInt4Field(null=True)  # '$' if unit >= 0 else 'transactions count'
    unit: int = UInt1Field(default=30)  # positive: $/days, 0: $/transaction, negative: transactions count / days
    # 0 - same group, 1 - to parent group, 2 - to grandparent # only for output trans, on input = None
    level: float | None = UInt1Field(default=0, null=True)
    income: bool = BooleanField(default=False)
    added_by: ForeignKeyRelation["User"] = ForeignKeyField("models.User", "limits", on_update=CASCADE)
    added_by_id: int

    _name = {"pmcur__pm__name", "pmcur__cur__ticker", "unit", "income", "amount"}

    class Meta:
        table_description = "Currency accounts balance"


class Addr(Model):
    coin: ForeignKeyRelation[Coin] = ForeignKeyField("models.Coin", "addrs", on_update=CASCADE)
    coin_id: int
    actor: ForeignKeyRelation[Actor] = ForeignKeyField("models.Actor", "addrs", on_update=CASCADE)
    actor_id: int

    nets: ManyToManyRelation[Net] = ManyToManyField("models.Net", "net_addr", related_name="addrs", on_update=CASCADE)

    pay_reqs: BackwardFKRelation["PayReq"]

    _name = {"coin__ticker", "free"}

    class Meta:
        table_description = "Coin address on cex"
        unique_together = (("coin_id", "actor_id"),)


class Asset(Model):
    addr: ForeignKeyRelation[Addr] = ForeignKeyField("models.Addr", "addrs", on_update=CASCADE)
    addr_id: int
    agent: ForeignKeyRelation[Agent] = ForeignKeyField("models.Agent", "assets", on_update=CASCADE)
    agent_id: int
    typ: AddrExType = IntEnumField(AddrExType, default=AddrExType.found)
    free: int = UInt8Field()  # /10^coinex.scale
    freeze: int | None = UInt8Field(default=0)  # /10^coinex.scale
    lock: int | None = UInt8Field(default=0)  # /10^coinex.scale
    target: int | None = UInt8Field(default=0, null=True)  # /10^coinex.scale

    _name = {"asset__coin__ticker", "free"}

    class Meta:
        table_description = "Coin balance"
        unique_together = (("addr_id", "agent_id", "typ"),)

    def epyd(self):
        module_name = f"xync_client.{self.agent.ex.name}.pyd"
        __import__(module_name)
        return sys.modules[module_name].AssetEpyd


class PayReq(Model, TsTrait):
    pay_until: datetime = DatetimeSecField()
    addr: ForeignKeyNullableRelation[Addr] = ForeignKeyField("models.Addr", "pay_reqs", on_update=CASCADE, null=True)
    addr_id: int
    cred: ForeignKeyNullableRelation[Cred] = ForeignKeyField("models.Cred", "pay_reqs", on_update=CASCADE, null=True)
    cred_id: int
    user: ForeignKeyRelation[User] = ForeignKeyField("models.User", "pay_reqs", on_update=CASCADE)
    user_id: int
    amount: float = UInt4Field()
    parts: int = UInt1Field(default=1)
    payed_at: datetime | None = DatetimeSecField(null=True)

    maked_ads: BackwardFKRelation["MyAd"]
    taken_orders: BackwardFKRelation["Order"]

    _icon = "pay"
    _name = {"ad_id"}

    class Meta:
        table_description = "Payment request"
        unique_together = (("user_id", "cred_id", "addr_id"),)


class Order(Model):
    exid: int = UInt8Field(unique=True)  # todo: спарить уникальность с биржей, тк на разных биржах могут совпасть
    ad: ForeignKeyRelation[Ad] = ForeignKeyField("models.Ad", "ads", on_update=CASCADE)
    ad_id: int
    amount: int = UInt4Field()  # /10^cur.scale
    quantity: int = UInt8Field(null=True)  # /10^coinex.scale
    cred: ForeignKeyRelation[Cred] = ForeignKeyField("models.Cred", "orders", on_update=CASCADE, null=True)
    cred_id: int | None
    taker: ForeignKeyRelation[Actor] = ForeignKeyField("models.Actor", "taken_orders", on_update=CASCADE)
    taker_id: int
    payreq: ForeignKeyNullableRelation[PayReq] = ForeignKeyField(
        "models.PayReq", "taken_orders", on_update=CASCADE, null=True
    )
    payreq_id: int
    maker_topic: int = UInt2Field(null=True)  # todo: remove nullability
    taker_topic: int = UInt2Field(null=True)
    status: OrderStatus = IntEnumField(OrderStatus, default=OrderStatus.created)
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)
    payed_at: datetime | None = DatetimeSecField(null=True)
    confirmed_at: datetime | None = DatetimeSecField(null=True)
    appealed_at: datetime | None = DatetimeSecField(null=True)
    chat_parsed: bool = BooleanField(default=False)

    msgs: BackwardFKRelation["Msg"]
    transfers: BackwardFKRelation["Transfer"]

    _name = {"cred__pmcur__pm__name"}

    def ami_maker(self, uid: int) -> bool:
        return self.taker_id != uid

    async def ami_seller(self, uid: int) -> bool:
        await self.fetch_related("ad__pair_side")  # todo: check and fetch if only need
        return self.ad.pair_side.is_sell == self.ami_maker(uid)

    async def client(self):
        if isinstance(self.ad, QuerySet):
            # noinspection PyTypeChecker
            self.ad: Ad = await self.ad.prefetch_related("agent__ex")
        elif isinstance(self.ad, Ad) and isinstance(self.ad.agent, QuerySet):
            # noinspection PyTypeChecker
            self.ad.agent = await self.ad.agent.prefetch_related("ex")
        elif isinstance(self.ad.agent, Agent) and isinstance(self.ad.agent.ex, QuerySet):
            # noinspection PyTypeChecker
            self.ad.agent.ex = await self.ad.agent.ex
        client = sys.modules[f"xync_client.{self.ad.maker.ex.name}.order"].Client
        return client(self)

    async def get_chat(self):
        await self.fetch_related("ad__pair_side", "msgs")
        return [
            f"{'b' if self.ad.pair_side.is_sell == m.to_maker else 's'}{m.to_maker and 't' or 'm'}: {m.txt or '<file>'}"
            for m in self.msgs
        ]

    # когда прилетел новый ордер, и мы уже знаем юзера которому он принадлежит
    async def hot_process(self, user: User):
        # берем последнюю активную сессиию прогрева юзера, и прикрепляем ордер к ней
        hot_db = (
            await Hot.filter(
                ads_shared=self.ad.my_ad, updated_at__gte=now() - timedelta(hours=2), status=HotStatus.opened, user=user
            )
            .order_by("-updated_at")
            .first()
        )
        await hot_db.orders.add(self)
        me = await User.get(person__actors__id=self.ad.maker_id)
        t = dict(amount=self.amount, cur_id=self.ad.pair_side.pair.cur_id, ts=now())
        if self.ad.pair_side.is_sell:  # me - maker - seller
            if self.status != OrderStatus.completed:  # dup requests reject
                dep = await user.balance(self.ad.pair_side.pair.cur_id)
                if dep < self.amount:
                    return 0, dep
                self.status = OrderStatus.completed
                self.confirmed_at = now()
                await Transaction.create(sender=user, receiver=me, **t, status=TransactionStatus.valid)
                await self.save(update_fields=["status", "confirmed_at"])
                res = 2
            else:
                res = 3
        else:  # me - maker - buyer
            if self.status != OrderStatus.paid:  # dup requests reject
                self.status = OrderStatus.paid
                self.payed_at = now()
                await Transaction.create(sender=me, receiver=user, **t, status=TransactionStatus.valid)
                await self.save(update_fields=["status", "payed_at"])
                res = 1
            else:
                res = 3
        return res, await user.balance(self.ad.pair_side.pair.cur_id)

    # def epyd(self):  # todo: for who?
    #     module_name = f"xync_client.{self.ex.name}.pyd"
    #     __import__(module_name)
    #     return sys.modules[module_name].OrderEpyd

    class Meta:
        table_description = "P2P Orders"

    class PydanticMeta(Model.PydanticMeta):
        max_recursion: int = 0
        exclude_raw_fields: bool = False
        exclude = ("taker", "ad", "cred", "msgs")


# @pre_save(Order)
# async def new_order(_meta, order: Order, _db, _updated: dict) -> None:
#     # todo: define is_new
#     if order.status == OrderStatus.created:
#         # возвращаем остаток монеты
#         ass = await models.Asset.get(
#             addr__coin_id=order.ad.pair_side.pair.coin_id,
#             addr__actor=self.agent_client.actor,
#         )
#         ass.free += order_db.quantity
#         await ass.save(update_fields=["free"])


class Task(Model):
    order: ForeignKeyRelation[Order] = ForeignKeyField("models.Order", "tasks", on_update=CASCADE)
    typ: TaskType = IntEnumField(TaskType)
    data: dict = JSONField()


class Transaction(Model):
    id: UUID = UUIDField(primary_key=True)
    amount: int = UInt4Field()  # /10^cur.scale
    cur: ForeignKeyRelation["Cur"] = ForeignKeyField("models.Cur", "transfers", on_update=CASCADE)
    cur_id: int
    sender: ForeignKeyRelation[User] = ForeignKeyField("models.User", "sends", on_update=CASCADE, null=True)
    sender_id: int | None
    receiver: ForeignKeyRelation[User] = ForeignKeyField("models.User", "receives", on_update=CASCADE)
    receiver_id: int
    # validator: ForeignKeyRelation[User] = ForeignKeyField("models.User", "validates", null=True)
    # validator_id: int
    status: TS = IntEnumField(TS)
    proof: bytes = UniqBinaryField(unique=True, null=True)  # len=128
    ts: datetime | None = DatetimeSecField(null=True)

    def is_expired(self) -> bool:
        """Проверка истёк ли запрос"""
        assert not self.proof and self.ts, "It is method for ttl requests only"
        return datetime.now(timezone.utc) > self.ts

    def is_valid_sender(self, sender_id: int) -> bool:
        """Проверка может ли отправитель оплатить этот запрос"""
        assert self.proof is None, "It is method for requests only"
        return self.sender_id is None or self.sender_id == sender_id

    @property
    def pack(self) -> bytes:
        def cr(cur_id: int, rec_id: int):
            """Упаковка валюта + получатель в 1+4=5 байт"""
            return struct.pack(">BL", cur_id, rec_id)

        def cra(cur_id: int, rec_id: int, amount: int):
            """Упаковка валюта + получатель + сумма в 1+4+4=9 байт"""
            return cr(cur_id, rec_id) + struct.pack(">L", amount)

        def tcras(ts: int, cur_id: int, rec_id: int, amount: int, sender_id: int):
            """Упаковка время+валюта+получатель+сумма+отправитель в 1+3+4+4+4=16 байт"""
            tsb = struct.pack(">L", ts - 1756566000)[:3]  # 3 todo: upd base ts
            return tsb + cra(cur_id, rec_id, amount) + struct.pack(">L", sender_id)

        # если это запрос, то все, пруфа нет и не нужен
        if self.status == TS.request:
            assert not self.proof, f"no need proof `{self.proof}` for request"
            return cra(
                self.cur_id,  # 1
                self.receiver_id,  # 4
                self.amount,  # 4
            )

        # иначе это отправка
        assert self.ts, "Time of sending is required"
        assert (
            ((pl := len(self.proof or b"")) == 0 and not self.status)
            or (self.status == TS.signed and pl == 64)
            or (self.status == TS.valid and pl == 128)
        ), f"wrong proof length `{pl}` for `{self.status.name}` transaction"

        return tcras(int(self.ts.timestamp()), self.cur_id, self.receiver_id, self.amount, self.sender_id)

    # async def sender_sign(self):  # moved to front
    #     assert self.status == TS.not_signed, "It is method for not signed transfers only"
    #     await self.fetch_related("sender")
    #     sender_prv = Ed25519PrivateKey.from_private_bytes(self.sender.prv)
    #     self.proof = sender_prv.sign(self.pack)
    #     # после создания прупа(+64) отправителя пак удлиннился с 21 байта до 85
    #     await self.save(update_fields=["proof"])

    async def approve(self, prv: bytes):
        assert self.status == TS.signed, "It is method for signed transfers only"
        assert len(self.proof) == 64, "Sender did not signed yet"
        # 1. Проверяем подпись отправителя
        snd_pub = Ed25519PublicKey.from_public_bytes(self.sender.pub)
        # отправитель подписывал транзу когда в ней еще не было пруфа, поэтому проверяем обрезок пака до него
        snd_pub.verify(self.proof, self.pack)
        # 2. Проверяем что баланс отправителя не меньшы отправляемой суммы. # todo: remove origin hack
        assert await self.sender.balance(self.cur_id) >= self.amount or not self.sender_id, "B"
        # 3. Подписываем
        pk = Ed25519PrivateKey.from_private_bytes(prv)
        self.proof += pk.sign(self.pack)  # и добавляет эту подпись к пруфу 85+64=149
        self.status = TS.valid
        # Только две подписи: отправителя + валидатора (128 байт)
        await self.save(update_fields=["proof", "status"])

    def check(self, vld_pub: bytes = None) -> bool:
        """Проверка доказательства"""
        if len(self.proof) != 128:  # 64 + 64
            return False  # wrong size
        sender_sig, vld_sig = self.proof[:64], self.proof[64:128]
        try:
            # Проверяем подпись отправителя
            sender_pub = Ed25519PublicKey.from_public_bytes(self.sender.pub)
            sender_pub.verify(sender_sig, self.pack)
            # Проверяем подпись валидатора
            if vld_pub:
                vld_pub = Ed25519PublicKey.from_public_bytes(vld_pub)
                vld_pub.verify(vld_sig, self.pack)
            return True
        except InvalidSignature as _:
            return False  # wrong sign


class Sign(Model):
    transaction: ForeignKeyRelation[Transaction] = ForeignKeyField("models.Transaction", "signs", on_update=CASCADE)
    transaction_id: int
    validator: ForeignKeyRelation[User] = ForeignKeyField("models.User", "approves", on_update=CASCADE)
    validator_id: int
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)


# class Checkpoint(Model):
#     amount: int = BigIntField()  # /10^cur.scale
#     cur: ForeignKeyRelation["Cur"] = ForeignKeyField("models.Cur", related_name="transfers")
#     cur_id: int
#     user: ForeignKeyRelation[User] = ForeignKeyField("models.User", "checkpoints", null=True)
#     user_id: int | None
#
#     class Meta:
#         unique_together = (("user_id", "cur_id"),)


class Transfer(Model):
    amount: int = UInt4Field()  # /10^cur.scale
    order: ForeignKeyRelation[Order] = ForeignKeyField("models.Order", "transfer", on_update=CASCADE, null=True)
    order_id: int
    file: OneToOneNullableRelation["File"] = OneToOneField("models.File", "transfer", on_update=CASCADE, null=True)
    file_id: int
    pmid: str = CharField(31, unique=True, null=True)
    sender_acc: str = CharField(31, null=True)
    # pm: ForeignKeyRelation["Pm"] = ForeignKeyField("models.Pm", "transfers", on_update=CASCADE)
    # pm_id: int
    updated_at: datetime | None = DatetimeSecField(auto_now=True)

    # class Meta:
    #     unique_together = (("pmid", "pm_id"),)


class Msg(Model):
    tg_mid: int = UInt4Field(null=True)
    txt: str = CharField(4095, null=True)
    read: bool = BooleanField(default=False, db_index=True)
    to_maker: bool = BooleanField()
    file: OneToOneNullableRelation["File"] = OneToOneField("models.File", "msg", on_update=CASCADE, null=True)
    order: ForeignKeyRelation[Order] = ForeignKeyField("models.Order", "msgs", on_update=CASCADE)
    sent_at: datetime | None = DatetimeSecField()

    # todo: required txt or file
    class PydanticMeta(Model.PydanticMeta):
        max_recursion: int = 0
        exclude_raw_fields: bool = False
        exclude = ("receiver", "order")

    class Meta:
        unique_together = (
            ("order", "txt"),
            # ("order", "sent_at"),
        )


class TopUpAble(Model):
    pm: OneToOneRelation[Pm] = OneToOneField("models.Pm", "topupable", on_update=CASCADE)
    pm_id: int
    url: str = CharField(127)
    auth: dict = JSONField(default={})
    fee: int = SmallIntField(default=0)  # /10_000


class TopUp(Model):
    topupable: ForeignKeyRelation[TopUpAble] = ForeignKeyField("models.TopUpAble", "topup", on_update=CASCADE)
    topupable_id: int
    pmid: str = CharField(36, unique=True, null=True)
    tid: str = CharField(36, unique=True, null=True)
    amount: int = UInt4Field()  # /10^cur.scale
    cur: ForeignKeyRelation["Cur"] = ForeignKeyField("models.Cur", "topups", on_update=CASCADE)
    cur_id: int
    user: ForeignKeyRelation[User] = ForeignKeyField("models.User", "topups", on_update=CASCADE)
    user_id: int
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)
    completed_at: datetime | None = DatetimeSecField(null=True)


class Dep(Model, TsTrait):
    pid: str = CharField(31)  # product_id
    apr: int = UInt2Field()  # /10_000
    fee: int | None = UInt2Field(null=True)  # /10_000
    apr_is_fixed: bool = BooleanField(default=False)
    duration: int | None = UInt2Field(null=True)
    early_redeem: bool | None = BooleanField(null=True)
    typ: DepType = IntEnumField(DepType)
    # mb: renewable?
    min_limit: float = UInt8Field()
    max_limit: float | None = UInt8Field(null=True)
    is_active: bool = BooleanField(default=True)

    coin: ForeignKeyRelation[Coin] = ForeignKeyField("models.Coin", "deps", on_update=CASCADE)
    coin_id: int
    reward_coin: ForeignKeyRelation[Coin] = ForeignKeyField("models.Coin", "deps_reward", on_update=CASCADE, null=True)
    reward_coin_id: int | None = None
    bonus_coin: ForeignKeyRelation[Coin] = ForeignKeyField("models.Coin", "deps_bonus", on_update=CASCADE, null=True)
    bonus_coin_id: int | None = None
    ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex", "deps", on_update=CASCADE)
    ex_id: int
    investments: BackwardFKRelation["Investment"]

    _icon = "seeding"
    _name = {"pid"}

    def repr(self):
        return (
            f"{self.coin.ticker}:{self.apr * 100:.3g}% "
            f"{f'{self.duration}d' if self.duration and self.duration > 0 else 'flex'}"
        )

    class Meta:
        table_description = "Investment products"
        unique_together = (("pid", "typ", "ex_id"),)


class Investment(Model, TsTrait):
    dep: ForeignKeyRelation[Dep] = ForeignKeyField("models.Dep", "investments", on_update=CASCADE)
    # dep_id: int
    amount: float = UInt8Field()
    is_active: bool = BooleanField(default=True)
    user: ForeignKeyRelation[User] = ForeignKeyField("models.User", "investments", on_update=CASCADE)

    _icon = "trending-up"
    _name = {"dep__pid", "amount"}

    def repr(self):
        return f"{self.amount:.3g} {self.dep.repr()}"

    class Meta:
        table_description = "Investments"


class ExStat(Model):
    ex: ForeignKeyRelation[Ex] = ForeignKeyField("models.Ex", "stats", on_update=CASCADE)
    ex_id: int
    action: ExAction = IntEnumField(ExAction)
    ok: bool | None = BooleanField(default=False, null=True)
    updated_at: datetime | None = DatetimeSecField(auto_now=True)

    _icon = "test-pipe"
    _name = {"ex_id", "action", "ok"}

    def repr(self):
        return f"{self.ex_id} {self.action.name} {self.ok}"

    class Meta:
        table = "ex_stat"
        table_description = "Ex Stats"
        unique_together = (("action", "ex_id"),)

    class PydanticMeta(Model.PydanticMeta):
        max_recursion: int = 2


class Vpn(Model):
    user: OneToOneRelation[User] = OneToOneField("models.User", "vpn", on_update=CASCADE)
    user_id: int
    prv: str = CharField(63, unique=True)
    pub: str = CharField(63, unique=True)
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)

    _icon = "vpn"
    _name = {"pub"}

    def repr(self):
        return self.user.username

    class Meta:
        table_description = "VPNs"


class File(Model):
    name: str = CharField(178, null=True, unique=True)
    typ: FileType = IntEnumField(FileType)
    ref: bytes = UniqBinaryField(unique=True)
    size: bytes = UInt4Field()
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)

    msg: BackwardOneToOneRelation[Msg]
    transfer: BackwardOneToOneRelation[Transfer]
    pmex_logos: BackwardFKRelation[PmEx]

    _icon = "file"
    _name = {"name"}

    class Meta:
        table_description = "Files"
        # Создаем индекс через raw SQL
        # indexes = ["CREATE UNIQUE INDEX IF NOT EXISTS idx_bytea_unique ON file (encode(sha256(ref), 'hex'))"]


class Invite(Model, TsTrait):
    ref: ForeignKeyRelation[User] = ForeignKeyField("models.User", "invite_approvals", on_update=CASCADE)
    ref_id: int
    protege: ForeignKeyRelation[User] = ForeignKeyField("models.User", "invite_requests", on_update=CASCADE)
    protege_id: int
    approved: str = BooleanField(default=False)  # status

    _icon = "invite"
    _name = {"ref__username", "protege__username", "approved"}

    def repr(self):
        return self.protege.name

    class Meta:
        table_description = "Invites"


class Credit(Model, TsTrait):
    lender: ForeignKeyRelation[User] = ForeignKeyField("models.User", "lends", on_update=CASCADE)
    lender_id: int
    borrower: ForeignKeyRelation[User] = ForeignKeyField("models.User", "borrows", on_update=CASCADE)
    borrower_id: int
    borrower_priority: bool = BooleanField(default=True)
    amount: int = UInt4Field(default=None)  # 0 - is all remain borrower balance

    _icon = "credit"
    _name = {"lender__username", "borrower__username", "amount"}

    def repr(self):
        return self.borrower.name

    class Meta:
        table_description = "Credits"
