from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Awaitable

import aiohttp
from pybotters.store import DataStore, DataStoreCollection

if TYPE_CHECKING:
    from pybotters.typedefs import Item
    from pybotters.ws import ClientWebSocketResponse


class Book(DataStore):
    """CoinW 合约订单簿数据存储。

    WebSocket 频道: futures/depth

    消息示例（来源: https://www.coinw.com/api-doc/futures-trading/market/subscribe-order-book）

    .. code:: json

        {
            "biz": "futures",
            "pairCode": "BTC",
            "type": "depth",
            "data": {
                "asks": [{"p": "95640.3", "m": "0.807"}, ...],
                "bids": [{"p": "95640.2", "m": "0.068"}, ...]
            }
        }
    """

    _KEYS = ["s", "S", "p", "q"]

    def _init(self) -> None:
        self.limit: int | None = None
        self._last_update: float = 0.0

    def _on_message(self, msg: dict[str, Any]) -> None:
        data = msg.get("data")
        if not isinstance(data, dict):
            return

        asks = data.get("asks") or []
        bids = data.get("bids") or []
        if not asks and not bids:
            return

        symbol = (
            msg.get("pairCode")
            or data.get("pairCode")
            or msg.get("symbol")
            or data.get("symbol")
        )
        if not symbol:
            return

        if self.limit is not None:
            asks = asks[: self.limit]
            bids = bids[: self.limit]

        entries: list[dict[str, Any]] = []
        for side, levels in (("a", asks), ("b", bids)):
            for level in levels:
                price = level.get("p") or level.get("price")
                size = level.get("m") or level.get("q") or level.get("size")
                if price is None or size is None:
                    continue
                entries.append(
                    {
                        "s": str(symbol),
                        "S": side,
                        "p": str(price),
                        "q": str(size),
                    }
                )

        if not entries:
            return

        self._find_and_delete({"s": str(symbol)})
        self._insert(entries)
        self._last_update = time.time()

    def sorted(
        self, query: Item | None = None, limit: int | None = None
    ) -> dict[str, list[Item]]:
        return self._sorted(
            item_key="S",
            item_asc_key="a",
            item_desc_key="b",
            sort_key="p",
            query=query,
            limit=limit,
        )

    @property
    def last_update(self) -> float:
        return self._last_update


class Detail(DataStore):
    """CoinW 合约信息数据存储。

    文档: https://www.coinw.com/api-doc/futures-trading/market/get-instrument-information
    """

    _KEYS = ["name"]

    @staticmethod
    def _transform(entry: dict[str, Any]) -> dict[str, Any] | None:
        if not entry:
            return None
        transformed = dict(entry)
        base = entry.get("name") or entry.get("base")
        quote = entry.get("quote")
        pricePrecision = entry.get("pricePrecision")
        transformed['tick_size'] = 10 ** (-int(pricePrecision))
        transformed['step_size'] = entry.get("oneLotSize")
        if base and quote:
            transformed.setdefault(
                "symbol", f"{str(base).upper()}_{str(quote).upper()}"
            )
        return transformed

    def _onresponse(self, data: Any) -> None:
        if data is None:
            self._clear()
            return

        entries: list[dict[str, Any]]
        if isinstance(data, dict):
            entries = data.get("data") or []
        else:
            entries = data

        items: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            transformed = self._transform(entry)
            if transformed:
                items.append(transformed)

        self._clear()
        if items:
            self._insert(items)


class Ticker(DataStore):
    """CoinW 24h 交易摘要数据存储。

    文档: https://www.coinw.com/api-doc/futures-trading/market/get-last-trade-summary-of-all-instruments
    """

    _KEYS = ["name"]

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        instrument = entry.get("instrument") or entry.get("symbol") or entry.get("pairCode")
        if not instrument:
            return None
        normalized = dict(entry)
        normalized["instrument"] = str(instrument).upper()
        return normalized

    def _onresponse(self, data: Any) -> None:
        if isinstance(data, dict):
            entries = data.get("data") or []
        else:
            entries = data

        self._update(entries)

    def _on_message(self, msg: dict[str, Any]) -> None:
        data = msg.get("data")
        entries: list[dict[str, Any]] = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = data.get("data") or data.get("tickers") or []

        items: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize(entry)
            if normalized:
                items.append(normalized)

        if not items:
            return

        instruments = [{"instrument": item["instrument"]} for item in items]
        self._delete(instruments)
        self._insert(items)


