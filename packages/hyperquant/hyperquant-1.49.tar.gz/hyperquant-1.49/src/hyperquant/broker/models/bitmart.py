from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal, Sequence

from pybotters.store import DataStore, DataStoreCollection

if TYPE_CHECKING:
    from pybotters.typedefs import Item
    from pybotters.ws import ClientWebSocketResponse


def _maybe_to_dict(payload: Any) -> Any:
    if payload is None:
        return None
    if hasattr(payload, "to_dict"):
        return payload.to_dict()
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload

class Ticker(DataStore):
    """Bitmart 合约行情数据。"""

    _KEYS = ["contract_id"]

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        tickers = payload.get("data", {}).get("tickers") or []
        items: list[dict[str, Any]] = []
        for entry in tickers:
            if not isinstance(entry, dict):
                continue
            contract_id = entry.get("contract_id")
            if contract_id is None:
                continue
            items.append(entry)
        self._clear()
        if items:
            self._insert(items)

class Book(DataStore):
    """Bitmart 合约深度数据。"""

    _KEYS = ["s", "S", "p"]

    def _init(self) -> None:
        self.limit: int | None = None
        self.id_to_symbol: dict[str, str] = {}
        self._state: dict[str, dict[str, dict[float, float]]] = {}
        self._last_update: float = 0.0

    @classmethod
    def _make_entry(cls, symbol: str, side: Literal["a", "b"], price: str, size: str) -> dict[str, Any]:
        return {
            "s": symbol,
            "S": side,
            "p": price,
            "q": size,
        }

    def _on_message(self, msg: dict[str, Any]) -> None:
        data = msg.get("data")
        group = msg.get("group")
        ms_t = msg.get("ms_t")
        if not isinstance(data, dict) or not isinstance(group, str):
            return

        try:
            _, contract_id = group.split(":", 1)
        except ValueError:
            return

        symbol = self.id_to_symbol.get(contract_id) or contract_id

        state = self._state.setdefault(symbol, {"a": {}, "b": {}})

        way = data.get("way")
        depths = data.get("depths") or []
        if way not in {1, 2} or not isinstance(depths, Sequence):
            return

        side_key = "b" if way == 1 else "a"
        if self.limit:
            depths = depths[: self.limit]
        
        self._find_and_delete({'s': symbol, 'S': side_key})
        self._update([
            self._make_entry(
                symbol,
                side_key,
                entry.get("price", '0'),
                entry.get("vol", '0'),
            )
            for entry in depths
        ])

        self._last_update = ms_t
    
    def _on_message_api(self, msg: dict[str, Any]) -> None:
        data = msg.get("data")
        if not isinstance(data, dict):
            return
        # Some callers embed symbol at top-level; prefer msg["symbol"] when present
        symbol = msg.get("symbol") or data.get("symbol")
        asks = data.get("asks") or []
        bids = data.get("bids") or []
        if self.limit:
            asks = asks[: self.limit]
            bids = bids[: self.limit]
            
        self._find_and_delete({'s': symbol})
        # OpenAPI order book arrays are typically [price, size, timestamp]
        def _normalize_level(level: Any) -> tuple[str, str]:
            if isinstance(level, dict):
                return str(level.get("price", "0")), str(level.get("vol", "0"))
            if isinstance(level, (list, tuple)) and len(level) >= 2:
                return str(level[0]), str(level[1])
            return "0", "0"

        self._update([
            self._make_entry(
                symbol,
                "a",
                *_normalize_level(entry),
            )
            for entry in asks
        ])
        self._update([
            self._make_entry(
                symbol,
                "b",
                *_normalize_level(entry),
            )
            for entry in bids
        ])
    

    def sorted(self, query: Item | None = None, limit: int | None = None) -> dict[str, list[Item]]:
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
    """Bitmart 合约详情。"""

    _KEYS = ["name"]

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        contracts = payload.get("data", {}).get("contracts") or []

        records: list[dict[str, Any]] = []
        for item in contracts:
            if not isinstance(item, dict):
                continue
            record: dict[str, Any] = {}
            contract = item.get("contract") or {}
            if isinstance(contract, dict):
                record.update(contract)
            risk_limit = item.get("risk_limit") or {}
            if isinstance(risk_limit, dict):
                record.update({f"risk_{k}": v for k, v in risk_limit.items()})
            fee_config = item.get("fee_config") or {}
            if isinstance(fee_config, dict):
                record.update({f"fee_{k}": v for k, v in fee_config.items()})
            plan_order_config = item.get("plan_order_config") or {}
            if isinstance(plan_order_config, dict):
                record.update({f"plan_{k}": v for k, v in plan_order_config.items()})
            tag_detail = item.get("contract_tag_detail") or {}
            if isinstance(tag_detail, dict):
                record.update({f"tag_{k}": v for k, v in tag_detail.items()})

            contract_id = record.get("contract_id") or contract.get("contract_id")
            if contract_id is None:
                continue
            record["contract_id"] = contract_id
            record["tick_size"] = record.get("price_unit")
            records.append(record)

        self._clear()
        if records:
            self._insert(records)


