from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Awaitable
from aiohttp import ClientResponse
from pybotters import DataStore
from pybotters.models.bitget_v2 import BitgetV2DataStore
from ..lib.util import place_to_step

if TYPE_CHECKING:
    from pybotters.typedefs import Item

class Detail(DataStore):
    """Futures instrument metadata store obtained from the futures instrument endpoint."""

    _KEYS = ["symbol"]

    def _transform(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        step_place = entry.get("volume_place", 1)
        tick_place = entry.get("price_place", 1)

        step_size = place_to_step(step_place)
        tick_size = place_to_step(tick_place)

        entry["stepSize"] = step_size
        entry["tickSize"] = tick_size
        # expose snake_case aliases for downstream callers keeping legacy naming
        entry["step_size"] = step_size
        entry["tick_size"] = tick_size

        return entry

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


class Book(DataStore):
    _KEYS = ["t", "s", "S", "p"]

    def _onmessage(self, msg: Item) -> None:
        action = msg["action"]
        inst_type = msg["arg"]["instType"]
        inst_id = msg["arg"]["instId"]

        data_to_insert = []
        data_to_update = []
        data_to_delete = []
        for book in msg["data"]:
            for side in ("asks", "bids"):
                for row in book[side]:
                    converted_row = {
                        "t": inst_type,
                        "s": inst_id,
                        "S": side[0],
                        "p": row[0],
                        "q": row[1],
                    }
                    if action == "snapshot":
                        data_to_insert.append(converted_row)
                    elif converted_row["q"] != "0":
                        data_to_update.append(converted_row)
                    else:
                        data_to_delete.append(converted_row)

        # Cleanup on reconnect
        if action == "snapshot":
            self._find_and_delete({"t": inst_type, "s": inst_id})

        self._insert(data_to_insert)
        self._update(data_to_update)
        self._delete(data_to_delete)
    
    def sorted(
        self, query: Item | None = None, limit: int | None = None
    ) -> dict[str, list[Item]]:
        return self._sorted(
            item_key="side",
            item_asc_key="a",
            item_desc_key="b",
            sort_key="p",
            query=query,
            limit=limit,
        )


class BitgetDataStore(BitgetV2DataStore):

    def _init(self):
        super()._init()
        self._create('detail', datastore_class=Detail)
        self._create("book", datastore_class=Book)
        
    async def initialize(self, *aws: Awaitable[ClientResponse]) -> None:
        for fut in asyncio.as_completed(aws):
            res = await fut
            data = await res.json()
            if res.url.path == '/api/v2/mix/market/contracts':
                self.detail._onresponse(data)
            elif res.url.path == '/api/v2/mix/market/tickers':
                self.ticker._clear()
                tickers = data.get('data', [])
                # 为每个ticker添加额外的字段
                for ticker in tickers:
                    symbol = ticker.get('symbol')
                    ticker['instId'] = symbol
                    ticker['instType'] = 'futures'

                self.ticker._update(tickers)
    
    @property
    def detail(self) -> Detail:
        """
        _key: symbol

        Data Structure:

        .. code:: json

            [
                {
                "symbol": "BTCUSDT",
                "baseCoin": "BTC",
                "quoteCoin": "USDT",
                "buyLimitPriceRatio": "0.9",
                "sellLimitPriceRatio": "0.9",
                "feeRateUpRatio": "0.1",
                "makerFeeRate": "0.0004",
                "takerFeeRate": "0.0006",
                "openCostUpRatio": "0.1",
                "supportMarginCoins": [
                    "USDT"
                ],
                "minTradeNum": "0.01",
                "priceEndStep": "1",
                "volumePlace": "2",
                "stepSize": "0.01",
                "tickSize": "0.1",
                "pricePlace": "1",
                "sizeMultiplier": "0.01",
                "symbolType": "perpetual",
                "minTradeUSDT": "5",
                "maxSymbolOrderNum": "999999",
                "maxProductOrderNum": "999999",
                "maxPositionNum": "150",
                "symbolStatus": "normal",
                "offTime": "-1",
                "limitOpenTime": "-1",
                "deliveryTime": "",
                "deliveryStartTime": "",
                "launchTime": "",
                "fundInterval": "8",
                "minLever": "1",
                "maxLever": "125",
                "posLimit": "0.05",
                "maintainTime": "1680165535278",
                "maxMarketOrderQty": "220",
                "maxOrderQty": "1200"
            }]
        
        """
        return self._get('detail')
    
    @property
    def ticker(self) -> DataStore:
        """
        _KEYS = ["instType", "instId"]

        Data Structure:

        .. code:: json

            [
                {
                    "symbol": "BTCUSDT",
                    "lastPr": "111534.6",
                    "askPr": "111534.6",
                    "bidPr": "111534.5",
                    "bidSz": "23.7924",
                    "askSz": "8.1762",
                    "high24h": "112300",
                    "low24h": "109136.2",
                    "ts": "1759115725508",
                    "change24h": "0.01906",
                    "baseVolume": "35520.11438048",
                    "quoteVolume": "3932280581.066103549",
                    "usdtVolume": "3932280581.066103549",
                    "openUtc": "112100",
                    "changeUtc24h": "-0.00504",
                    "indexPrice": "111587.6090439271505504",
                    "fundingRate": "-0.000002",
                    "holdingAmount": "66775.1917",
                    "deliveryStartTime": null,
                    "deliveryTime": null,
                    "deliveryStatus": "",
                    "open24h": "109448.3",
                    "markPrice": "111537",
                    "instId": "BTCUSDT",
                    "instType": "futures"
                }
            ]
        """
        return self._get('ticker')
    
    @property
    def orders(self) -> DataStore:
        """
        _KEYS = ["instType", "instId", "orderId"]
        .. code:: json

            [
                {
                "instType": "futures",
                "instId": "BTCUSDT",
                "orderId": "1",
                "clientOid": "1",
                "size": "8.0000",
                "newSize": "500.0000",
                "notional": "8.000000",
                "orderType": "market",
                "force": "gtc",
                "side": "buy",
                "fillPrice": "26256.0",
                "tradeId": "1",
                "baseVolume": "0.0003",
                "fillTime": "1695797773286",
                "fillFee": "-0.00000018",
                "fillFeeCoin": "BTC",
                "tradeScope": "T",
                "accBaseVolume": "0.0003",
                "priceAvg": "26256.0",
                "status": "partially_filled",
                "cTime": "1695797773257",
                "uTime": "1695797773326",
                "stpMode": "cancel_taker",
                "feeDetail": [
                    {
                    "feeCoin": "BTC",
                    "fee": "-0.00000018"
                    }
                ],
                "enterPointSource": "WEB"
                }
            ]
        """
        return self._get('orders')
    
    @property
    def book(self) -> DataStore:
        """
        _KEYS = ["t", "s", "S", "p"]

        Data Structure:

        .. code:: json

            [
                {
                    "t": "futures",
                    "s": "BTCUSDT",
                    "S": "a",
                    "p": "111534.6",
                    "q": "8.1762"
                },
                {
                    "t": "futures",
                    "s": "BTCUSDT",
                    "S": "b",
                    "p": "111534.5",
                    "q": "23.7924"
                }
            ]
        """
        return self._get("book")
    
    @property
    def account(self) -> DataStore:
        """
        _KEYS = ["instType", "marginCoin"]

        Data Structure:

        .. code:: json

           [
                {
                    "marginCoin": "USDT",
                    "frozen": "0.00000000",
                    "available": "13.98545761",
                    "maxOpenPosAvailable": "13.98545761",
                    "maxTransferOut": "13.98545761",
                    "equity": "13.98545761",
                    "usdtEquity": "13.985457617660",
                    "crossedRiskRate": "0",
                    "unrealizedPL": "0.000000000000",
                    "unionTotalMargin": "100",
                    "unionAvailable": "20",
                    "unionMm": "15",
                    "assetMode": "union"
                }
            ]
        """
        return self._get("account")

    @property
    def position(self) -> DataStore:
        """
        _KEYS = ["instType", "instId", "posId"]

        Data Structure:

        .. code:: json

           [
                {
                    "posId": "1",
                    "instId": "ETHUSDT",
                    "marginCoin": "USDT",
                    "marginSize": "9.5",
                    "marginMode": "crossed",
                    "holdSide": "short",
                    "posMode": "hedge_mode",
                    "total": "0.1",
                    "available": "0.1",
                    "frozen": "0",
                    "openPriceAvg": "1900",
                    "leverage": 20,
                    "achievedProfits": "0",
                    "unrealizedPL": "0",
                    "unrealizedPLR": "0",
                    "liquidationPrice": "5788.108475905242",
                    "keepMarginRate": "0.005",
                    "marginRate": "0.004416374196",
                    "cTime": "1695649246169",
                    "breakEvenPrice": "24778.97",
                    "totalFee": "1.45",
                    "deductedFee": "0.388",
                    "markPrice": "2500",
                    "assetMode": "union",
                    "uTime": "1695711602568",
                    "autoMargin": "off"
                }
            ]
        """
        return self._get("position")