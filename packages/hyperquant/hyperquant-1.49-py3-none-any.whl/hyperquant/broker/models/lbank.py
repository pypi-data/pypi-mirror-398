from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, TYPE_CHECKING

from aiohttp import ClientResponse
from pybotters.store import DataStore, DataStoreCollection

if TYPE_CHECKING:
    from pybotters.typedefs import Item
    from pybotters.ws import ClientWebSocketResponse

logger = logging.getLogger(__name__)


def _accuracy_to_step(accuracy: int | str | None) -> str:
    try:
        n = int(accuracy) if accuracy is not None else 0
    except (TypeError, ValueError):  # pragma: no cover - defensive guard
        n = 0
    if n <= 0:
        return "1"
    return "0." + "0" * (n - 1) + "1"


class Book(DataStore):
    """LBank order book store parsed from the depth channel."""

    _KEYS = ["id", "S", "p"]

    def _init(self) -> None:
        self.limit: int | None = None
        self.symbol_map: dict[str, str] = {}




    def _on_message(self, msg: Any) -> None:
        
        data = json.loads(msg)
        
        if not data:
            return

        channel_id = None
        if data.get("y") is not None:
            channel_id = str(data["y"])

        symbol = None
        if channel_id:
            symbol = self.symbol_map.get(channel_id)
        if symbol is None and data.get("i"):
            symbol = self.symbol_map.get(str(data["i"]))

        bids = data.get("b", [])
        asks = data.get("s", [])
        if not (bids or asks):
            return
        bids = bids[: self.limit] if self.limit else bids
        asks = asks[: self.limit] if self.limit else asks
        bids = [
            {"id": channel_id, "S": "b", "p": str(item[0]), "q": str(item[1]), "s": symbol}
            for item in bids
        ]
        asks = [
            {"id": channel_id, "S": "a", "p": str(item[0]), "q": str(item[1]), "s": symbol}
            for item in asks
        ]


        if channel_id is not None:
            self._find_and_delete({"id": channel_id})
        self._insert(bids + asks)