class Ticker(DataStore):
    """24h 数据信息。"""

    _KEYS = ["contract_id"]

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        tickers = payload.get("data", {}).get("tickers") or []
        items: list[dict[str, Any]] = []
        for entry in tickers:
            if not isinstance(entry, dict):
                continue
            contract_id = entry.get("contract_id")
            if contract_id is None:
                continue
            record = dict(entry)
            record["contract_id"] = contract_id
            items.append(record)

        self._clear()
        if items:
            self._insert(items)


class Orders(DataStore):
    """订单列表。"""

    _KEYS = ["order_id"]

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        order_id = entry.get("order_id")
        if order_id is None:
            return None
        normalized = dict(entry)
        normalized["order_id"] = order_id
        return normalized

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        orders = payload.get("data", {}).get("orders") or []
        items: list[dict[str, Any]] = []
        for entry in orders:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize(entry)
            if normalized:
                items.append(normalized)
        self._clear()
        if items:
            self._insert(items)


class Positions(DataStore):
    """持仓信息。"""

    _KEYS = ["position_id"]

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        position_id = entry.get("position_id")
        if position_id is None:
            return None
        normalized = dict(entry)
        normalized["position_id"] = position_id
        return normalized

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        positions = payload.get("data", {}).get("positions") or []
        items: list[dict[str, Any]] = []
        for entry in positions:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize(entry)
            if normalized:
                items.append(normalized)
        self._clear()
        if items:
            self._insert(items)


class Balances(DataStore):
    """账户资产信息。"""

    _KEYS = ["coin_code"]

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        coin = entry.get("coin_code")
        if coin is None:
            return None
        normalized = dict(entry)
        normalized["coin_code"] = coin
        return normalized

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        assets = payload.get("data", {}).get("assets") or []
        items: list[dict[str, Any]] = []
        for entry in assets:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize(entry)
            if normalized:
                items.append(normalized)
        self._clear()
        if items:
            self._insert(items)


