from __future__ import annotations

import asyncio
import itertools
import logging
import time
from typing import Any, Iterable, Literal

import pybotters

from .models.lbank import LbankDataStore
from .lib.util import fmt_value

logger = logging.getLogger(__name__)

# https://ccapi.rerrkvifj.com 似乎是spot的api
# https://uuapi.rerrkvifj.com 似乎是合约的api


class Lbank:
    """LBank public market-data client (REST + WS)."""

    def __init__(
        self,
        client: pybotters.Client,
        *,
        front_api: str | None = None,
        rest_api: str | None = None,
        ws_url: str | None = None,
    ) -> None:
        self.client = client
        self.store = LbankDataStore()
        self.front_api = front_api or "https://uuapi.rerrkvifj.com"
        self.rest_api = rest_api or "https://api.lbkex.com"
        self.ws_url = ws_url or "wss://uuws.rerrkvifj.com/ws/v3"
        self._req_id = itertools.count(int(time.time() * 1000))
        self._ws_app = None
        self._rest_headers = {"source": "4", "versionflage": "true"}

    async def __aenter__(self) -> "Lbank":
        await self.update("detail")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    async def update(
        self,
        update_type: Literal["detail", "balance", "position", "orders", "orders_finish", "all"] = "all",
        *,
        product_group: str = "SwapU",
        exchange_id: str = "Exchange",
        asset: str = "USDT",
        instrument_id: str | None = None,
        page_index: int = 1,
        page_size: int = 1000,
    ) -> None:
        """Refresh local caches via REST endpoints.

        Parameters mirror the documented REST API default arguments.
        """

        requests: list[Any] = []

        include_detail = update_type in {"detail", "all"}
        include_orders = update_type in {"orders", "all"}
        include_position = update_type in {"position", "all"}
        include_balance = update_type in {"balance", "all"}

        if update_type == "orders_finish":
            await self.update_finish_order(
                product_group=product_group,
                page_index=page_index,
                page_size=page_size,
            )
            return

        if include_detail:
            requests.append(
                self.client.post(
                    f"{self.front_api}/cfd/agg/v1/instrument",
                    json={"ProductGroup": product_group},
                    headers=self._rest_headers,
                )
            )

        if include_orders:
            requests.append(
                self.client.get(
                    f"{self.front_api}/cfd/query/v1.0/Order",
                    params={
                        "ProductGroup": product_group,
                        "ExchangeID": exchange_id,
                        "pageIndex": page_index,
                        "pageSize": page_size,
                    },
                    headers=self._rest_headers,
                )
            )
        
        if include_position:
            requests.append(
                self.client.get(
                    f"{self.front_api}/cfd/query/v1.0/Position",
                    params={
                        "ProductGroup": product_group,
                        "Valid": 1,
                        "pageIndex": page_index,
                        "pageSize": page_size,
                    },
                    headers=self._rest_headers,
                )
            )

        if include_balance:
            resolved_instrument = instrument_id or self._resolve_instrument()
            if not resolved_instrument:
                raise ValueError(
                    "instrument_id is required to query balance; call update('detail') first or provide instrument_id explicitly."
                )
            self.store.balance.set_asset(asset)
            requests.append(
                self.client.post(
                    f"{self.front_api}/cfd/agg/v1/sendQryAll",
                    json={
                        "productGroup": product_group,
                        "instrumentID": resolved_instrument,
                        "asset": asset,
                    },
                    headers=self._rest_headers,
                )
            )

        if not requests:
            raise ValueError(f"update_type err: {update_type}")

        await self.store.initialize(*requests)

    async def query_trade(
        self,
        order_id: str | None = None,
        *,
        product_group: str = "SwapU",
        page_index: int = 1,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Fetch trade executions linked to a given OrderSysID.

        Example response payload::

            [
                {
                    "TradeUnitID": "e1b03fb1-6849-464f-a",
                    "ProductGroup": "SwapU",
                    "CloseProfit": 0,
                    "BusinessNo": 1001770339345505,
                    "TradeID": "1000162046503720",
                    "PositionID": "1000632926272299",
                    "DeriveSource": "0",
                    "OrderID": "",
                    "Direction": "0",
                    "InstrumentID": "SOLUSDT",
                    "OffsetFlag": "0",
                    "Remark": "def",
                    "DdlnTime": "0",
                    "UseMargin": 0.054213,
                    "Currency": "USDT",
                    "Turnover": 5.4213,
                    "SettlementGroup": "SwapU",
                    "Leverage": 100,
                    "OrderSysID": "1000632948114584",
                    "ExchangeID": "Exchange",
                    "AccountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                    "TradeTime": 1760161085,
                    "Fee": 0.00325278,
                    "OrderPrice": 180.89,
                    "InsertTime": 1760161085,
                    "MemberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                    "MatchRole": "1",
                    "ClearCurrency": "USDT",
                    "Price": 180.71,
                    "Volume": 0.03,
                    "OpenPrice": 182.94,
                    "MasterAccountID": "",
                    "PriceCurrency": "USDT",
                    "FeeCurrency": "USDT"
                    }
            ]
        """

        if not order_id:
            raise ValueError("order_id is required to query order executions")

        params = {
            "ProductGroup": product_group,
            "OrderSysID": order_id,
            "pageIndex": page_index,
            "pageSize": page_size,
        }

        res = await self.client.get(
            f"{self.front_api}/cfd/query/v1.0/Trade",
            params=params,
            headers=self._rest_headers,
        )
        data = await res.json()
        payload = self._ensure_ok("query_trade", data)

        if isinstance(payload, dict):
            rows = payload.get("data")
            if isinstance(rows, list):
                return rows
        elif isinstance(payload, list):  # pragma: no cover - defensive fallback
            return payload

        return []

    async def query_order(
        self,
        order_id: str | None = None,
        *,
        product_group: str = "SwapU",
        page_index: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """
        返回值示例:

        .. code:: json

            {
                "order_id": "1000632478428573",
                "instrument_id": "SOLUSDT",
                "position_id": "1000632478428573",
                "direction": "0",
                "offset_flag": "0",
                "trade_time": 1760123456,
                "avg_price": 182.5,
                "volume": 0.03,
                "turnover": 5.475,
                "fee": 0.003285,
                "trade_count": 1
            }
        
        如果没有订单成交返回
            {
                "order_id": "1000632478428573",
                "trade_count": 0
            }
        """

        if not order_id:
            raise ValueError("order_id is required to query order statistics")

        trades = await self.query_trade(
            order_id,
            product_group=product_group,
            page_index=page_index,
            page_size=page_size,
        )

        if not trades:
            return {
                "order_id": order_id,
                "trade_count": 0,
            }

        def _to_float(value: Any) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        total_volume = sum(_to_float(trade.get("Volume")) for trade in trades)
        total_turnover = sum(_to_float(trade.get("Turnover")) for trade in trades)
        total_fee = sum(_to_float(trade.get("Fee")) for trade in trades)

        avg_price = total_turnover / total_volume if total_volume else None
        last_trade = trades[-1]

        return {
            "order_id": order_id,
            "instrument_id": last_trade.get("InstrumentID"),
            "position_id": last_trade.get("PositionID"),
            "direction": last_trade.get("Direction"),
            "offset_flag": last_trade.get("OffsetFlag"),
            "trade_time": last_trade.get("TradeTime"),
            "avg_price": avg_price,
            "volume": total_volume,
            "turnover": total_turnover,
            "fee": total_fee,
            "trade_count": len(trades),
        }

    def _resolve_instrument(self) -> str | None:
        detail_entries = self.store.detail.find()
        if detail_entries:
            return detail_entries[0].get("symbol")
        return None

    def _get_detail_entry(self, symbol: str) -> dict[str, Any]:
        detail = self.store.detail.get({"symbol": symbol})
        if not detail:
            raise ValueError(f"Unknown LBank instrument: {symbol}")
        return detail

    @staticmethod
    def _format_with_step(value: float, step: Any) -> str:
        try:
            step_float = float(step)
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            step_float = 0.0

        if step_float <= 0:
            return str(value)

        return fmt_value(value, step_float)

    async def update_finish_order(
        self,
        *,
        product_group: str = "SwapU",
        page_index: int = 1,
        page_size: int = 200,
        start_time: int | None = None,
        end_time: int | None = None,
        instrument_id: str | None = None,
    ) -> None:
        """Fetch finished orders within the specified time window (default: last hour)."""

        now_ms = int(time.time() * 1000)
        if end_time is None:
            end_time = now_ms
        if start_time is None:
            start_time = end_time - 60 * 60 * 1000
        if start_time >= end_time:
            raise ValueError("start_time must be earlier than end_time")

        params: dict[str, Any] = {
            "ProductGroup": product_group,
            "pageIndex": page_index,
            "pageSize": page_size,
            "startTime": start_time,
            "endTime": end_time,
        }
        if instrument_id:
            params["InstrumentID"] = instrument_id

        await self.store.initialize(
            self.client.get(
                f"{self.front_api}/cfd/cff/v1/FinishOrder",
                params=params,
                headers=self._rest_headers,
            )
        )

    async def place_order(
        self,
        symbol: str,
        *,
        direction: Literal["buy", "sell", "0", "1"],
        volume: float,
        price: float | None = None,
        order_type: Literal["market", "limit_ioc", "limit_gtc"] = "market",
        offset_flag: Literal["open", "close", "0", "1"] = "open",
        exchange_id: str = "Exchange",
        product_group: str = "SwapU",
        order_proportion: str = "0.0000",
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """Create an order using documented REST parameters.
        
        返回示例:

        .. code:: json

            {
                "offsetFlag": "5",
                "orderType": "1",
                "reserveMode": "0",
                "fee": "0.0066042",
                "frozenFee": "0",
                "ddlnTime": "0",
                "userID": "lbank_exchange_user",
                "masterAccountID": "",
                "exchangeID": "Exchange",
                "accountID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                "orderSysID": "1000633129818889",
                "volumeRemain": "0",
                "price": "183.36",
                "businessValue": "1760183423813",
                "frozenMargin": "0",
                "instrumentID": "SOLUSDT",
                "posiDirection": "2",
                "volumeMode": "1",
                "volume": "0.06",
                "insertTime": "1760183423",
                "copyMemberID": "",
                "position": "0.06",
                "tradePrice": "183.45",
                "leverage": "100",
                "businessResult": "",
                "availableUse": "0",
                "orderStatus": "1",
                "openPrice": "182.94",
                "frozenMoney": "0",
                "remark": "def",
                "reserveUse": "0",
                "sessionNo": "41",
                "isCrossMargin": "1",
                "closeProfit": "0.0306",
                "businessNo": "1001770756852986", # 订单有成交会并入仓位 businessNo
                "relatedOrderSysID": "",
                "positionID": "1000632926272299",
                "mockResp": false,
                "deriveSource": "0",
                "copyOrderID": "",
                "currency": "USDT",
                "turnover": "11.007",
                "frontNo": "-68",
                "direction": "1",
                "orderPriceType": "4",
                "volumeCancled": "0",
                "updateTime": "1760183423",
                "localID": "1000633129818889",
                "volumeTraded": "0.06",
                "appid": "WEB",
                "tradeUnitID": "e1b03fb1-6849-464f-a",
                "businessType": "P",
                "memberID": "e1b03fb1-6849-464f-a986-94b9a6e625e6",
                "timeCondition": "0",
                "copyProfit": "0"
            }

        """

        direction_code = self._normalize_direction(direction)
        offset_code = self._normalize_offset(offset_flag)
        price_type_code, order_type_code = self._resolve_order_type(order_type)

        detail_entry = self._get_detail_entry(symbol)
        volume_str = self._format_with_step(volume, detail_entry.get("step_size"))
        price_str: str | None = None
        if price_type_code == "0":
            if price is None:
                raise ValueError("price is required for limit orders")
            price_str = self._format_with_step(price, detail_entry.get("tick_size"))

        payload: dict[str, Any] = {
            # "ProductGroup": product_group,
            "InstrumentID": symbol,
            "ExchangeID": exchange_id,
            "Direction": direction_code,
            "OffsetFlag": offset_code,
            "OrderPriceType": price_type_code,
            "OrderType": order_type_code,
            "Volume": volume_str,
            "orderProportion": order_proportion,
        }

        if price_type_code == "0":
            payload["Price"] = price_str
        elif price is not None:
            # logger.warning("Price is ignored for market orders")
            pass


        res = await self.client.post(
            f"{self.front_api}/cfd/cff/v1/SendOrderInsert",
            json=payload,
            headers=self._rest_headers,
        )
        data = await res.json()
        return self._ensure_ok("place_order", data)

    async def cancel_order(
        self,
        order_sys_id: str,
        *,
        action_flag: str | int = "1",
    ) -> dict[str, Any]:
        """Cancel an order by OrderSysID."""

        payload = {"OrderSysID": order_sys_id, "ActionFlag": str(action_flag)}
        res = await self.client.post(
            f"{self.front_api}/cfd/action/v1.0/SendOrderAction",
            json=payload,
            headers=self._rest_headers,
        )
        data = await res.json()
        return self._ensure_ok("cancel_order", data)

    @staticmethod
    def _ensure_ok(operation: str, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict) or data.get("code") != 200:
            raise RuntimeError(f"{operation} failed: {data}")
        return data.get("data") or {}
    
    # https://uuapi.rerrkvifj.com/cfd/agg/v1/sendQryAll
    # {
    # "productGroup": "SwapU",
    # "instrumentID": "BTCUSDT",
    # "asset": "USDT"
    # }
    
    async def query_all(self, symbol:str):
        """查询资产信息
        
        .. code:: json
        
            {
                "fundingRateTimestamp": 28800,
                "isMarketAcount": 0,
                "longMaxVolume": 10000000000000000,
                "role": 2,
                "openingTime": 1609545600000,
                "isCrossMargin": 1,
                "longLeverage": 25,
                "shortLastVolume": 10000000000000000,
                "longLastVolume": 10000000000000000,
                "onTime": 1609459200000,
                "shortMaintenanceMarginRate": "0.0025",
                "state": 3,
                "markedPrice": "111031.3",
                "assetBalance": {
                "reserveAvailable": "0.0",
                "balance": "22.79163408",
                "frozenMargin": "0.0",
                "reserveMode": "0",
                "totalCloseProfit": "-15.982736",
                "available": "22.79163408",
                "crossMargin": "0.0",
                "reserve": "0.0",
                "frozenFee": "0.0",
                "marginAble": "0.0",
                "realAvailable": "22.79163408"
                },
                "longMaxLeverage": 200,
                "shortMaintenanceMarginQuickAmount": "0",
                "shortLastAmount": "10798590",
                "unrealProfitCalType": "2",
                "longLastAmount": "10798590",
                "shortMaxVolume": 10000000000000000,
                "shortLeverage": 25,
                "calMarkedPrice": "111031.3",
                "longMaintenanceMarginRate": "0.0025",
                "wsToken": "fa1d5e0ad94ede6efab6ced66ea5367cfe68c81173863424dc6e8d846d7e723b",
                "shortMaxLeverage": 200,
                "nextFundingRateTimestamp": 1760976000000,
                "longMaintenanceMarginQuickAmount": "0",
                "forbidTrade": false,
                "defaultPositionType": "2",
                "lastPrice": "111027.9",
                "fundingRate": "0.00003598"
            }
            
        """

        payload = {
            "productGroup": "SwapU",
            "instrumentID": symbol,
            "asset": "USDT"
        }
        res = await self.client.post(
            f"{self.front_api}/cfd/agg/v1/sendQryAll",
            json=payload,
            headers=self._rest_headers,
        )
        data = await res.json()
        return self._ensure_ok("query_all", data)
        

    async def set_position_mode(self, mode: Literal["hedge", "oneway"] = "oneway") -> dict[str, Any]:
        """设置持仓模式到单向持仓或对冲持仓"""

        mode_code = "2" if mode == "oneway" else "1"
        payload = {
            "PositionType": mode_code,
        }
        res = await self.client.post(
            f"{self.front_api}/cfd/action/v1.0/SendMemberAction",
            json=payload,
            headers=self._rest_headers,
        )
        data = await res.json()
        return self._ensure_ok("set_position_mode", data)

    @staticmethod
    def _normalize_direction(direction: str) -> str:
        mapping = {
            "buy": "0",
            "long": "0",
            "sell": "1",
            "short": "1",
        }
        return mapping.get(str(direction).lower(), str(direction))

    @staticmethod
    def _normalize_offset(offset: str) -> str:
        mapping = {
            "open": "0",
            "close": "1",
        }
        return mapping.get(str(offset).lower(), str(offset))

    @staticmethod
    def _resolve_order_type(order_type: str) -> tuple[str, str]:
        mapping = {
            "market": ("4", "1"),
            "limit_ioc": ("0", "1"),
            "limit_gtc": ("0", "0"),
        }
        try:
            return mapping[str(order_type).lower()]
        except KeyError as exc:  # pragma: no cover - guard
            raise ValueError(f"Unsupported order_type: {order_type}") from exc


    async def sub_orderbook(self, symbols: list[str], limit: int | None = None) -> None:
        """订阅指定交易对的订单簿（遵循 LBank 协议）。
        """

        async def sub(payload):
            wsapp = self.client.ws_connect(
                self.ws_url,
                hdlr_bytes=self.store.onmessage,
                send_json=payload,
            )
            await wsapp._event.wait()

        send_jsons = []
        y = 3000000001
        if limit:
            self.store.book.limit = limit

        for symbol in symbols:

            info = self.store.detail.get({"symbol": symbol})
            if not info:
                raise ValueError(f"Unknown LBank symbol: {symbol}")
            
            tick_size = info['tick_size']
            sub_i = symbol + "_" + str(tick_size) + "_25"
            send_jsons.append(
                {
                    "x": 3,
                    "y": str(y),
                    "a": {"i": sub_i},
                    "z": 1,
                }
            )

            self.store.register_book_channel(str(y), symbol)
            y += 1

        # Rate limit: max 5 subscriptions per second
        for i in range(0, len(send_jsons), 5):
            batch = send_jsons[i:i+5]
            await asyncio.gather(*(sub(send_json) for send_json in batch))
            if i + 5 < len(send_jsons):
                await asyncio.sleep(0.3)
