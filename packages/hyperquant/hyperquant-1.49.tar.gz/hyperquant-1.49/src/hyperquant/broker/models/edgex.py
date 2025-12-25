from __future__ import annotations

import asyncio
from typing import Any, Awaitable, TYPE_CHECKING

from aiohttp import ClientResponse
import aiohttp
from pybotters.store import DataStore, DataStoreCollection

if TYPE_CHECKING:
    from pybotters.typedefs import Item
    from pybotters.ws import ClientWebSocketResponse


class Book(DataStore):
    """Order book data store for the Edgex websocket feed."""

    _KEYS = ["c", "S", "p"]

    def _init(self) -> None:
        self._version: int | str | None = None
        self.limit: int | None = None

    def _on_message(self, msg: dict[str, Any]) -> None:
        content = msg.get("content") or {}
        entries = content.get("data") or []
        data_type = (content.get("dataType") or "").lower()

        for entry in entries:
            contract_id = entry.get("contractId")
            if contract_id is None:
                continue

            contract_name = entry.get("contractName")
            end_version = entry.get("endVersion")
            depth_type = (entry.get("depthType") or "").lower()

            is_snapshot = data_type == "snapshot" or depth_type == "snapshot"

            if is_snapshot:
                self._handle_snapshot(
                    contract_id,
                    contract_name,
                    entry,
                )
            else:
                self._handle_delta(
                    contract_id,
                    contract_name,
                    entry,
                )

            if end_version is not None:
                self._version = self._normalize_version(end_version)

    def _handle_snapshot(
        self,
        contract_id: str,
        contract_name: str | None,
        entry: dict[str, Any],
    ) -> None:
        asks = entry.get("asks") or []
        bids = entry.get("bids") or []

        self._find_and_delete({"c": contract_id})

        payload: list[dict[str, Any]] = []
        payload.extend(
            self._build_items(
                contract_id,
                contract_name,
                "a",
                asks,
            )
        )
        payload.extend(
            self._build_items(
                contract_id,
                contract_name,
                "b",
                bids,
            )
        )

        if payload:
            self._insert(payload)
            self._trim(contract_id, contract_name)

    def _handle_delta(
        self,
        contract_id: str,
        contract_name: str | None,
        entry: dict[str, Any],
    ) -> None:
        updates: list[dict[str, Any]] = []
        deletes: list[dict[str, Any]] = []

        asks = entry.get("asks") or []
        bids = entry.get("bids") or []

        for side, levels in (("a", asks), ("b", bids)):
            for row in levels:
                price, size = self._extract_price_size(row)
                criteria = {"c": contract_id, "S": side, "p": price}

                if not size or float(size) == 0.0:
                    deletes.append(criteria)
                    continue

                updates.append(
                    {
                        "c": contract_id,
                        "S": side,
                        "p": price,
                        "q": size,
                        "s": self._symbol(contract_id, contract_name),
                    }
                )

        if deletes:
            self._delete(deletes)
        if updates:
            self._update(updates)
            self._trim(contract_id, contract_name)

    def _build_items(
        self,
        contract_id: str,
        contract_name: str | None,
        side: str,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in rows:
            price, size = self._extract_price_size(row)
            if not size or float(size) == 0.0:
                continue
            items.append(
                {
                    "c": contract_id,
                    "S": side,
                    "p": price,
                    "q": size,
                    "s": self._symbol(contract_id, contract_name),
                }
            )
        return items

    @staticmethod
    def _normalize_version(value: Any) -> int | str:
        if value is None:
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _to_str(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _extract_price_size(row: dict[str, Any]) -> tuple[str, str]:
        return str(row["price"]), str(row["size"])

    def _trim(self, contract_id: str, contract_name: str | None) -> None:
        if self.limit is None:
            return

        query: dict[str, Any]
        symbol = self._symbol(contract_id, contract_name)
        if symbol:
            query = {"s": symbol}
        else:
            query = {"c": contract_id}

        sort_data = self.sorted(query, self.limit)
        asks = sort_data.get("a", [])
        bids = sort_data.get("b", [])

        self._find_and_delete(query)

        trimmed = asks + bids
        if trimmed:
            self._insert(trimmed)

    @staticmethod
    def _symbol(contract_id: str, contract_name: str | None) -> str:
        if contract_name:
            return str(contract_name)
        return str(contract_id)

    @property
    def version(self) -> int | str | None:
        """返回当前缓存的订单簿版本号。"""
        return self._version

    def sorted(
        self,
        query: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """按买卖方向与价格排序后的订单簿视图。"""
        return self._sorted(
            item_key="S",
            item_asc_key="a",
            item_desc_key="b",
            sort_key="p",
            query=query,
            limit=limit,
        )


class Ticker(DataStore):
    """24 小时行情推送数据。"""

    _KEYS = ["c"]

    def _on_message(self, msg: dict[str, Any]) -> None:
        content = msg.get("content") or {}
        entries = content.get("data") or []
        data_type = (content.get("dataType") or "").lower()

        for entry in entries:
            item = self._format(entry)
            if item is None:
                continue

            criteria = {"c": item["c"]}
            if data_type == "snapshot":
                self._find_and_delete(criteria)
                self._insert([item])
            else:
                self._update([item])

    def _onresponse(self, data: dict[str, Any]) -> None:
        entries = data.get("data") or []

        if not isinstance(entries, list):
            entries = [entries]

        items = []
        for entry in entries:
            item = self._format(entry)
            if item:
                items.append(item)

        self._clear()
        if items:
            self._insert(items)

    def _format(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        contract_id = entry.get("contractId")
        if contract_id is None:
            return None

        item: dict[str, Any] = {"c": str(contract_id)}

        name = entry.get("contractName")
        if name is not None:
            item["s"] = str(name)

        fields = [
            "priceChange",
            "priceChangePercent",
            "trades",
            "size",
            "value",
            "high",
            "low",
            "open",
            "close",
            "highTime",
            "lowTime",
            "startTime",
            "endTime",
            "lastPrice",
            "indexPrice",
            "oraclePrice",
            "openInterest",
            "fundingRate",
            "fundingTime",
            "nextFundingTime",
            "bestAskPrice",
            "bestBidPrice",
        ]

        for key in fields:
            value = entry.get(key)
            if value is not None:
                item[key] = str(value)

        return item


class Order(DataStore):
    """Order data store combining REST results with trade-event deltas.

    We only keep fields that are practical for trading book-keeping: identifiers,
    basic order parameters, cumulative fills, high-level status and timestamps.
    Network payloads carry hundreds of fields (``l2`` signatures, TPSL templates,
    liquidation metadata, etc.), but the extra data adds noise and bloats memory
    consumption.  This store narrows every entry to a compact schema while still
    supporting diff events from the private websocket feed.
    """

    _KEYS = ["orderId"]

    _TERMINAL_STATUSES = {
        "FILLED",
        "CANCELED",
        "CANCELLED",
        "REJECTED",
        "EXPIRED",
    }

    _ACTIVE_STATUSES = {
        "OPEN",
        "PARTIALLY_FILLED",
        "PENDING",
        "CREATED",
        "ACKNOWLEDGED",
    }

    _KEEP_FIELDS = (
        "userId",
        "accountId",
        "coinId",
        "contractId",
        "clientOrderId",
        "type",
        "timeInForce",
        "reduceOnly",
        "price",
        "size",
        "cumFillSize",
        "cumFillValue",
        "cumMatchSize",
        "cumMatchValue",
        "cumMatchFee",
        "triggerPrice",
        "triggerPriceType",
        "cancelReason",
        "createdTime",
        "updatedTime",
        "matchSequenceId",
    )

    _BOOL_FIELDS = {"reduceOnly"}

    def _on_message(self, msg: dict[str, Any]) -> None:
        content = msg.get("content") or {}
        data = content.get("data") or {}
        orders = data.get("order") or []

        if not isinstance(orders, list):
            orders = [orders]

        items = [self._format(order) for order in orders]
        items = [item for item in items if item]
        if not items:
            return

        event = (content.get("event") or "").lower()
        if event == "snapshot":
            self._clear()
            self._insert(items)
            return

        for item in items:
            status = str(item.get("status") or "").upper()
            criteria = {"orderId": item["orderId"]}
            existing = self.find(criteria)

            if status in self._TERMINAL_STATUSES:
                if existing:
                    self._update([item])
                else:
                    self._insert([item])
                self._find_and_delete(criteria)
                continue

            if status and status not in self._ACTIVE_STATUSES:
                if existing:
                    self._update([item])
                else:
                    self._insert([item])
                self._find_and_delete(criteria)
                continue

            if existing:
                self._update([item])
            else:
                self._insert([item])

    def _onresponse(self, data: dict[str, Any]) -> None:
        payload = data.get("data")

        if isinstance(payload, dict):
            orders = payload.get("dataList") or payload.get("orderList") or []
        else:
            orders = payload or []

        if not isinstance(orders, list):
            orders = [orders]

        items = [self._format(order) for order in orders]
        items = [item for item in items if item]

        self._clear()
        if items:
            self._insert(items)

    @staticmethod
    def _normalize_order_id(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _normalize_side(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value.lower()
        return str(value)

    @staticmethod
    def _normalize_status(value: Any) -> str | None:
        if value is None:
            return None
        return str(value).upper()

    @staticmethod
    def _stringify(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (bool, dict, list)):
            return value
        return str(value)

    def _format(self, order: dict[str, Any] | None) -> dict[str, Any] | None:
        if not order:
            return None

        order_id = (
            order.get("orderId")
            or order.get("id")
            or order.get("order_id")
            or order.get("orderID")
        )

        normalized_id = self._normalize_order_id(order_id)
        if normalized_id is None:
            return None

        item: dict[str, Any] = {"orderId": normalized_id, "id": normalized_id}

        side = self._normalize_side(order.get("side"))
        if side is not None:
            item["side"] = side

        status = self._normalize_status(order.get("status"))
        if status is not None:
            item["status"] = status

        contract_name = order.get("contractName")
        if contract_name:
            symbol = self._stringify(contract_name)
            item["contractName"] = symbol
            item.setdefault("symbol", symbol)

        for field in self._KEEP_FIELDS:
            if field in ("side", "status"):
                continue
            value = order.get(field)
            if value is None:
                continue
            if field in self._BOOL_FIELDS:
                item[field] = bool(value)
            else:
                item[field] = self._stringify(value)

        return item


class Balance(DataStore):
    """Account balance snapshot retaining only the trading-critical fields."""

    _KEYS = ["accountId", "coinId"]


    def _onresponse(self, data: dict[str, Any]) -> None:
        data = data.get('data', {})
        collateral_assets = data.get('collateralAssetModelList') or []
        if collateral_assets:
            self._update(collateral_assets)

    def _on_message(self, msg: dict[str, Any]) -> None:
        pass


class Position(DataStore):
    """
    Stores per-account open positions in a simplified camelCase schema.
    Only the current open position fields are retained: positionId, contractId, accountId,
    userId, coinId, side, size, value, fee, fundingFee.
    """

    _KEYS = ["positionId"]

    @staticmethod
    def _stringify(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (bool, dict, list)):
            return value
        return str(value)

    def _onresponse(self, data: dict[str, Any]) -> None:
        """
        Handle REST response for getAccountAsset (open positions snapshot).
        Expects data from getAccountAsset (REST), which returns a snapshot of **current open positions**,
        as a list in data["positionList"].
        Each entry is normalized to camelCase schema, only including essential fields for the current open position.
        """
        data = data.get("data", {}) or {}
        positions = data.get("positionList") or []
        if not isinstance(positions, list):
            positions = [positions]
        items = [self._normalize_position(pos) for pos in positions]
        self._clear()
        if items:
            self._update(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        data = msg.get("content", {}).get("data", {})
        if not data:
            return
        positions = data.get("position")
        if not positions:
            return
        items = [self._normalize_position(pos) for pos in positions]
        self._clear()
        if items:
            self._update(items)

    def _normalize_position(self, pos: dict[str, Any]) -> dict[str, Any]:
        # Only keep essential fields for the current open position
        def get(key, *alts):
            for k in (key,) + alts:
                if k in pos and pos[k] is not None:
                    return pos[k]
            return None

        open_size = get("openSize")
        open_value = get("openValue")
        open_fee = get("openFee")
        funding_fee = get("fundingFee")

        # side: "long" if openSize > 0, "short" if openSize < 0, None if 0
        side = None
        try:
            if open_size is not None:
                fsize = float(open_size)
                if fsize > 0:
                    side = "long"
                elif fsize < 0:
                    side = "short"
        except Exception:
            side = None

        size = None
        if open_size is not None:
            try:
                size = str(abs(float(open_size)))
            except Exception:
                size = str(open_size)
        value = None
        if open_value is not None:
            try:
                value = str(abs(float(open_value)))
            except Exception:
                value = str(open_value)

        item = {
            "positionId": self._stringify(get("positionId", "position_id")),
            "contractId": self._stringify(get("contractId")),
            "accountId": self._stringify(get("accountId")),
            "userId": self._stringify(get("userId")),
            "coinId": self._stringify(get("coinId")),
            "side": side,
            "size": size,
            "value": value,
            "fee": self._stringify(open_fee),
            "fundingFee": self._stringify(funding_fee),
        }
        return item


class CoinMeta(DataStore):
    """Coin metadata (precision, StarkEx info, etc.)."""

    _KEYS = ["coinId"]

    def _onresponse(self, data: dict[str, Any]) -> None:
        coins = (data.get("data") or {}).get("coinList") or []
        items: list[dict[str, Any]] = []

        for coin in coins:
            coin_id = coin.get("coinId")
            if coin_id is None:
                continue
            items.append(
                {
                    "coinId": str(coin_id),
                    "coinName": coin.get("coinName"),
                    "stepSize": coin.get("stepSize"),
                    "showStepSize": coin.get("showStepSize"),
                    "starkExAssetId": coin.get("starkExAssetId"),
                }
            )

        self._clear()
        if items:
            self._insert(items)


class ContractMeta(DataStore):
    """Per-contract trading parameters from the metadata endpoint."""

    _KEYS = ["contractName"]

    _FIELDS = (
        "contractName",
        "baseCoinId",
        "quoteCoinId",
        "tickSize",
        "stepSize",
        "minOrderSize",
        "maxOrderSize",
        "defaultTakerFeeRate",
        "defaultMakerFeeRate",
        "enableTrade",
        "fundingInterestRate",
        "fundingImpactMarginNotional",
        "fundingRateIntervalMin",
        "starkExSyntheticAssetId",
        "starkExResolution",
    )

    def _onresponse(self, data: dict[str, Any]) -> None:
        contracts = (data.get("data") or {}).get("contractList") or []
        items: list[dict[str, Any]] = []

        for contract in contracts:
            contract_id = contract.get("contractId")
            if contract_id is None:
                continue

            payload = {"contractId": str(contract_id)}
            for key in self._FIELDS:
                payload[key] = contract.get(key)
            payload["riskTierList"] = self._simplify_risk_tiers(
                contract.get("riskTierList")
            )

            items.append(payload)

        self._clear()
        if items:
            self._insert(items)

    @staticmethod
    def _simplify_risk_tiers(risk_tiers: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for tier in risk_tiers or []:
            items.append(
                {
                    "tier": tier.get("tier"),
                    "positionValueUpperBound": tier.get("positionValueUpperBound"),
                    "maxLeverage": tier.get("maxLeverage"),
                    "maintenanceMarginRate": tier.get("maintenanceMarginRate"),
                    "starkExRisk": tier.get("starkExRisk"),
                    "starkExUpperBound": tier.get("starkExUpperBound"),
                }
            )
        return items


class AppMeta(DataStore):
    """Global metadata (appName, env, fee account, etc.)."""

    _KEYS = ["appName"]

    def _onresponse(self, data: dict[str, Any]) -> None:
        appdata = (data.get("data") or {}).get("global") or {}
        if not appdata:
            self._clear()
            return
        # Convert all values to str where appropriate, but preserve fields as-is (for bool/int etc).
        item = {}
        for k, v in appdata.items():
            if k == "starkExCollateralCoin" and isinstance(v, dict):
                # Flatten the dict into top-level fields with prefix
                for subk, subv in v.items():
                    # Compose the flattened key
                    prefix = "starkExCollateral"
                    # Capitalize first letter of subkey
                    if subk and subk[0].islower():
                        flatkey = prefix + subk[0].upper() + subk[1:]
                    else:
                        flatkey = prefix + subk
                    item[flatkey] = subv if subv is None or isinstance(subv, (bool, int, float)) else str(subv)
                continue
            # Convert to str except for None; preserve bool/int/float as-is
            if v is None:
                item[k] = v
            elif isinstance(v, (bool, int, float)):
                item[k] = v
            else:
                item[k] = str(v)
        self._clear()
        if item:
            self._insert([item])


class EdgexDataStore(DataStoreCollection):
    """Edgex DataStore collection exposing the order book feed."""

    def _init(self) -> None:
        self._create("book", datastore_class=Book)
        self._create("ticker", datastore_class=Ticker)
        self._create("orders", datastore_class=Order)
        self._create("balance", datastore_class=Balance)
        # Position store holds per-account open positions in simplified camelCase form
        self._create("position", datastore_class=Position)
        self._create("meta_coin", datastore_class=CoinMeta)
        self._create("detail", datastore_class=ContractMeta)
        self._create("app", datastore_class=AppMeta)

    @property
    def book(self) -> Book:
        """
        获取 Edgex 合约订单簿数据流。

        .. code:: json

            [
                {
                    "c": "10000001",        # 合约 ID
                    "s": "BTCUSD",
                    "S": "a",               # 方向 a=卖 b=买
                    "p": "117388.2",        # 价格
                    "q": "12.230",          # 数量
                }
            ]
        """
        return self._get("book")

    @property
    def orders(self) -> Order:
        """
        账户订单数据流（REST 快照 + 私有 WS 增量）。

        存储为**精简 schema**，仅保留实操必需字段。终态订单（FILLED / CANCELED / CANCELLED / REJECTED / EXPIRED）
        会在写入一次后从本地缓存删除，只保留进行中的订单（OPEN / PARTIALLY_FILLED / PENDING / CREATED / ACKNOWLEDGED）。


        存储示例（本地条目）
        -------------------
        REST 快照：

        .. code:: json

            [
                {
                    "orderId": "564815695875932430",
                    "id": "564815695875932430",
                    "contractId": "10000001",
                    "contractName": "BTCUSD",
                    "symbol": "BTCUSD",
                    "side": "buy",
                    "status": "OPEN",
                    "type": "LIMIT",
                    "timeInForce": "GOOD_TIL_CANCEL",
                    "reduceOnly": false,
                    "price": "97444.5",
                    "size": "0.010",
                    "cumFillSize": "0.000",
                    "cumFillValue": "0",
                    "clientOrderId": "553364074986685",
                    "createdTime": "1734662555665",
                    "updatedTime": "1734662555665"
                }
            ]


        """
        return self._get("orders")

    @property
    def balance(self) -> Balance:
        """
        获取账户资产余额（REST 快照 + 私有 WS 增量）。

        .. code:: json

            [
                {
                    userId: "663528067892773124",
                    accountId: "663528067938910372",
                    coinId: "1000",
                    totalEquity: "22.721859",
                    totalPositionValueAbs: "0",
                    initialMarginRequirement: "0",
                    starkExRiskValue: "0",
                    pendingWithdrawAmount: "0",
                    pendingTransferOutAmount: "0",
                    orderFrozenAmount: "3.001126965030794963240623474121093750",
                    availableAmount: "19.720732",
                },
            ]

        """
        return self._get("balance")
        
    @property
    def position(self) -> "Position":
        """
        获取账户当前未平仓持仓（open positions，来自 getAccountAsset）。

        本属性提供**当前未平仓持仓**的快照（由 REST ``getAccountAsset`` 提供），每条数据为当前账户的一个持仓（多/空/逐仓/全仓等）。
        字段为 snake_case，包含持仓数量、均价、强平价、杠杆、保证金率等信息，适合用于持仓管理与风险监控。

        数据示例：

        .. code:: python

        [
            {
                orderId: "665307878751470244",
                id: "665307878751470244",
                side: "buy",
                status: "OPEN",
                userId: "663528067892773124",
                accountId: "663528067938910372",
                coinId: "1000",
                contractId: "10000003",
                clientOrderId: "32570392453812747",
                type: "LIMIT",
                timeInForce: "GOOD_TIL_CANCEL",
                reduceOnly: False,
                price: "210.00",
                size: "0.3",
                cumFillSize: "0",
                cumFillValue: "0",
                cumMatchSize: "0",
                cumMatchValue: "0",
                cumMatchFee: "0",
                triggerPrice: "0",
                triggerPriceType: "UNKNOWN_PRICE_TYPE",
                cancelReason: "UNKNOWN_ORDER_CANCEL_REASON",
                createdTime: "1758621759117",
                updatedTime: "1758621759122",
                matchSequenceId: "784278904",
            },
        ];


        本属性仅包含**当前持有的未平仓持仓**（由 REST ``getAccountAsset`` 提供）。
        若需获取**历史已平仓持仓周期**，请调用 ``getPositionTermPage``。
        """
        return self._get("position")
        
    @property
    def coins(self) -> CoinMeta:
        """
        获取币种精度及 StarkEx 资产信息列表。

        .. code:: json

            [
                {
                    "coinId": "1000",
                    "coinName": "USDT",
                    "stepSize": "0.000001",
                    "showStepSize": "0.0001",
                    "starkExAssetId": "0x33bda5c9..."
                }
            ]
        """
        return self._get("meta_coin")

    @property
    def detail(self) -> ContractMeta:
        """
        获取合约级别的交易参数。

        .. code:: json

            [
                {
                    "contractId": "10000001",
                    "contractName": "BTCUSD",
                    "baseCoinId": "1001",
                    "quoteCoinId": "1000",
                    "tickSize": "0.1",
                    "stepSize": "0.001",
                    "minOrderSize": "0.001",
                    "maxOrderSize": "50.000",
                    "defaultMakerFeeRate": "0.0002",
                    "defaultTakerFeeRate": "0.00055",
                    "enableTrade": true,
                    "fundingInterestRate": "0.0003",
                    "fundingImpactMarginNotional": "10",
                    "fundingRateIntervalMin": "240",
                    "starkExSyntheticAssetId": "0x42544332...",
                    "starkExResolution": "0x2540be400",
                    "riskTierList": [
                        {
                            "tier": 1,
                            "positionValueUpperBound": "50000",
                            "maxLeverage": "100",
                            "maintenanceMarginRate": "0.005",
                            "starkExRisk": "21474837",
                            "starkExUpperBound": "214748364800000000000"
                        }
                    ]
                }
            ]
        """
        return self._get("detail")

    @property
    def ticker(self) -> Ticker:
        """
        获取 24 小时行情推送。

        .. code:: json

            [
                {
                    "c": "10000001",      # 合约 ID
                    "s": "BTCUSD",        # 合约名称
                    "lastPrice": "117400",  # 最新价
                    "priceChange": "200",   # 涨跌额
                    "priceChangePercent": "0.0172",  # 涨跌幅
                    "size": "1250",        # 24h 成交量
                    "value": "147000000", # 24h 成交额
                    "high": "118000",      # 24h 最高价
                    "low": "116500",       # 低价
                    "open": "116800",      # 开盘价
                    "close": "117400",     # 收盘价
                    "indexPrice": "117350", # 指数价
                    "oraclePrice": "117360.12", # 预言机价
                    "openInterest": "50000",    # 持仓量
                    "fundingRate": "0.000234",  # 当前资金费率
                    "fundingTime": "1758240000000", # 上一次结算时间
                    "nextFundingTime": "1758254400000", # 下一次结算时间
                    "bestAskPrice": "117410",    # 卖一价
                    "bestBidPrice": "117400"     # 买一价
                }
            ]
        """
        return self._get("ticker")

    async def initialize(self, *aws: Awaitable["ClientResponse"]) -> None:
        """Populate metadata stores from awaited HTTP responses."""

        for fut in asyncio.as_completed(aws):
            res = await fut
            data = await res.json()
            if data['code'] != 'SUCCESS':
                raise ValueError(f"Unexpected response code: {data}")
            if res.url.path == "/api/v1/public/meta/getMetaData":
                self._apply_metadata(data)
            elif res.url.path == "/api/v1/private/account/getAccountAsset":
                self.balance._onresponse(data)
                self.position._onresponse(data)
            elif res.url.path == "/api/v1/private/order/getActiveOrderPage":
                self.orders._onresponse(data)
            elif res.url.path == "/api/v1/public/quote/getTicker":
                self.ticker._onresponse(data)

    def onmessage(self, msg: Item, ws: ClientWebSocketResponse | None = None) -> None:
        # print(msg)
        channel = (msg.get("channel") or "").lower()
        msg_type = (msg.get("type") or "").lower()

        if msg_type == "ping" and ws is not None:
            payload = {"type": "pong", "time": msg.get("time")}
            asyncio.create_task(ws.send_json(payload))
            return

        if msg_type in {"trade-event", "trade_event", "order-event", "order_event"}:
            self.orders._on_message(msg)
            self.position._on_message(msg)

        if "depth" in channel and msg_type in {"quote-event", "payload"}:
            self.book._on_message(msg)

        if channel.startswith("ticker") and msg_type in {"payload", "quote-event"}:
            self.ticker._on_message(msg)

    def _apply_metadata(self, data: dict[str, Any]) -> None:
        self.app._onresponse(data)
        self.coins._onresponse(data)
        self.detail._onresponse(data)


    @property
    def app(self) -> AppMeta:
        """
        获取全局元数据，如 appName、环境、fee 账户等。

        .. code:: python


        [
            {
                "appName": "edgeX",
                "appEnv": "mainnet",
                "appOnlySignOn": "https://pro.edgex.exchange",
                "feeAccountId": "256105",
                "feeAccountL2Key": "0x70092acf49d535fbb64d99883abda95dcf9a4fc60f494437a3d76f27db0a0f5",
                "poolAccountId": "508126509156794507",
                "poolAccountL2Key": "0x7f2e1e8a572c847086ee93c9b5bbce8b96320aaa69147df1cfca91d5e90bc60",
                "fastWithdrawAccountId": "508126509156794507",
                "fastWithdrawAccountL2Key": "0x7f2e1e8a572c847086ee93c9b5bbce8b96320aaa69147df1cfca91d5e90bc60",
                "fastWithdrawMaxAmount": "100000",
                "fastWithdrawRegistryAddress": "0xBE9a129909EbCb954bC065536D2bfAfBd170d27A",
                "starkExChainId": "0x1",
                "starkExContractAddress": "0xfAaE2946e846133af314d1Df13684c89fA7d83DD",
                "starkExCollateralCoinId": "1000",
                "starkExCollateralCoinName": "USD",
                "starkExCollateralStepSize": "0.000001",
                "starkExCollateralShowStepSize": "0.0001",
                "starkExCollateralIconUrl": "https://static.edgex.exchange/icons/coin/USDT.svg",
                "starkExCollateralStarkExAssetId": "0x2ce625e94458d39dd0bf3b45a843544dd4a14b8169045a3a3d15aa564b936c5",
                "starkExCollateralStarkExResolution": "0xf4240",
                "starkExMaxFundingRate": 12000,
                "starkExOrdersTreeHeight": 64,
                "starkExPositionsTreeHeight": 64,
                "starkExFundingValidityPeriod": 86400,
                "starkExPriceValidityPeriod": 86400,
                "maintenanceReason": "",
            }
        ]
        """
        return self._get("app")