class BitmartDataStore(DataStoreCollection):
    """Bitmart 合约数据集合。"""

    def _init(self) -> None:
        self._create("book", datastore_class=Book)
        self._create("detail", datastore_class=Detail)
        self._create("orders", datastore_class=Orders)
        self._create("positions", datastore_class=Positions)
        self._create("balances", datastore_class=Balances)
        self._create("ticker", datastore_class=Ticker)
    
    def onmessage(self, msg: Item, ws: ClientWebSocketResponse | None = None) -> None:
        if isinstance(msg, dict):
            group = msg.get("group")

            if isinstance(group, str):
                if group.startswith("futures/depth"):
                    self.book._on_message_api(msg)
                if group.startswith("Depth"):
                    self.book._on_message(msg)

    @property
    def book(self) -> Book:
        """
        .. code:: json

            {
                "s": "BTCUSDT",
                "S": "a",  # 卖单
                "p": "95640.3",
                "q": "0.807"
            }
        """
        return self._get("book")

    @property
    def detail(self) -> Detail:
        """`ifcontract/contracts_all` 返回的合约配置信息。

        .. code:: json

            {
                "contract_id": 1,
                "index_id": 1,
                "name": "BTCUSDT",
                "display_name": "BTCUSDT 永续合约",
                "display_name_en": "BTCUSDT_SWAP",
                "contract_type": 1,
                "base_coin": "BTC",
                "quote_coin": "USDT",
                "price_coin": "BTC",
                "exchange": "*",
                "contract_size": "0.001",
                "begin_at": "2022-02-27T16:00:00Z",
                "end_at": "2020-01-01T00:00:00Z",
                "delive_at": "2018-10-01T02:00:00Z",
                "delivery_cycle": 28800,
                "min_leverage": "1",
                "max_leverage": "200",
                "price_unit": "0.1",
                "tick_size": "0.1",
                "vol_unit": "1",
                "value_unit": "0.1",
                "min_vol": "1",
                "max_vol": "500000",
                "liquidation_warn_ratio": "0.85",
                "fast_liquidation_ratio": "0.8",
                "settle_type": 1,
                "open_type": 3,
                "compensate_type": 1,
                "status": 3,
                "block": 1,
                "rank": 1,
                "created_at": "2018-07-12T09:16:57Z",
                "depth_bord": "0.0375",
                "base_coin_zh": "",
                "base_coin_en": "",
                "max_rate": "0.0375",
                "min_rate": "-0.0375",
                "market_status": 0,
                "hedge_name": "binance",
                "icon_url": "/static-file/public/coin/BTC-20200604060942.png",
                "robot_risk_threshold": "0",
                "fund_rate_threshold": "0",
                "fund_rate_switch": 0,
                "fund_rate_config": "0",
                "market_price_rate": "0.003",
                "robot_fund_rate_offset": "0",
                "credit_max_leverage": 20,
                "limit_ratio": "0.05",
                "max_order_num": 200,
                "min_trade_val": "5",
                "bind_order_flag": false,
                "market_max_vol": "80000",
                "quote_type": 1,
                "risk_contract_id": 1,
                "risk_base_limit": "1000000",
                "risk_step": "1000000",
                "risk_maintenance_margin": "0.0025",
                "risk_initial_margin": "0.005",
                "risk_status": 1,
                "fee_contract_id": 1,
                "fee_maker_fee": "0.0002",
                "fee_taker_fee": "0.0006",
                "fee_settlement_fee": "0",
                "fee_created_at": "2018-07-12T20:47:22Z",
                "plan_contract_id": 0,
                "plan_min_scope": "0.001",
                "plan_max_scope": "2",
                "plan_max_count": 100,
                "plan_min_life_cycle": 24,
                "plan_max_life_cycle": 438000,
                "tag_tag_id": 1,
                "tag_tag_name": "hot"
            }
        """
        return self._get("detail")

    @property
    def orders(self) -> Orders:
        """用户订单 (`userAllOrders`)。
        key: order_id
        .. code:: json

            [
                {
                    "order_id": 3000236525013551,
                    "contract_id": 72,
                    "position_id": 0,
                    "account_id": 2008001004625862,
                    "price": "0.25",
                    "vol": "1",
                    "done_vol": "0",
                    "done_avg_price": "0",
                    "way": 1,
                    "category": 1,
                    "make_fee": "0",
                    "take_fee": "0",
                    "origin": "web",
                    "created_at": "2025-10-29T08:23:20.745717Z",
                    "updated_at": "2025-10-29T08:23:20.753482Z",
                    "finished_at": "",
                    "status": 2,
                    "errno": 0,
                    "mode": 1,
                    "leverage": "10",
                    "open_type": 2,
                    "order_type": 0,
                    "extends": {
                        "remark": "default",
                        "broker_id": "",
                        "order_type": 0,
                        "bonus_only": false,
                        "request_trace_id": "",
                        "trigger_ratio_type": 0,
                        "is_guaranteed_sl_or_tp": false,
                        "is_market_zero_slippage": false,
                        "zero_slippage_ratio": ""
                    },
                    "client_order_id": "",
                    "executive_price": "",
                    "life_cycle": 0,
                    "price_type": 0,
                    "price_way": 0,
                    "plan_category": 0,
                    "activation_price": "",
                    "callback_rate": "",
                    "executive_order_id": 0,
                    "bind_leverage": "",
                    "pre_plan_order_id": 0,
                    "stop_profit_executive_price": "",
                    "stop_profit_price_type": 0,
                    "stop_loss_executive_price": "",
                    "stop_loss_price_type": 0,
                    "liquidation_fee": "",
                    "account_type": 0,
                    "pnl": "",
                    "data_type": "",
                    "position_mode": 1,
                    "pnl_rate": "",
                    "preset_is_guaranteed_sl": false,
                    "preset_is_guaranteed_tp": false
                }
            ]
        """
        return self._get("orders")

    @property
    def positions(self) -> Positions:
        """用户持仓 (`userPositions`)。

        .. code:: json

            [
                {
                    "position_id": 3000236533088511,
                    "account_id": 2008001004625862,
                    "contract_id": 72,
                    "hold_vol": "1",
                    "freeze_vol": "0",
                    "close_vol": "0",
                    "hold_avg_price": "0.2964901",
                    "open_avg_price": "0.2964901",
                    "close_avg_price": "0",
                    "oim": "0.02982690406",
                    "im": "0.02982690406",
                    "mm": "0.000741261625",
                    "realised_profit": "-0.00017789406",
                    "earnings": "-0.00017789406",
                    "hold_fee": "0",
                    "open_type": 2,
                    "position_type": 1,
                    "status": 1,
                    "errno": 0,
                    "created_at": "2025-10-29T11:16:37.63704Z",
                    "updated_at": "2025-10-29T11:16:37.63704Z",
                    "notional_value": "0.2964901",
                    "fair_value": "0.29650465",
                    "current_value": "0.2965151",
                    "liquidation_value": "-10.702412850255",
                    "bankruptcy_value": "0",
                    "close_able_vol": "1",
                    "bankruptcy_fee": "0.00017789406",
                    "current_un_earnings": "0.000025",
                    "fair_un_earnings": "0.00001455",
                    "liquidate_price": "0",
                    "current_roe": "0.0008431570971989815",
                    "fair_roe": "0.0004907174305698073",
                    "current_notional_roe": "0.0008431984744178642",
                    "fair_notional_roe": "0.000490741512111197",
                    "leverage": "0.0269540457075690273",
                    "bind_leverage": "10",
                    "account_type": 0,
                    "position_mode": 0,
                    "fee": "-0.00017789406"
                }
            ]
        """
        return self._get("positions")

    @property
    def balances(self) -> Balances:
        """账户资产 (`copy/trade/user/info`)。

        .. code:: json

            [
                {
                    "account_id": 14794011,
                    "coin_code": "USDT",
                    "available_vol": "10.970977797397999999",
                    "cash_vol": "11.000536099457999999",
                    "freeze_vol": "0",
                    "realised_vol": "0.000536099457999999",
                    "un_realised_vol": "-0.00001502",
                    "earnings_vol": "0.000536099457999999",
                    "total_im": "",
                    "margin_balance": "",
                    "available_balance": "",
                    "trans_out_balance": "",
                    "status": 0,
                    "total_balance": "",
                    "account_rights": "11.000521079457999999",
                    "bonus_voucher_vol": "",
                    "freeze_bonus_voucher_vol": ""
                }
            ]
        """
        return self._get("balances")

    @property
    def ticker(self) -> Ticker:
        """Bitmart 合约行情数据（`/v1/ifcontract/tickers` 返回）。

        表示 Bitmart 合约行情接口 `/v1/ifcontract/tickers` 返回的数据，包含合约的最新价格、成交量、指数价格、公允价格、资金费率等信息。

        .. code:: json

            [
                {
                    "last_price": "0.002296",
                    "open": "0.002347",
                    "close": "0.002296",
                    "low": "0.00224",
                    "high": "0.002394",
                    "avg_price": "0.0023197328648874",
                    "volume": "6",
                    "total_volume": "200110472",
                    "timestamp": 1761812348,
                    "rise_fall_rate": "-0.0217298679164891",
                    "rise_fall_value": "-0.000051",
                    "contract_id": 33125,
                    "contract_name": "IOSTUSDT",
                    "position_size": "",
                    "volume24": "229630336",
                    "amount24": "533620.3631860018137124",
                    "high_price_24": "0.002394",
                    "low_price_24": "0.00224",
                    "base_coin_volume": "200110472",
                    "quote_coin_volume": "464202.8385065298408528",
                    "ask_price": "0.002302",
                    "ask_vol": "6396074",
                    "bid_price": "0.002289",
                    "bid_vol": "3214783",
                    "index_price": "0.00229906",
                    "fair_price": "0.002296",
                    "depth_price": {
                        "bid_price": "0",
                        "ask_price": "0",
                        "mid_price": "0"
                    },
                    "fair_basis": "",
                    "fair_value": "",
                    "rate": {
                        "quote_rate": "0",
                        "base_rate": "0",
                        "interest_rate": "0"
                    },
                    "premium_index": "",
                    "funding_rate": "-0.0000601",
                    "next_funding_rate": "",
                    "next_funding_at": "2025-10-30T16:00:00Z",
                    "pps": "0",
                    "quote_coin": "USDT",
                    "base_coin": "IOST"

            ]
        """
        return self._get("ticker")
