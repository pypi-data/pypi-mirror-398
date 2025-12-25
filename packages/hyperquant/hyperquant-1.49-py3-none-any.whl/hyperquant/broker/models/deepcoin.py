from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Awaitable

import aiohttp
from pybotters.store import DataStore, DataStoreCollection

if TYPE_CHECKING:
    from pybotters.typedefs import Item
    from pybotters.ws import ClientWebSocketResponse


_DEFAULT_QUOTE = "USDT"
_DEFAULT_INST_TYPE = "SWAP"


def _extract_base(value: Any) -> str | None:
    """Extract the base currency (e.g., BTC) from various identifier forms."""
    if not value:
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    for sep in ("/", "_"):
        text = text.replace(sep, "-")
    if text.endswith("-SWAP"):
        text = text[:-5]
    parts = text.split("-")
    candidate = parts[0] if parts else text
    if candidate.endswith(_DEFAULT_QUOTE):
        candidate = candidate[: -len(_DEFAULT_QUOTE)]
    candidate = candidate.replace(" ", "")
    return candidate or None


def _ensure_identifiers(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure symbol is formatted as BTCUSDT and instId as BTC-USDT-SWAP
    assuming DeepCoin swap instruments quote in USDT.
    """
    base = (
        entry.get("baseCcy")
        or entry.get("base")
        or _extract_base(entry.get("instId"))
        or _extract_base(entry.get("I"))
        or _extract_base(entry.get("symbol"))
        or _extract_base(entry.get("s"))
    )
    if not base:
        return entry

    base = str(base).upper()
    symbol = f"{base}{_DEFAULT_QUOTE}"
    inst_id = f"{base}-{_DEFAULT_QUOTE}-{_DEFAULT_INST_TYPE}"

    entry["s"] = symbol
    entry["symbol"] = symbol
    entry["instId"] = inst_id
    entry["I"] = inst_id
    return entry


def _get_ticker(msg:dict) -> dict | None:
    r = msg.get("r", [])
    if len(r) == 0:
        return None
    ticker = r[0].get('d')
    if ticker:
        _ensure_identifiers(ticker)
    return ticker

class Detail(DataStore):
    _KEYS = ["s"]

    def _on_response(self, msg: dict[str, Any]) -> None:
        data = msg.get('data', [])
        # 展开data 新增tick_size 同 tickSize 字段 step_size 同 lotSize 字段
        for item in data:
            _ensure_identifiers(item)
            if 'tickSize' in item:
                item['tick_size'] = item['tickSize']
            elif 'tickSz' in item:
                item['tick_size'] = item['tickSz']
            if 'lotSize' in item:
                item['step_size'] = item['lotSize']
            elif 'lotSz' in item:
                item['step_size'] = item['lotSz']

        self._update(data)

class Ticker(DataStore):
    _KEYS = ["s"]

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        normalized_entry = _ensure_identifiers(dict(entry))
        symbol = normalized_entry.get("s")
        if not symbol:
            return None

        normalized = dict(normalized_entry)

        bid = entry.get("bidPx") or entry.get("BP1")
        ask = entry.get("askPx") or entry.get("AP1")
        try:
            if bid is not None:
                normalized["BP1"] = float(bid)
        except (TypeError, ValueError):
            pass
        try:
            if ask is not None:
                normalized["AP1"] = float(ask)
        except (TypeError, ValueError):
            pass

        return normalized

    def _on_response(self, msg: dict[str, Any]) -> None:
        data = msg.get("data") or []
        items: list[dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize(entry)
            if normalized:
                items.append(normalized)

        self._clear()
        if items:
            self._insert(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        ticker = _get_ticker(msg)
        if ticker:
            self._update([ticker])


class Book(DataStore):
    """用ticker数据构建的深度数据(book_best)"""

    _KEYS = ["s", "S"]

    def _init(self) -> None:
        self.limit: int | None = None
        self.id_to_symbol: dict[str, str] = {}
        self._state: dict[str, dict[str, dict[float, float]]] = {}


    def _on_message(self, msg: dict[str, Any]) -> None:
        ticker = _get_ticker(msg)
        if not ticker:
            return

        symbol = ticker.get("s")
        self._update([
            {
                's': symbol,
                'S': 'b',
                'p': float(ticker.get('BP1', 0)),
                'q': 0
            },{
                's': symbol,
                'S': 'a',
                'p': float(ticker.get('AP1', 0)),
                'q': 0
            }
        ])


class Balance(DataStore):
    """资金余额数据。"""

    _KEYS = ["ccy"]

    @staticmethod
    def _normalize_rest(entry: dict[str, Any]) -> dict[str, Any] | None:
        ccy = entry.get("ccy")
        if not ccy:
            return None
        normalized = {
            "ccy": str(ccy),
            "bal": entry.get("bal"),
            "availBal": entry.get("availBal"),
            "frozenBal": entry.get("frozenBal"),
        }
        if entry.get("withdrawable") is not None:
            normalized["withdrawable"] = entry.get("withdrawable")
        return normalized

    @staticmethod
    def _normalize_ws(data: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None
        mapping = {
            "A": "accountId",
            "B": "bal",
            "C": "ccy",
            "M": "memberId",
            "W": "withdrawable",
            "a": "availBal",
            "u": "useMargin",
            "c": "closeProfit",
            "FF": "frozenFee",
            "FM": "frozenMargin",
        }
        normalized: dict[str, Any] = {}
        for key, value in data.items():
            target = mapping.get(key)
            if target:
                normalized[target] = value
            else:
                normalized[key] = value
        if "ccy" not in normalized and "C" in data:
            normalized["ccy"] = data["C"]
        if "bal" not in normalized and "B" in data:
            normalized["bal"] = data["B"]
        if not normalized.get("ccy"):
            return None
        return normalized

    def _on_response(self, msg: dict[str, Any]) -> None:
        data = msg.get("data") or []
        items: list[dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize_rest(entry)
            if normalized:
                items.append(normalized)

        self._clear()
        if items:
            self._insert(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        results = msg.get("result") or []
        for item in results:
            data = item.get("data") if isinstance(item, dict) else None
            normalized = self._normalize_ws(data or {})
            if not normalized:
                continue
            key = {"ccy": str(normalized["ccy"])}
            if self.get(key):
                self._update([normalized])
            else:
                self._insert([normalized])


class Position(DataStore):
    """仓位数据。"""

    _KEYS = ["instId", "posSide"]

    @staticmethod
    def _normalize_rest(entry: dict[str, Any]) -> dict[str, Any] | None:
        normalized = _ensure_identifiers(dict(entry))
        inst_id = normalized.get("instId")
        pos_side = normalized.get("posSide")
        if not inst_id or pos_side is None:
            return None
        normalized["instId"] = str(inst_id)
        normalized["posSide"] = str(pos_side)
        return normalized

    @staticmethod
    def _normalize_ws(data: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None
        mapping = {
            "A": "accountId",
            "I": "instId",
            "M": "memberId",
            "OP": "avgPx",
            "Po": "pos",
            "U": "updateTime",
            "p": "posSide",
            "u": "useMargin",
            "c": "closeProfit",
            "l": "lever",
            "i": "isCrossMargin",
        }
        normalized: dict[str, Any] = {}
        for key, value in data.items():
            target = mapping.get(key)
            if target:
                normalized[target] = value
            else:
                normalized[key] = value
        normalized = _ensure_identifiers(normalized)
        if "posSide" not in normalized and "p" in data:
            normalized["posSide"] = str(data["p"])
  
        if not normalized.get("instId") or normalized.get("posSide") is None:
            return None
        return normalized

    def _on_response(self, msg: dict[str, Any]) -> None:
        data = msg.get("data") or []
        items: list[dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize_rest(entry)
            if normalized:
                items.append(normalized)

        self._clear()
        if items:
            self._insert(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        results = msg.get("result") or []
        for item in results:
            data = item.get("data") if isinstance(item, dict) else None
            normalized = self._normalize_ws(data or {})
            if not normalized:
                continue
            key = {"instId": normalized["instId"], "posSide": normalized["posSide"]}
            if normalized.get("pos") in {None, 0, "0"}:
                self._delete([key])
                continue
            if self.get(key):
                self._update([normalized])
            else:
                self._insert([normalized])


class Orders(DataStore):
    """当前委托。"""

    _KEYS = ["ordId"]


    @staticmethod
    def _normalize_rest(entry: dict[str, Any]) -> dict[str, Any] | None:
        ord_id = entry.get("ordId") or entry.get("ordID")
        if not ord_id:
            return None
        normalized = dict(entry)
        normalized["ordId"] = str(ord_id)
        normalized = _ensure_identifiers(normalized)
        if "instId" in normalized and normalized["instId"] is not None:
            normalized["instId"] = str(normalized["instId"])
        return normalized

    @staticmethod
    def _normalize_ws(data: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None
        mapping = {
            "L": "clOrdId",
            "I": "instId",
            "OPT": "orderPriceType",
            "D": "direction",
            "o": "offsetFlag",
            "P": "px",
            "V": "sz",
            "OT": "ordType",
            "i": "isCrossMargin",
            "OS": "ordId",
            "l": "lever",
            "Or": "state",
            "v": "accFillSz",
            "IT": "insertTime",
            "U": "updateTime",
            "T": "turnover",
            "p": "posiDirection",
            "t": "fillPx",
        }
        normalized: dict[str, Any] = {}
        for key, value in data.items():
            target = mapping.get(key)
            if target:
                normalized[target] = value
            else:
                normalized[key] = value
        normalized = _ensure_identifiers(normalized)
        if "ordId" not in normalized and "OS" in data:
            normalized["ordId"] = str(data["OS"])
        if "state" in normalized and isinstance(normalized["state"], (int, float)):
            normalized["state"] = str(normalized["state"])
        normalized = _ensure_identifiers(normalized)
        if not normalized.get("ordId"):
            return None
        # state_tomap  # 4 live 6 cancel 1 filled # todo
        state_map = {
            "0": "filled",
            "1": "filled",
            "2": "partially_filled",
            "3": "partially_filled_canceled",
            "4": "live",
            "5": "nofill",
            "6": "canceled",
            "7": "canceled",
            "filled": "filled",
            "partially_filled": "partially_filled",
            "partially_filled_canceled": "partially_filled_canceled",
            "live": "live",
            "nofill": "nofill",
            "canceled": "canceled"
        }
        state = normalized.get("state")
        if state in state_map:
            normalized["state"] = state_map[state]
        
        return normalized

    def _on_response(self, msg: dict[str, Any]) -> None:
        data = msg.get("data") or []
        items: list[dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize_rest(entry)
            if normalized:
                items.append(normalized)

        self._clear()
        if items:
            self._insert(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        # 4 live 6 cancel 1 filled
        results = msg.get("result") or []
        deletes: list[dict[str, Any]] = []
        updates: list[dict[str, Any]] = []
        inserts: list[dict[str, Any]] = []
        for item in results:
            data = item.get("data") if isinstance(item, dict) else None
            normalized = self._normalize_ws(data or {})
            if not normalized:
                continue
            key = {"ordId": normalized["ordId"]}
            if self.get(key):
                updates.append(normalized)
            else:
                inserts.append(normalized)
            state = str(normalized.get("state") or "").lower()
            if state in {"filled", "canceled", "nofill", "partially_filled_canceled"}:
                deletes.append(normalized)
        if inserts:
            self._insert(inserts)
        if updates:
            self._update(updates)
        if deletes:
            self._delete(deletes)


class Trades(DataStore):
    """成交明细。"""

    _KEYS = ["tradeId"]

    @staticmethod
    def _normalize_rest(entry: dict[str, Any]) -> dict[str, Any] | None:
        trade_id = entry.get("tradeId") or entry.get("tradeID")
        if not trade_id:
            return None
        normalized = _ensure_identifiers(dict(entry))
        normalized["tradeId"] = str(trade_id)
        return normalized

    @staticmethod
    def _normalize_ws(data: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None
        mapping = {
            "TI": "tradeId",
            "D": "direction",
            "OS": "ordId",
            "M": "memberId",
            "A": "accountId",
            "I": "instId",
            "o": "offsetFlag",
            "P": "px",
            "V": "sz",
            "TT": "tradeTime",
            "IT": "insertTime",
            "T": "turnover",
            "F": "fee",
            "f": "feeCcy",
            "CC": "clearCurrency",
            "m": "matchRole",
            "l": "lever",
            "CP": "closeProfit",
        }
        normalized: dict[str, Any] = {}
        for key, value in data.items():
            target = mapping.get(key)
            if target:
                normalized[target] = value
            else:
                normalized[key] = value
        normalized = _ensure_identifiers(normalized)
        if "tradeId" not in normalized and "TI" in data:
            normalized["tradeId"] = str(data["TI"])
        if not normalized.get("tradeId"):
            return None
        return normalized

    def _on_response(self, msg: dict[str, Any]) -> None:
        data = msg.get("data") or []
        items: list[dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize_rest(entry)
            if normalized:
                items.append(normalized)

        if not items:
            return
        keys = [{"tradeId": item["tradeId"]} for item in items]
        self._delete(keys)
        self._insert(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        results = msg.get("result") or []
        items: list[dict[str, Any]] = []
        for item in results:
            data = item.get("data") if isinstance(item, dict) else None
            normalized = self._normalize_ws(data or {})
            if normalized:
                items.append(normalized)
        if not items:
            return
        keys = [{"tradeId": item["tradeId"]} for item in items]
        self._delete(keys)
        self._insert(items)


class DeepCoinDataStore(DataStoreCollection):
    """DeepCoin 合约数据存储集合"""

    def _init(self) -> None:
        self._create("detail", datastore_class=Detail)
        self._create("ticker", datastore_class=Ticker)
        self._create("book", datastore_class=Book)
        self._create("orders", datastore_class=Orders)
        self._create("position", datastore_class=Position)
        self._create("balance", datastore_class=Balance)
        self._create("trades", datastore_class=Trades)

    def _on_message(self, msg: Item, ws: ClientWebSocketResponse | None = None) -> None:
        chan = msg.get("a")
        if chan == 'PO':
            self.ticker._on_message(msg)
            self.book._on_message(msg)
            return

        action = msg.get("action")
        if action == "PushOrder":
            self.orders._on_message(msg)
        elif action == "PushAccount":
            self.balance._on_message(msg)
        elif action == "PushPosition":
            self.position._on_message(msg)
        elif action == "PushTrade":
            self.trades._on_message(msg)

    def onmessage(self, msg: Item, ws: ClientWebSocketResponse | None = None) -> None:
        self._on_message(msg, ws)

    async def initialize(self, *aws: Awaitable[aiohttp.ClientResponse]) -> None:
        for fut in asyncio.as_completed(aws):
            res = await fut
            data = await res.json()
            path = res.url.path
            if path.endswith("/market/instruments"):
                self.detail._clear()
                self.detail._on_response(data)
            elif path.endswith("/market/tickers"):
                self.ticker._on_response(data)
            elif path.endswith("/trade/v2/orders-pending"):
                self.orders._on_response(data)
            elif path.endswith("/account/positions"):
                self.position._on_response(data)
            elif path.endswith("/account/balances"):
                self.balance._on_response(data)
            elif path.endswith("/trade/fills"):
                self.trades._on_response(data)
            elif path.endswith("/trade/orders-history"):
                self.orders._on_response(data)

    @property
    def ticker(self) -> Ticker:
        """
        _key: s
        .. code :: json
           
             [{
                "s": "BTCUSDT",
                "I": "BTCUSDT",
                "U": 1757642301089,
                "PF": 1756690200,
                "E": 0.0005251816,
                "O": 114206.7,
                "H": 116346,
                "L": 114132.8,
                "V": 7688046,
                "T": 885654450.392686,
                "N": 115482.9,
                "M": 115473.7,
                "D": 115455.77,
                "V2": 19978848,
                "T2": 2288286517.724497,
                "F": 57727.9,
                "C": 173183.6,
                "BP1": 115482.8,
                "AP1": 115482.9
            }]
        """
        return self._get("ticker")
    
    @property
    def book(self) -> Book:
        """
        _key: s, S
        .. code :: json
              
            [
                {
                    "s": "BTCUSDT",
                    "S": "b",
                    "p": 115482.8,
                    "q": 0
                },
                {
                    "s": "BTCUSDT",
                    "S": "a",
                    "p": 115482.9,
                    "q": 0
                }
            ]
        
        """
        return self._get("book")

    @property
    def detail(self) -> Detail:
        """
        _key: s
        .. code :: json
           
            [
                {
                    "s": "BTCUSDT",
                    "instType": "SWAP",
                    "instId": "BTC-USDT-SWAP",
                    "uly": "",
                    "baseCcy": "BTC",
                    "quoteCcy": "USDT",
                    "ctVal": "0.001",
                    "ctValCcy": "",
                    "listTime": "0",
                    "lever": "125",
                    "tickSz": "0.1",
                    "lotSz": "1",
                    "minSz": "1",
                    "ctType": "",
                    "alias": "",
                    "state": "live",
                    "maxLmtSz": "200000",
                    "maxMktSz": "200000",
                    "tick_size": "0.1",
                    "step_size": "1"
                }
            ]
        """
        return self._get("detail")

    @property
    def orders(self) -> Orders:
        """
        当前委托订单数据。

        该数据结构用于记录当前账户下所有活跃的委托订单（如限价单、市价单等），
        包含订单的唯一标识、交易对、状态、价格、数量等关键信息。生命周期上，
        订单在下单、成交、撤单等过程中会不断更新，配合 `trades` 可追踪完整的订单执行历程。

        _key: ordId
        .. code :: json

            [
                {
                    "ordId": "1234567890",
                    "instId": "BTC-USDT-SWAP",
                    "clOrdId": "myorder001",
                    "px": "115000",
                    "sz": "0.01",
                    "ordType": "limit",
                    "side": "buy",
                    "state": "live",
                    "accFillSz": "0",
                    "insertTime": 1711111111111,
                    "updateTime": 1711111112222
                }
            ]
        主要字段:
            - ordId: 订单唯一id
            - instId: 交易对
            - px: 委托价格
            - sz: 委托数量
            - ordType: 订单类型（如限价、市价）
            - state: 当前订单状态（如live/partially_filled/filled/canceled等）
            - accFillSz: 已成交数量
            - insertTime: 下单时间
            - updateTime: 更新时间
        """
        return self._get("orders")

    @property
    def position(self) -> Position:
        """
        当前持仓数据。

        记录账户在各交易对上的持仓情况，包括方向、多空、持仓量、均价、杠杆等。
        持仓数据在开仓、平仓、爆仓等事件发生时实时更新，是风险监控与盈亏计算的基础。

        _key: instId, posSide
        .. code :: json

            [
                {
                    "instType": "SWAP",
                    "mgnMode": "cross",
                    "instId": "DOT-USDT-SWAP",
                    "posId": "1001113501647163",
                    "posSide": "long",
                    "pos": "5",
                    "avgPx": "2.624",
                    "lever": "20",
                    "liqPx": "0.001",
                    "useMargin": "0.0656",
                    "unrealizedProfit": "0.001000000000000112",
                    "mrgPosition": "merge",
                    "ccy": "USDT",
                    "uTime": "1762350896000",
                    "cTime": "1762350896000"
                }
            ]
        """
        return self._get("position")

    @property
    def balance(self) -> Balance:
        """
        账户余额数据。

        反映账户在各币种上的余额、可用余额、冻结余额等资金情况，是资金划转与风险控制的重要依据。
        余额数据在充值、提现、成交、资金划转等环节实时变动。

        _key: ccy
        .. code :: json

            [
                {
                    "ccy": "USDT",
                    "bal": "1000.0",
                    "availBal": "800.0",
                    "frozenBal": "200.0",
                    "withdrawable": "750.0"
                }
            ]
        主要字段:
            - ccy: 币种
            - bal: 总余额
            - availBal: 可用余额
            - frozenBal: 冻结余额
            - withdrawable: 可提余额
        """
        return self._get("balance")

    @property
    def trades(self) -> Trades:
        """
        成交明细数据。

        记录账户所有历史成交（包括主动成交与被动成交），用于统计订单执行情况、盈亏分析和对账。
        每条成交数据包含唯一成交id、订单id、成交方向、成交数量、成交价格、手续费等。

        _key: tradeId
        .. code :: json

            [
                {
                    "tradeId": "9876543210",
                    "ordId": "1234567890",
                    "instId": "BTCUSDT",
                    "direction": "buy",
                    "sz": "0.01",
                    "px": "115100",
                    "fee": "-0.02",
                    "feeCcy": "USDT",
                    "tradeTime": 1711111114444
                }
            ]
        主要字段:
            - tradeId: 成交唯一id
            - ordId: 所属订单id
            - instId: 交易对
            - direction: 买卖方向
            - sz: 成交数量
            - px: 成交价格
            - fee: 手续费
            - tradeTime: 成交时间
        """
        return self._get("trades")