class Orders(DataStore):
    """CoinW 当前订单数据存储。"""

    _KEYS = ["id"]

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        order_id = entry.get("id")
        if order_id is None:
            return None
        normalized = dict(entry)
        normalized["id"] = str(order_id)
        return normalized

    def _onresponse(self, data: Any) -> None:
        payload = []
        if isinstance(data, dict):
            inner = data.get("data")
            if isinstance(inner, dict):
                payload = inner.get("rows") or []
            elif isinstance(inner, list):
                payload = inner
        elif isinstance(data, list):
            payload = data

        items: list[dict[str, Any]] = []
        for entry in payload or []:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize(entry)
            if normalized:
                items.append(normalized)

        self._clear()
        if items:
            self._insert(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        data = msg.get("data")
        if isinstance(data, dict) and data.get("result") is not None:
            return

        entries: list[dict[str, Any]] = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = data.get("rows") or data.get("data") or []

        if not entries:
            return

        to_insert: list[dict[str, Any]] = []
        to_delete: list[dict[str, Any]] = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize(entry)
            if not normalized:
                continue

            status = str(normalized.get("status") or "").lower()
            order_status = str(normalized.get("orderStatus") or "").lower()
            remove = status in {"close", "cancel", "canceled"} or order_status in {
                "finish",
                "cancel",
            }

            # query = {"id": normalized["id"]}
            to_delete.append(normalized)
            if not remove:
                to_insert.append(normalized)

        if to_delete:
            self._delete(to_delete)
        if to_insert:
            self._insert(to_insert)


class Position(DataStore):
    """CoinW 当前持仓数据存储。"""

    _KEYS = ["openId"]


    def _onresponse(self, data: Any) -> None:
        payload = []
        if isinstance(data, dict):
            payload = data.get("data") or []
        elif isinstance(data, list):
            payload = data

        items: list[dict[str, Any]] = []
        for entry in payload or []:
            if not isinstance(entry, dict):
                continue
            entry['openId'] = str(entry.get("id"))
            items.append(entry)

        self._clear()
        if items:
            self._insert(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        data = msg.get("data")

        if isinstance(data, dict) and data.get("result") is not None:
            return

        entries: list[dict[str, Any]] = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = data.get("rows") or data.get("data") or []

        if not entries:
            return

        to_insert: list[dict[str, Any]] = []
        to_update: list[dict[str, Any]] = []
        to_delete: list[dict[str, Any]] = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            normalized = entry


            if normalized.get("status") == 'close':
                to_delete.append(normalized)
                continue

            if self.find(normalized):
                to_update.append(normalized)
            else:
                to_insert.append(normalized)

        if to_delete:
            self._delete(to_delete)
        if to_update:
            self._update(to_update)
        if to_insert:
            self._insert(to_insert)


class Balance(DataStore):
    """CoinW 合约账户资产数据存储。"""

    _KEYS = ["currency"]

    @staticmethod
    def _normalize_rest(entry: dict[str, Any]) -> dict[str, Any]:
        currency = "USDT"
        normalized = {
            "currency": currency,
            "availableMargin": entry.get("availableMargin"),
            "availableUsdt": entry.get("availableUsdt"),
            "almightyGold": entry.get("almightyGold"),
            "alMargin": entry.get("alMargin"),
            "alFreeze": entry.get("alFreeze"),
            "time": entry.get("time"),
            "userId": entry.get("userId"),
        }
        if "available" not in normalized:
            normalized["available"] = entry.get("availableUsdt")
        normalized["availableMargin"] = entry.get("availableMargin")
        normalized["margin"] = entry.get("alMargin")
        normalized["freeze"] = entry.get("alFreeze")
        return {k: v for k, v in normalized.items() if v is not None}

    @staticmethod
    def _normalize_ws(entry: dict[str, Any]) -> dict[str, Any] | None:
        currency = entry.get("currency")
        if not currency:
            return None
        currency_str = str(currency).upper()
        normalized = dict(entry)
        normalized["currency"] = currency_str
        # 对齐 REST 字段
        if "availableUsdt" not in normalized and "available" in normalized:
            normalized["availableUsdt"] = normalized["available"]
        if "alMargin" not in normalized and "margin" in normalized:
            normalized["alMargin"] = normalized["margin"]
        if "alFreeze" not in normalized and "freeze" in normalized:
            normalized["alFreeze"] = normalized["freeze"]
        return normalized

    def _onresponse(self, data: Any) -> None:
        entry = None
        if isinstance(data, dict):
            entry = data.get("data")
        if not isinstance(entry, dict):
            entry = {}

        self._clear()
        normalized = self._normalize_rest(entry)
        self._insert([normalized])

    def _on_message(self, msg: dict[str, Any]) -> None:
        data = msg.get("data")
        if isinstance(data, dict) and data.get("result") is not None:
            return

        entries: list[dict[str, Any]] = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = data.get("rows") or data.get("data") or []

        if not entries:
            return

        normalized_items: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize_ws(entry)
            if normalized:
                normalized_items.append(normalized)

        if not normalized_items:
            return

        currencies = [{"currency": item["currency"]} for item in normalized_items]
        self._delete(currencies)
        self._insert(normalized_items)


class CoinwFuturesDataStore(DataStoreCollection):
    """CoinW 合约交易 DataStoreCollection。

    - REST: https://api.coinw.com/v1/perpum/instruments
    - WebSocket: wss://ws.futurescw.com/perpum (depth)
    """

    def _init(self) -> None:
        self._create("book", datastore_class=Book)
        self._create("detail", datastore_class=Detail)
        self._create("ticker", datastore_class=Ticker)
        self._create("orders", datastore_class=Orders)
        self._create("position", datastore_class=Position)
        self._create("balance", datastore_class=Balance)

    def onmessage(self, msg: Item, ws: ClientWebSocketResponse | None = None) -> None:
        msg_type = msg.get("type")
        # print(msg)
        if msg_type == "depth":
            self.book._on_message(msg)
        elif msg_type == "order":
            self.orders._on_message(msg)
        elif msg_type == "position" or msg_type == "position_change":
            self.position._on_message(msg)
        elif msg_type == "assets":
            self.balance._on_message(msg)
        elif msg_type == "ticker":
            self.ticker._on_message(msg)

    async def initialize(self, *aws: Awaitable[aiohttp.ClientResponse]) -> None:
        for fut in asyncio.as_completed(aws):
            res = await fut
            data = await res.json()
            if res.url.path == "/v1/perpum/instruments":
                self.detail._onresponse(data)
            elif res.url.path == "/v1/perpumPublic/tickers":
                self.ticker._onresponse(data)
            elif res.url.path == "/v1/perpum/orders/open":
                self.orders._onresponse(data)
            elif res.url.path == "/v1/perpum/positions/all":
                self.position._onresponse(data)
            elif res.url.path == "/v1/perpum/account/getUserAssets":
                self.balance._onresponse(data)

    @property
    def book(self) -> Book:
        """订单簿深度数据流。

        数据来源：
          - WebSocket: ``type == "depth"`` （参考 https://www.coinw.com/api-doc/futures-trading/market/subscribe-order-book）

        数据结构（节选）::

            {
                "s": "BTC",
                "S": "a",  # 卖单
                "p": "95640.3",
                "q": "0.807"
            }
        """

        return self._get("book", Book)

    @property
    def detail(self) -> Detail:
        """合约基础信息数据流。

        响应示例（节选）:

        .. code:: json

        {
            "base": "btc",
            "closeSpread": 0.0002,
            "commissionRate": 0.0006,
            "configBo": {
                "margins": {
                    "100": 0.075,
                    "5": 0.00375,
                    "50": 0.0375,
                    "20": 0.015,
                    "10": 0.0075
                },
                "simulatedMargins": {
                    "5": 0.00375,
                    "20": 0.015,
                    "10": 0.0075
                }
            },
            "createdDate": 1548950400000,
            "defaultLeverage": 20,
            "defaultStopLossRate": 0.99,
            "defaultStopProfitRate": 100,
            "depthPrecision": "0.1,1,10,50,100",
            "iconUrl": "https://hkto-prod.oss-accelerate.aliyuncs.com/4dfca512e957e14f05da07751a96061cf4bfd5df438504f65287fa0a8c3cadb6.svg",
            "id": 1,
            "indexId": 1,
            "leverage": [
                5,
                10,
                20,
                50,
                100,
                125,
                200
            ],
            "makerFee": "0.0001",
            "maxLeverage": 200,
            "maxPosition": 20000,
            "minLeverage": 1,
            "minSize": 1,
            "name": "BTC",
            "oneLotMargin": 1,
            "oneLotSize": 0.001,
            "oneMaxPosition": 15000,
            "openSpread": 0.0003,
            "orderLimitMaxRate": 0.05,
            "orderLimitMinRate": 0.05,
            "orderMarketLimitAmount": 10,
            "orderPlanLimitAmount": 30,
            "partitionIds": "2013,2011",
            "platform": 0,
            "pricePrecision": 1,
            "quote": "usdt",
            "selected": 0,
            "settledAt": 1761062400000,
            "settledPeriod": 8,
            "settlementRate": 0.0004,
            "sort": 1,
            "status": "online",
            "stopCrossPositionRate": 0.1,
            "stopSurplusRate": 0.01,
            "takerFee": "0.0006",
            "updatedDate": 1752040118000,
            "symbol": "BTC_USDT",
            "tick_size": 1.0,
            "step_size": 0.001
        }
        """

        return self._get("detail", Detail)

    @property
    def ticker(self) -> Ticker:
        """24小时交易摘要数据流。
        
        .. code:: json

            {
                'fair_price': 97072.4,
                'max_leverage': 125,
                'total_volume': 0.003,
                'price_coin': 'btc',
                'contract_id': 1,
                'base_coin': 'btc',
                'high': 98001.5,
                'rise_fall_rate': 0.012275,
                'low': 95371.4,
                'name': 'BTCUSDT',
                'contract_size': 0.001,
                'quote_coin': 'usdt',
                'last_price': 97072.4
            }
        
        """
        return self._get("ticker", Ticker)

    @property
    def orders(self) -> Orders:
        """当前订单数据流。

        数据来源：
          - REST: ``GET /v1/perpum/orders/open``
          - WebSocket: ``type == "order"``

        数据结构（节选）::

            {
                "currentPiece": "1",
                "leverage": "50",
                "originalType": "plan",
                "processStatus": 0,
                "contractType": 1,
                "frozenFee": "0",
                "openPrice": "175",
                "orderStatus": "unFinish",
                "instrument": "SOL",
                "quantityUnit": 1,
                "source": "web",
                "updatedDate": 1761109078404,
                "positionModel": 1,
                "posType": "plan",
                "baseSize": "0.1",
                "quote": "usdt",
                "liquidateBy": "manual",
                "makerFee": "0.0001",
                "totalPiece": "1",
                "tradePiece": "0",
                "orderPrice": "175",
                "id": "33309055657317395",
                "direction": "long",
                "margin": "0.35",
                "indexPrice": "185.68",
                "quantity": "1",
                "takerFee": "0.0006",
                "userId": "1757458",
                "cancelPiece": "0",
                "createdDate": 1761109078404,
                "positionMargin": "0.35",
                "base": "sol",
                "status": "open"
            }
        """

        return self._get("orders", Orders)

    @property
    def position(self) -> Position:
        """当前持仓数据流。

        数据来源：
          - REST: ``GET /v1/perpum/positions``
          - WebSocket: ``type == "position"``

        .. code:: json

            {
                "currentPiece": "0",
                "isProfession": 0,
                "leverage": "10",
                "originalType": "execute",
                "orderId": "33309059291614824",
                "contractType": 1,
                "openId": "2435521222638707873",
                "fee": "0.00020724",
                "openPrice": "0.3456",
                "orderStatus": "finish",
                "instrument": "JUP",
                "quantityUnit": 1,
                "source": "api",
                "updatedDate": 1761192795412,
                "positionModel": 1,
                "feeRate": "0.0006",
                "netProfit": "-0.00040724",
                "baseSize": "1",
                "quote": "usdt",
                "liquidateBy": "manual",
                "totalPiece": "1",
                "orderPrice": "0",
                "id": "23469279597150213",
                "fundingSettle": "0",
                "direction": "long",
                "margin": "0.03435264",
                "takerMaker": 1,
                "indexPrice": "0.3455",
                "quantity": "0.03456",
                "userId": "1757458",
                "closedPiece": "1",
                "createdDate": 1761192793000,
                "hedgeId": "23469279597150214",
                "closePrice": "0.3454",
                "positionMargin": "0.03435264",
                "base": "jup",
                "realPrice": "0.3454",
                "status": "close"
                }
        """

        return self._get("position", Position)

    @property
    def balance(self) -> Balance:
        """合约账户资产数据流。

        数据来源：
          - REST: ``GET /v1/perpum/account/getUserAssets``
          - WebSocket: ``type == "assets"``

        .. code:: json

            {
                "currency": "USDT",
                "availableMargin": 0.0,
                "availableUsdt": 0,
                "almightyGold": 0.0,
                "alMargin": 0,
                "alFreeze": 0,
                "time": 1761055905797,
                "userId": 1757458,
                "available": 0,
                "margin": 0,
                "freeze": 0
            }
        """

        return self._get("balance", Balance)