class Detail(DataStore):
    """Futures instrument metadata store obtained from the futures instrument endpoint."""

    _KEYS = ["symbol"]

    def _transform(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        try:
            instrument:dict = entry["instrument"]
            fee:dict = entry["fee"]
            market_data:dict = entry["marketData"]
        except (KeyError, TypeError):
            return None
        return {
            "symbol": instrument.get("instrumentID"),
            "instrument_name": instrument.get("instrumentName"),
            "base_currency": instrument.get("baseCurrency"),
            "price_currency": instrument.get("priceCurrency"),
            "min_order_volume": instrument.get("minOrderVolume"),
            "max_order_volume": instrument.get("maxOrderVolume"),
            "tick_size": instrument.get("priceTick"),
            "step_size": instrument.get("volumeTick"),
            "maker_fee": fee.get("makerOpenFeeRate"),
            "taker_fee": fee.get("takerOpenFeeRate"),
            "last_price": market_data.get("lastPrice"),
            "amount24": market_data.get("turnover24"),
        }

    def _onresponse(self, data: list[dict[str, Any]] | dict[str, Any] | None) -> None:
        if not data:
            self._clear()
            return
        entries = data
        if isinstance(data, dict):  # pragma: no cover - defensive guard
            entries = data.get("data") or []
        items: list[dict[str, Any]] = []
        for entry in entries or []:
            transformed = self._transform(entry)
            if transformed:
                items.append(transformed)
        if not items:
            self._clear()
            return
        self._clear()
        self._insert(items)


class Orders(DataStore):
    """Active order snapshots fetched via the REST order query."""

    _KEYS = ["order_id"]

    _ORDER_STATUS_MAP = {
        "1": "filled",
        "2": "filled",
        "4": "open",
        "5": "partially_filled",
        "6": "canceled",
    }

    _DIRECTION_MAP = {
        "0": "buy",
        "1": "sell",
    }

    _OFFSET_FLAG_MAP = {
        "0": "open",
        "1": "close",
    }

    def _transform(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        if not entry:
            return None

        order_id = entry.get("OrderSysID") or entry.get("orderSysID")
        if not order_id:
            return None

        direction = self._DIRECTION_MAP.get(str(entry.get("Direction")), str(entry.get("Direction")))
        offset_flag = self._OFFSET_FLAG_MAP.get(
            str(entry.get("OffsetFlag")), str(entry.get("OffsetFlag"))
        )

        order_price_type = str(entry.get("OrderPriceType")) if entry.get("OrderPriceType") is not None else None
        order_type = str(entry.get("OrderType")) if entry.get("OrderType") is not None else None

        if order_price_type == "4":
            order_kind = "market"
        elif order_type == "1":
            order_kind = "limit_fak"
        else:
            order_kind = "limit"

        status_code = str(entry.get("OrderStatus")) if entry.get("OrderStatus") is not None else None
        status = self._ORDER_STATUS_MAP.get(status_code, status_code)

        client_order_id = (
            entry.get("LocalID")
            or entry.get("localID")
            or entry.get("LocalId")
            or entry.get("localId")
        )

        return {
            "order_id": order_id,
            "client_order_id": client_order_id,
            "symbol": entry.get("InstrumentID"),
            "side": direction,
            "offset": offset_flag,
            "order_type": order_kind,
            "price": entry.get('TradePrice') or entry.get("Price"),
            "order_price": entry.get("OrderPrice") or entry.get('Price'),
            "quantity": entry.get("Volume"),
            "filled": entry.get("VolumeTraded"),
            "remaining": entry.get("VolumeRemain"),
            "status": status,
            "status_code": status_code,
            "position_id": entry.get("PositionID"),
            "leverage": entry.get("Leverage"),
            "frozen_margin": entry.get("FrozenMargin"),
            "frozen_fee": entry.get("FrozenFee"),
            "insert_time": entry.get("InsertTime"),
            "update_time": entry.get("UpdateTime"),
        }

    @staticmethod
    def _extract_rows(data: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not data:
            return []
        payload = data.get("data") if isinstance(data, dict) else None
        if isinstance(payload, dict):
            rows = payload.get("data")
            if isinstance(rows, list):
                return rows
        if isinstance(payload, list):  # pragma: no cover - defensive path
            return payload
        return []

    def _onresponse(self, data: dict[str, Any] | None) -> None:
        rows = self._extract_rows(data)
        if not rows:
            self._clear()
            return

        items: list[dict[str, Any]] = []
        for row in rows:
            transformed = self._transform(row)
            if transformed:
                items.append(transformed)

        self._clear()
        if items:
            self._insert(items)


class OrderFinish(Orders):
    """Finished order snapshots fetched from the historical REST endpoint."""

    def _onresponse(self, data: dict[str, Any] | None) -> None:
        rows: list[dict[str, Any]] = []
        if isinstance(data, dict):
            payload = data.get("data") or {}
            if isinstance(payload, dict):
                list_payload = payload.get("list") or {}
                if isinstance(list_payload, dict):
                    rows = list_payload.get("resultList") or []

        if not rows:
            self._clear()
            return

        items: list[dict[str, Any]] = []
        for row in rows:
            transformed = self._transform(row)
            if transformed:
                items.append(transformed)

        self._clear()
        if items:
            self._insert(items)


class Position(DataStore):
    """Open position snapshots fetched from the REST position endpoint."""

    _KEYS = ["position_id"]

    _POS_DIRECTION_MAP = {
        "1": "net",
        "2": "long",
        "3": "short",
    }

    def _transform(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        if not entry:
            return None
        position_id = entry.get("PositionID")
        bus_id = entry.get("BusinessNo")
        if not position_id:
            return None
        
        q = float(entry.get("Position", 0))
        side = "net"
        if q > 0:
            side = "long"
        elif q < 0:
            side = "short"
        
        return {
            "position_id": position_id,
            "bus_id": bus_id,
            "symbol": entry.get("InstrumentID"),
            "side": side,
            "quantity": entry.get("Position"),
            "available": entry.get("AvailableUse"),
            "avg_price": entry.get("OpenPrice"),
            "entry_price": entry.get("OpenPrice"),
            "leverage": entry.get("Leverage"),
            "liquidation_price": entry.get("estimateLiquidationPrice") or entry.get("FORCECLOSEPRICE"),
            "margin_used": entry.get("UseMargin"),
            "unrealized_pnl": entry.get("PositionFee"),
            "realized_pnl": entry.get("CloseProfit"),
            "update_time": entry.get("UpdateTime"),
            "insert_time": entry.get("InsertTime"),
            "begin_time": entry.get("BeginTime")
        }

    def _onresponse(self, data: dict[str, Any] | None) -> None:
        rows = Orders._extract_rows(data)  # reuse helper for nested payload
        if not rows:
            self._clear()
            return

        items: list[dict[str, Any]] = []
        for row in rows:
            transformed = self._transform(row)
            if transformed:
                items.append(transformed)

        self._clear()
        if items:
            self._insert(items)


class Balance(DataStore):
    """Account balance snapshot derived from sendQryAll endpoint."""

    _KEYS = ["asset"]

    def _init(self) -> None:
        self._asset: str | None = None

    def set_asset(self, asset: str | None) -> None:
        self._asset = asset

    def _transform(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not payload:
            return None
        asset_balance = payload.get("assetBalance") or {}
        if not asset_balance:
            return None

        asset = payload.get("asset") or asset_balance.get("currency") or self._asset or "USDT"

        return {
            "asset": asset,
            "balance": asset_balance.get("balance"),
            "available": asset_balance.get("available"),
            "real_available": asset_balance.get("realAvailable"),
            "frozen_margin": asset_balance.get("frozenMargin"),
            "frozen_fee": asset_balance.get("frozenFee"),
            "total_close_profit": asset_balance.get("totalCloseProfit"),
            "cross_margin": asset_balance.get("crossMargin"),
        }

    def _onresponse(self, data: dict[str, Any] | None) -> None:
        payload: dict[str, Any] = {}
        if isinstance(data, dict):
            payload = data.get("data") or {}

        item = self._transform(payload)
        self._clear()
        if item:
            self._insert([item])


class LbankDataStore(DataStoreCollection):
    """Aggregates book/detail stores for the LBank public feed."""

    def _init(self) -> None:
        self._create("book", datastore_class=Book)
        self._create("detail", datastore_class=Detail)
        self._create("orders", datastore_class=Orders)
        self._create("order_finish", datastore_class=OrderFinish)
        self._create("position", datastore_class=Position)
        self._create("balance", datastore_class=Balance)
        self._channel_to_symbol: dict[str, str] = {}

    @property
    def book(self) -> Book:
        """
        订单簿（Order Book）数据流，按订阅ID（channel_id）索引。

        此属性表示通过深度频道（depth channel）接收到的订单簿快照和增量更新，数据结构示例如下：

        Data structure:
            [
                {
                    "id": <channel_id>,
                    "S": "b" 或 "a",  # "b" 表示买单，"a" 表示卖单
                    "p": <价格>,
                    "q": <数量>,
                    "s": <标准化交易对符号>
                },
                ...
            ]

        通过本属性可以获取当前 LBank 订单簿的最新状态，便于后续行情分析和撮合逻辑处理。
        """
        return self._get("book")

    @property
    def detail(self) -> Detail:
        """

        _KEYS = ["symbol"]

        期货合约详情元数据流。

        此属性表示通过期货合约接口获取的合约详情，包括合约ID、合约名称、基础币种、计价币种、最小/最大下单量、价格跳动、交易量跳动、maker/taker手续费率、最新价和24小时成交额等信息。

        Data structure:
            [
                {
                    "symbol": "BTCUSDT",               # 合约ID
                    "instrument_name": "BTCUSDT",      # 合约名称
                    "base_currency": "BTC",            # 基础币种
                    "price_currency": "USDT",          # 计价币种
                    "min_order_volume": "0.0001",        # 最小下单量
                    "max_order_volume": "600.0",         # 最大下单量
                    "tick_size": "0.1",                  # 最小价格变动单位
                    "step_size": "0.0001",               # 最小数量变动单位
                    "maker_fee": "0.0002",               # Maker 手续费率
                    "taker_fee": "0.0006",               # Taker 手续费率
                    "last_price": "117025.5",            # 最新价
                    "amount24": "807363493.97579747"     # 24小时成交额
                },
                ...
            ]

        通过本属性可以获取所有支持的期货合约元数据，便于下单参数校验和行情展示。
        """
        return self._get("detail")

    @property
    def orders(self) -> Orders:
        """
        活跃订单数据流。

        此属性表示通过 REST 接口获取的当前活跃订单快照，包括已开仓订单、部分成交订单等状态。

        Data structure:
            [
                {
                    "order_id": <系统订单ID>,
                    "client_order_id": <用户自定义订单ID>,
                    "symbol": <合约ID>,
                    "side": "buy" 或 "sell",
                    "offset": "open" 或 "close",
                    "order_type": "limit" / "market" / "limit_fak",
                    "price": <下单价格>,
                    "quantity": <下单数量>,
                    "filled": <已成交数量>,
                    "remaining": <剩余数量>,
                    "status": <订单状态>,
                    "status_code": <原始状态码>,
                    "position_id": <关联仓位ID>,
                    "leverage": <杠杆倍数>,
                    "frozen_margin": <冻结保证金>,
                    "frozen_fee": <冻结手续费>,
                    "insert_time": <下单时间>,
                    "update_time": <更新时间>
                },
                ...
            ]

        通过本属性可以跟踪当前活跃订单状态，便于订单管理和风控。
        """
        return self._get("orders")

    @property
    def order_finish(self) -> OrderFinish:
        """历史已完成订单数据流，与 ``orders`` 字段保持兼容。"""
        return self._get("order_finish")

    @property
    def position(self) -> Position:
        """
        持仓数据流。

        此属性表示通过 REST 接口获取的当前持仓快照，包括多头、空头或净持仓等方向信息。

        Data structure:
            [
                {
                    "position_id": <仓位ID>,
                    "bus_id": <订单ID覆盖>,
                    "symbol": <合约ID>,
                    "side": "long" / "short" / "net",
                    "quantity": <持仓数量>,
                    "available": <可用数量>,
                    "avg_price": <持仓均价>,
                    "entry_price": <开仓均价>,
                    "leverage": <杠杆倍数>,
                    "liquidation_price": <预估强平价>,
                    "margin_used": <已用保证金>,
                    "unrealized_pnl": <未实现盈亏>,
                    "realized_pnl": <已实现盈亏>,
                    "update_time": <更新时间>,
                    "insert_time": <插入时间>,
                    "begin_time": <持仓开始时间>
                },
                ...
            ]

        通过本属性可以跟踪账户当前仓位状态，便于盈亏分析和风控。
        """
        return self._get("position")

    @property
    def balance(self) -> Balance:
        """
        账户余额数据流。

        此属性表示通过 REST 接口获取的账户资产快照，包括余额、可用余额、保证金等信息。

        Data structure:
            [
                {
                    "asset": <资产币种>,
                    "balance": <总余额>,
                    "available": <可用余额>,
                    "real_available": <实际可用余额>,
                    "frozen_margin": <冻结保证金>,
                    "frozen_fee": <冻结手续费>,
                    "total_close_profit": <累计平仓收益>,
                    "cross_margin": <全仓保证金>
                }
            ]

        通过本属性可以跟踪账户余额与资金情况，便于资金管理和风险控制。
        """
        return self._get("balance")


    def register_book_channel(self, channel_id: str, symbol: str, *, raw_symbol: str | None = None) -> None:
        if channel_id is not None:
            self.book.symbol_map[str(channel_id)] = symbol
        if raw_symbol:
            self.book.symbol_map[str(raw_symbol)] = symbol


    async def initialize(self, *aws: Awaitable[ClientResponse]) -> None:
        for fut in asyncio.as_completed(aws):
            res = await fut
            data = await res.json()

            if res.url.path == "/cfd/agg/v1/instrument":
                self.detail._onresponse(data)
            if res.url.path == "/cfd/query/v1.0/Order":
                self.orders._onresponse(data)
            if res.url.path == "/cfd/query/v1.0/Position":
                self.position._onresponse(data)
            if res.url.path == "/cfd/agg/v1/sendQryAll":
                self.balance._onresponse(data)
            if res.url.path == "/cfd/cff/v1/FinishOrder":
                self.order_finish._onresponse(data)


    def onmessage(self, msg: Item, ws: ClientWebSocketResponse | None = None) -> None:
        self.book._on_message(msg)
