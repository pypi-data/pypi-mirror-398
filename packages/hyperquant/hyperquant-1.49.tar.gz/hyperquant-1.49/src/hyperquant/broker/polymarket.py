from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from functools import lru_cache
import os
import time
from typing import Any, Iterable, Iterator, Literal, Mapping, Sequence

import json

import aiohttp
import pybotters
import pybotters.ws
import pytz
from web3 import Web3

from .models.polymarket import PolymarketDataStore
from .auth import Auth

DEFAULT_REST_ENDPOINT = "https://clob.polymarket.com"
DEFAULT_WS_ENDPOINT = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
GAMMA_EVENTS_API = "https://gamma-api.polymarket.com/events"
DEFAULT_DATA_ENDPOINT = "https://data-api.polymarket.com"
RTS_DATA_ENDPOINT = "wss://ws-live-data.polymarket.com/"
DEFAULT_BASE_SLUG = "btc-updown-15m"
HOURLY_BITCOIN_BASE_SLUG = "bitcoin-up-or-down"
DEFAULT_INTERVAL = 15 * 60
DEFAULT_WINDOW = 8
TICK_SIZE_CACHE_TTL_SECS = 300
API_NAME = "polymarket"
END_CURSOR = "LTE="
USDC_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ZERO_BYTES32 = "0x0000000000000000000000000000000000000000000000000000000000000000"
ZERO_B32 = ZERO_BYTES32
USDCE_DIGITS = 6
ERC20_BALANCE_OF_ABI = (
    "[{\"constant\":true,\"inputs\":[{\"name\":\"account\",\"type\":\"address\"}],"
    "\"name\":\"balanceOf\",\"outputs\":[{\"name\":\"\",\"type\":\"uint256\"}],"
    "\"payable\":false,\"stateMutability\":\"view\",\"type\":\"function\"}]"
)
NEG_RISK_ADAPTER_ADDRESS = '0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296'

CONDITIONAL_TOKENS_ABI = [
    {
        "inputs": [
            {
                "internalType": "contract IERC20",
                "name": "collateralToken",
                "type": "address",
            },
            {
                "internalType": "bytes32",
                "name": "parentCollectionId",
                "type": "bytes32",
            },
            {
                "internalType": "bytes32",
                "name": "conditionId",
                "type": "bytes32",
            },
            {
                "internalType": "uint256[]",
                "name": "indexSets",
                "type": "uint256[]",
            },
        ],
        "name": "redeemPositions",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

CONDITIONAL_TOKENS_SPLIT_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "CONDITION_ID", "type": "bytes32"},
            {"name": "partition", "type": "uint256[]"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "splitPosition",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "CONDITION_ID", "type": "bytes32"},
            {"name": "partition", "type": "uint256[]"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "mergePositions",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
]
DEFAULT_POLYGON_RPCS = (
    # "https://polygon.llamarpc.com",
    "https://polygon-rpc.com",
    "https://rpc.ankr.com/polygon",
)
SAFE_ABI = [
    {
        "inputs": [],
        "name": "nonce",
        "outputs": [{"internalType": "uint256", "name": "nonce", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
            {"internalType": "uint8", "name": "operation", "type": "uint8"},
            {"internalType": "uint256", "name": "safeTxGas", "type": "uint256"},
            {"internalType": "uint256", "name": "baseGas", "type": "uint256"},
            {"internalType": "uint256", "name": "gasPrice", "type": "uint256"},
            {"internalType": "address", "name": "gasToken", "type": "address"},
            {"internalType": "address", "name": "refundReceiver", "type": "address"},
            {"internalType": "uint256", "name": "_nonce", "type": "uint256"},
        ],
        "name": "getTransactionHash",
        "outputs": [{"internalType": "bytes32", "name": "txHash", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
            {"internalType": "uint8", "name": "operation", "type": "uint8"},
            {"internalType": "uint256", "name": "safeTxGas", "type": "uint256"},
            {"internalType": "uint256", "name": "baseGas", "type": "uint256"},
            {"internalType": "uint256", "name": "gasPrice", "type": "uint256"},
            {"internalType": "address", "name": "gasToken", "type": "address"},
            {"internalType": "address", "name": "refundReceiver", "type": "address"},
            {"internalType": "bytes", "name": "signatures", "type": "bytes"},
        ],
        "name": "execTransaction",
        "outputs": [{"internalType": "bool", "name": "success", "type": "bool"}],
        "stateMutability": "payable",
        "type": "function",
    },
]
_EASTERN_TZ = pytz.timezone("US/Eastern")



from .lib.polymarket.ctfAbi import ctf_abi
from .lib.polymarket.safeAbi import safe_abi


USDCE_DIGITS = 6

def parse_field(value):
    """尝试将字符串 JSON 转为对象，否则原样返回"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value

def _iter_offsets(window: int) -> Iterator[int]:
    yield 0
    for step in range(1, window + 1):
        yield step
        yield -step


def _parse_list(value: Any) -> list[Any]:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    if value is None:
        return []
    return list(value)


def _accepting_orders(market: Mapping[str, Any]) -> bool:
    accepting = market.get("acceptingOrders") or market.get("accepting_orders")
    if isinstance(accepting, str):
        return accepting.lower() == "true"
    return bool(accepting)


def _compose_hourly_slug(base_slug: str, *, now: datetime | None = None) -> str:
    tz_now = now or datetime.now(_EASTERN_TZ)
    if tz_now.tzinfo is None:
        tz_now = _EASTERN_TZ.localize(tz_now)
    else:
        tz_now = tz_now.astimezone(_EASTERN_TZ)

    tz_now = (tz_now + timedelta(seconds=5)).replace(minute=0, second=0, microsecond=0)
    month_str = tz_now.strftime("%B").lower()
    day = tz_now.day
    hour_12 = tz_now.strftime("%I").lstrip("0") or "0"
    am_pm = tz_now.strftime("%p").lower()
    return f"{base_slug}-{month_str}-{day}-{hour_12}{am_pm}-et"


class Polymarket:
    """Polymarket CLOB client with REST helpers, stores and WS subscriptions."""

    def __init__(
        self,
        client: pybotters.Client,
        *,
        rest_api: str | None = None,
        ws_public: str | None = None,
        private_key: str | None = None,
        chain_id: int | None = None,
        signature_type: int | None = None,
        funder: str | None = None
    ) -> None:
        # Logger (per-class, safe default)
        self.logger = logging.getLogger(f"{API_NAME}.{self.__class__.__name__}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s][%(levelname)s][%(name)s] %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        self.client = client
        self.rest_api = (rest_api or DEFAULT_REST_ENDPOINT).rstrip("/")
        self.ws_public = ws_public or DEFAULT_WS_ENDPOINT

        self.chain_id = chain_id or 137
        # Default to POLY_GNOSIS_SAFE (2) to match common proxy flows used in examples/tests.
        # Users can override via constructor.
        self.signature_type = signature_type if signature_type is not None else 2
        self.funder = funder

        self.store = PolymarketDataStore()
        self._ws_public: pybotters.ws.WebSocketApp | None = None
        self._ws_public_ready = asyncio.Event()
        self._ws_personal: pybotters.ws.WebSocketApp | None = None
        self.auth = False
        self._tick_size_cache: dict[str, tuple[str, float]] = {}

        self._ensure_session_entry(private_key=private_key, funder=funder, chain_id=chain_id)

    async def __aenter__(self) -> "Polymarket":
        if self.auth:
            await self.create_or_derive_api_creds()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - 
        await self.aclose()

    async def aclose(self) -> None:
        if self._ws_public is not None:
            with suppress(Exception):
                await self._ws_public.current_ws.close()
            self._ws_public = None
            self._ws_public_ready.clear()

    async def prewarm_connections(
        self,
        endpoints: Sequence[str] | None = None,
        timeout: float = 1.0,
    ) -> None:
        """Pre-warm HTTP connections to reduce first-request latency."""
        if endpoints is None:
            endpoints = ("/ok", "/time")
        session = getattr(self.client, "_session", None)
        if session is None:
            raise RuntimeError("pybotters client session missing")
        for endpoint in endpoints:
            url = f"{self.rest_api}{endpoint}"
            try:
                async with session.get(url, timeout=timeout) as resp:
                    await resp.read()
            except Exception:
                continue

    # ------------------------------------------------------------------
    # Store helpers

    async def update(
        self,
        update_type: Literal[
            "all",
            "markets",
            "book",
            "books",
            "position",
            "orders",
        ] | Sequence[str] = "all",
        *,
        token_ids: Sequence[str] | str | None = None,
        limit: int | None = None,
    ) -> None:
        """Refresh cached data using Polymarket REST endpoints.
        
        update_type 可以是单个字符串或列表，例如:
            update_type='position'
            update_type=['position', 'orders']
        """
        # 统一转为 set
        if isinstance(update_type, str):
            types = {update_type}
        else:
            types = set(update_type)

        include_detail = "all" in types or "detail" in types or "markets" in types
        include_books = "all" in types or "book" in types or "books" in types
        include_position = "all" in types or "position" in types
        include_history_position = "history_position" in types
        include_orders = "all" in types or "orders" in types

        if include_books and token_ids is None:
            raise ValueError("token_ids are required when updating books")

        tasks: list[tuple[str, Any]] = []
        if include_detail:
            params = {"limit": limit} if limit else None
            tasks.append(
                (
                    "detail",
                    asyncio.create_task(
                        self._rest("GET", "/markets", params=params)
                    ),
                )
            )

        if include_books and token_ids is not None:
            body = [{"token_id": tid} for tid in self._token_list(token_ids)]
            tasks.append(
                (
                    "books",
                    asyncio.create_task(
                        self._rest("POST", "/books", json=body)
                    ),
                )
            )
        
        if include_position or include_history_position:
            tasks.append(
                (
                    "position",
                    asyncio.create_task(
                        self.get_mergeable_positions()
                    ),
                )
            )

        if include_orders:
            tasks.append(("orders", asyncio.create_task(self.get_orders())))
        

        if not tasks:
            raise ValueError(f"Unsupported update_type={update_type}")

        results: dict[str, Any] = {}

        keys = [k for k, _ in tasks]
        futs = [f for _, f in tasks]

        done = await asyncio.gather(*futs, return_exceptions=True)

        for key, res in zip(keys, done):
            if isinstance(res, Exception):
                # REST 更新为 best-effort：记录错误但不中断整体流程
                try:
                    logger = getattr(self, "logger", None)
                    if logger:
                        logger.warning(f"[update] {key} failed: {res}", exc_info=True)
                    else:
                        print(f"[update] {key} failed: {res}")
                except Exception:
                    pass
                continue
            results[key] = res


        if "books" in results:
            entries = results["books"].get("data") or results["books"]
            for entry in entries or []:
                message = {
                    "event_type": "book",
                    "asset_id": entry.get("asset_id") or entry.get("token_id"),
                    "bids": entry.get("bids"),
                    "asks": entry.get("asks"),
                }
                self.store.book._on_message(message)
        
        if "position" in results or "history_position" in results:
            data = results["position"]
            self.store.position._on_response(data)

        if "orders" in results:
            orders = results["orders"]
            self.store.orders._on_response(orders)

    async def sub_rts_prices(
        self,
        symbols: Sequence[str] | str | None = None,
        *,
        source: Literal["chainlink", "binance"] = "chainlink",
        server_filter: bool = False,
    ) -> pybotters.ws.WebSocketApp:
        """Subscribe to Polymarket RTDS prices (Chainlink or Binance sources).

        Parameters
        ----------
        symbols
            Requested symbols (Chainlink prefers ``eth/usd`` format, Binance
            uses ``ethusdt``).
        source
            Either ``"chainlink"`` (default) or ``"binance"``.
        server_filter
            When ``True`` the request payload includes the filter exactly as the
            docs specify (e.g. ``{"symbol":"btc/usd"}``). In practice the
            server sometimes stops streaming after returning the first snapshot
            when filters are present, so the default behaviour is to subscribe
            to the full feed and filter locally.
        """

        if isinstance(symbols, str):
            requested = [symbols]
        elif symbols:
            requested = list(symbols)
        else:
            requested = []

        target_symbols = {s.lower() for s in requested if s}

        if source == "chainlink":
            topic = "crypto_prices_chainlink"
            sub_type = "*"
            if server_filter and target_symbols:
                if len(target_symbols) == 1:
                    filters = json.dumps({"symbol": next(iter(target_symbols))})
                else:
                    filters = json.dumps({"symbols": sorted(target_symbols)})
            else:
                filters = None
        else:
            topic = "crypto_prices"
            sub_type = "update"
            filters = None
            if server_filter and target_symbols:
                filters = ",".join(sorted(target_symbols))

        subscription: dict[str, Any] = {"topic": topic, "type": sub_type}
        if filters:
            subscription["filters"] = filters

        payload = {
            "action": "subscribe",
            "subscriptions": [subscription],
        }

        def callback(msg, ws):
            if not msg:
                return
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                return

            payload = data.get("payload") or {}
            symbol = str(payload.get("symbol") or "").lower()
            if (not server_filter) and target_symbols and symbol and symbol not in target_symbols:
                return

            self.store.onmessage(data, ws)

        wsapp = self.client.ws_connect(
            RTS_DATA_ENDPOINT,
            send_json=payload,
            hdlr_str=callback,
            heartbeat=5,
        )

        await wsapp._event.wait()
        return wsapp


    async def sub_books(
        self,
        token_ids: Sequence[str] | str,
        wsapp: pybotters.ws.WebSocketApp | None = None,
        only_bbo: bool = False,
        with_trades: bool = False
    ) -> pybotters.ws.WebSocketApp:
        """Subscribe to public order-book updates for the provided token ids."""

        tokens = self._token_list(token_ids)
        payload = {"type": "market", "assets_ids": tokens}
        if wsapp:
            await wsapp.current_ws.send_json(payload)
        hdrl_json = self.store.onmessage_for_bbo if only_bbo else self.store.onmessage
        hd_lst = [hdrl_json]
        if with_trades:
            hd_lst.append(self.store.onmessage_for_last_trade)

        self._ws_public = self.client.ws_connect(
            self.ws_public,
            send_json=payload,
            hdlr_json=hd_lst
        )
        await self._ws_public._event.wait()
        return self._ws_public
    
    async def sub_personal(
        self,
        callback: Any = None,
        markets: Sequence[str] | None = None,
        rest_sync: bool = True,
        rest_order_sync_interval: int = 5,
        rest_position_sync_interval: int = 8,
    ) -> pybotters.ws.WebSocketApp:
        """Subscribe to personal updates (requires authentication)."""

        creds = self._api_creds()
        if not creds:
            raise RuntimeError("Polymarket API credentials are required for personal subscriptions")

        # 记录 position store 最后更新时间
        last_position_update = time.time()
        
        def _handler(message, ws=None):
            nonlocal last_position_update
            self.store.onmessage(message, ws)
            # 检测是否是 position 相关消息
            if isinstance(message, dict) and message.get('event_type') in ('order', 'trade'):
                last_position_update = time.time()
            if callback:
                callback(message, ws)

        effective_cb = _handler if callback else self.store.onmessage

        api_key = creds.get("api_key")
        api_secret = creds.get("api_secret")
        api_passphrase = creds.get("api_passphrase")
        if not api_key or not api_secret or not api_passphrase:
            raise RuntimeError("Polymarket API key/secret/passphrase missing; call create_or_derive_api_creds")

        auth = {"apiKey": api_key, "secret": api_secret, "passphrase": api_passphrase}
        payload = {"markets": list(markets or []), "type": "user", "auth": auth}

        # 在开始前用rest_api同步持仓
        await self.update('position')

        # 后台任务：3秒无更新则同步持仓
        async def _rest_sync_watchdog():
            nonlocal last_position_update
            last_orders_update = time.time()
            while True:
                await asyncio.sleep(1)
                now = time.time()
                # position: 6秒无更新则同步
                if now - last_position_update > rest_position_sync_interval:
                    try:
                        await self.update('position')
                        last_position_update = now
                    except Exception:
                        pass
                # orders: 每3秒同步一次
                if now - last_orders_update > rest_order_sync_interval:
                    try:
                        await self.update('orders')
                        last_orders_update = now
                    except Exception:
                        pass
        
        if rest_sync:
            asyncio.create_task(_rest_sync_watchdog())

        # 使用 send_json 参数，这样重连后会自动重新订阅
        self._ws_personal = self.client.ws_connect(
            "wss://ws-subscriptions-clob.polymarket.com/ws/user",
            send_json=payload,
            hdlr_json=effective_cb,
            heartbeat=30,
            auth=None,
        )
        await self._ws_personal._event.wait()


        return self._ws_personal
    
    async def sub_trades(self, slug: str):
        """订阅activate trades"""
        payload = {
            "action": "subscribe",
            "subscriptions": [
                {
                    "topic": "activity",
                    "type": "orders_matched",
                    "filters":  json.dumps({"event_slug": slug}, separators=(',', ':'))
                }
            ]
        }
        print(payload)
        def callback(msg, ws):
            if not msg:
                return
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                return
            
            self.store.onmessage(data, ws)

        # 使用 send_json 参数，重连后自动重新订阅
        wsapp = self.client.ws_connect(
            RTS_DATA_ENDPOINT,
            send_json=payload,
            hdlr_str=callback,
            heartbeat=5
        )
        await wsapp._event.wait()
        return wsapp
    

   

    # ------------------------------------------------------------------
    # Public REST endpoints

    async def get_markets(self, **params: Any) -> Any:
        return await self._rest("GET", "/markets", params=params or None)

    async def get_market(self, market_id: str) -> Any:
        return await self._rest("GET", f"/markets/{market_id}")

    async def get_market_by_slug(self, slug: str) -> Any:
        """Fetch a market using its human-readable slug.
        https://docs.polymarket.com/api-reference/markets/get-market-by-slug
        """
        market:dict = await self._rest("GET", f"/slug/{slug}", host='https://gamma-api.polymarket.com/markets')
        market = {k: parse_field(v) for k, v in market.items()}
        return market
    
    async def get_order_book(self, token_id: str) -> Any:
        return await self._rest("GET", "/book", params={"token_id": token_id})

    async def get_order_books(self, token_ids: Sequence[str] | str) -> Any:
        body = [{"token_id": tid} for tid in self._token_list(token_ids)]
        return await self._rest("POST", "/books", json=body)

    async def get_midpoint(self, token_id: str) -> Any:
        return await self._rest("GET", "/midpoint", params={"token_id": token_id})

    async def get_midpoints(self, token_ids: Sequence[str] | str) -> Any:
        body = [{"token_id": tid} for tid in self._token_list(token_ids)]
        return await self._rest("POST", "/midpoints", json=body)

    async def get_price(self, token_id: str, side: str) -> Any:
        return await self._rest("GET", "/price", params={"token_id": token_id, "side": side})

    async def get_prices(self, requests: Iterable[Mapping[str, str]]) -> Any:
        body = [dict(req) for req in requests]
        return await self._rest("POST", "/prices", json=body)

    async def get_spread(self, token_id: str) -> Any:
        return await self._rest("GET", "/spread", params={"token_id": token_id})

    async def get_spreads(self, token_ids: Sequence[str] | str) -> Any:
        body = [{"token_id": tid} for tid in self._token_list(token_ids)]
        return await self._rest("POST", "/spreads", json=body)

    async def get_last_trade_price(self, token_id: str) -> Any:
        return await self._rest("GET", "/last-trade-price", params={"token_id": token_id})

    async def get_last_trades_prices(self, token_ids: Sequence[str] | str) -> Any:
        body = [{"token_id": tid} for tid in self._token_list(token_ids)]
        return await self._rest("POST", "/last-trades-prices", json=body)

    async def get_tick_size(self, token_id: str) -> Any:
        return await self._rest("GET", "/tick-size", params={"token_id": token_id})

    async def get_neg_risk(self, token_id: str) -> Any:
        return await self._rest("GET", "/neg-risk", params={"token_id": token_id})

    async def get_fee_rate(self, token_id: str) -> Any:
        return await self._rest("GET", "/fee-rate", params={"token_id": token_id})

    # ------------------------------------------------------------------
    # Credential management (Level 1 / Level 2)

    async def create_api_key(self, nonce: int | None = None) -> dict[str, Any]:
        params = {"nonce": nonce} if nonce is not None else None
        data = await self._rest("POST", "/auth/api-key", params=params)
        self._store_api_creds(data)
        return data

    async def derive_api_key(self, nonce: int | None = None) -> dict[str, Any]:
        params = {"nonce": nonce} if nonce is not None else None
        data = await self._rest("GET", "/auth/derive-api-key", params=params)
        self._store_api_creds(data)
        return data

    async def create_or_derive_api_creds(self, nonce: int | None = None) -> dict[str, Any]:
        try:
            return await self.derive_api_key(nonce)
        except Exception:
            return await self.create_api_key(nonce)

    async def get_api_keys(self) -> Any:
        return await self._rest("GET", "/auth/api-keys")

    async def delete_api_key(self) -> Any:
        return await self._rest("DELETE", "/auth/api-key")

    async def get_closed_only_mode(self) -> Any:
        return await self._rest("GET", "/auth/ban-status/closed-only")

    # ------------------------------------------------------------------
    # Trading helpers (Level 2)

    async def post_order(
        self,
        signed_order: Mapping[str, Any],
        *,
        order_type: str = "GTC",
        owner: str | None = None,
    ) -> Any:
        """Low-level publish for an already-signed order.

        Prefer ``place_order`` for a compact, user-friendly API.
        """
        payload = {
            "order": dict(signed_order),
            "owner": self._owner_key(owner),
            "orderType": order_type,
        }
        return await self._rest("POST", "/order", json=payload)

    # ------------------------------------------------------------------
    # Compact order placement (py_clob_client-like)

    @staticmethod
    def _round_down(x: float, sig_digits: int) -> float:
        from math import floor

        return floor(x * (10**sig_digits)) / (10**sig_digits)

    @staticmethod
    def _round_normal(x: float, sig_digits: int) -> float:
        return round(x * (10**sig_digits)) / (10**sig_digits)

    @staticmethod
    def _round_up(x: float, sig_digits: int) -> float:
        from math import ceil

        return ceil(x * (10**sig_digits)) / (10**sig_digits)

    @staticmethod
    def _decimal_places(x: float) -> int:
        from decimal import Decimal

        return abs(Decimal(x.__str__()).as_tuple().exponent)

    @classmethod
    def _to_token_decimals(cls, x: float) -> int:
        f = (10**6) * x
        if cls._decimal_places(f) > 0:
            f = cls._round_normal(f, 0)
        return int(f)

    @staticmethod
    def _contracts(chain_id: int, neg_risk: bool = False) -> dict[str, str]:
        """Minimal contract config (avoid external deps)."""
        cfg = {
            False: {
                137: {
                    "exchange": "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",
                    "collateral": USDC_CONTRACT,
                    "conditional_tokens": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",
                    "neg_risk_adapter": None,
                },
                80002: {
                    "exchange": "0xdFE02Eb6733538f8Ea35D585af8DE5958AD99E40",
                    "collateral": "0x9c4e1703476e875070ee25b56a58b008cfb8fa78",
                    "conditional_tokens": "0x69308FB512518e39F9b16112fA8d994F4e2Bf8bB",
                    "neg_risk_adapter": None,
                },
            },
            True: {
                137: {
                    "exchange": "0xC5d563A36AE78145C45a50134d48A1215220f80a",
                    "collateral": USDC_CONTRACT,
                    "conditional_tokens": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",
                    "neg_risk_adapter": "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296",
                },
                80002: {
                    "exchange": "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296",
                    "collateral": "0x9c4e1703476e875070ee25b56a58b008cfb8fa78",
                    "conditional_tokens": "0x69308FB512518e39F9b16112fA8d994F4e2Bf8bB",
                    "neg_risk_adapter": None,
                },
            },
        }
        try:
            return cfg[bool(neg_risk)][int(chain_id)]
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Unsupported chain_id={chain_id} for Polymarket") from e

    @staticmethod
    def _rounding_for_tick(tick_size: str | float) -> tuple[int, int, int]:
        """Return (price_digits, size_digits, amount_digits) for tick_size."""
        ts = str(tick_size)
        mapping = {
            "0.1": (1, 2, 3),
            "0.01": (2, 2, 4),
            "0.001": (3, 2, 5),
            "0.0001": (4, 2, 6),
        }
        return mapping.get(ts, (2, 2, 4))

    async def place_order(
        self,
        *,
        token_id: str,
        side: str,
        price: float,
        size: float,
        order_type: Literal["GTC", 'FOK'] = "GTC",
        tick_size: str | float | None = None,
        fee_rate_bps: int | None = None,
        expiration: int | None = None,
        taker: str = ZERO_ADDRESS,
        neg_risk: bool = False,
        owner: str | None = None,
        nonce: int | None = None,
    ) -> Any:
        """Create, sign and submit an order with a compact interface.

        Parameters
        - token_id: outcome token id
        - side: 'BUY' | 'SELL'
        - price: float price
        - size: float size (in outcome tokens)
        - order_type: 'GTC' (default) or other server-accepted types
        - fee_rate_bps: optional fee bps; defaults to market fee
        - expiration: unix seconds; defaults to 0 (no expiry)
        - taker: zero address by default (public order)
        - neg_risk: whether market is negative risk
        - owner: API key owner (defaults to current credentials)
        - nonce: onchain nonce, default 0
        """

        if price <= 0:
            raise ValueError("price must be positive; use place_market_order for market orders")

        # Ensure L2 creds exist
        if not self._api_creds():
            raise RuntimeError("Polymarket API credentials missing; call create_or_derive_api_creds first")

        private_key, maker_addr, signer_addr = self._get_signing_context()
        signed_dict = await self._build_signed_order(
            private_key=private_key,
            maker_addr=maker_addr,
            signer_addr=signer_addr,
            token_id=token_id,
            side=side,
            price=price,
            size=size,
            tick_size=tick_size,
            fee_rate_bps=fee_rate_bps,
            expiration=expiration,
            taker=taker,
            neg_risk=neg_risk,
            nonce=nonce,
        )

        # Submit (use aiohttp session directly with HMAC headers for performance)
        payload = {
            "order": signed_dict,
            "owner": self._owner_key(owner),
            "orderType": order_type,
        }
        return await self._signed_request_via_session("POST", "/order", payload)

    async def place_market_order(
        self,
        *,
        token_id: str,
        side: str,
        amount: float,
        order_type: Literal["FOK", "GTC", "FAK", "GTD"] = "FOK",
        price: float | None = None,
        tick_size: str | float | None = None,
        fee_rate_bps: int | None = None,
        taker: str = ZERO_ADDRESS,
        neg_risk: bool = False,
        owner: str | None = None,
        nonce: int | None = None,
    ) -> Any:
        """Create, sign and submit a market order similar to ``py_clob_client``.

        BUY orders treat ``amount`` as collateral (USDC); SELL orders treat it as shares.
        """

        if amount <= 0:
            raise ValueError("amount must be greater than 0 for market orders")

        if not self._api_creds():
            raise RuntimeError("Polymarket API credentials missing; call create_or_derive_api_creds first")

        private_key, maker_addr, signer_addr = self._get_signing_context()
        owner_key = self._owner_key(owner)
        order_type_str = (order_type or "FOK").upper()

        if price is None or price <= 0:
            price = await self._calculate_market_price(
                token_id=token_id,
                side=side,
                amount=amount,
                order_type=order_type_str,
            )

        signed_dict = await self._build_signed_market_order(
            private_key=private_key,
            maker_addr=maker_addr,
            signer_addr=signer_addr,
            token_id=token_id,
            side=side,
            amount=amount,
            price=price,
            tick_size=tick_size,
            fee_rate_bps=fee_rate_bps,
            taker=taker,
            neg_risk=neg_risk,
            nonce=nonce,
        )

        payload = {
            "order": signed_dict,
            "owner": owner_key,
            "orderType": order_type_str,
        }
        return await self._signed_request_via_session("POST", "/order", payload)

    async def _calculate_market_price(
        self,
        *,
        token_id: str,
        side: str,
        amount: float,
        order_type: str,
    ) -> float:
        side_flag = side.upper()
        if side_flag not in {"BUY", "SELL"}:
            raise ValueError("side must be 'BUY' or 'SELL'")
        if amount <= 0:
            raise ValueError("amount must be greater than 0 for market pricing")

        book = await self.get_order_book(token_id)
        if not isinstance(book, Mapping):
            raise RuntimeError("Polymarket order book unavailable for market order")

        key = "asks" if side_flag == "BUY" else "bids"
        raw_levels = book.get(key) or []
        levels: list[tuple[float, float]] = []
        for lvl in raw_levels:
            try:
                price = float(lvl.get("price"))
                size = float(lvl.get("size"))
            except (TypeError, ValueError):
                continue
            if price is None or size is None:
                continue
            levels.append((price, size))

        if not levels:
            raise RuntimeError(f"Polymarket market order has no {key} liquidity")

        total = 0.0
        if side_flag == "BUY":
            for price, size in reversed(levels):
                total += price * size
                if total >= amount:
                    return price
        else:
            for price, size in reversed(levels):
                total += size
                if total >= amount:
                    return price

        if (order_type or "FOK").upper() == "FOK":
            raise RuntimeError("Polymarket market order exceeds available liquidity")

        return levels[0][0]

    async def _signed_request_via_session(
        self, method: str, path: str, body: Mapping[str, Any] | list[Any] | None
    ) -> Any:
        import time, base64, hmac, hashlib
        from eth_account import Account as _A
        import aiohttp

        method = method.upper()
        session: aiohttp.ClientSession = getattr(self.client, "_session", None)
        if session is None:
            raise RuntimeError("pybotters client session missing")
        creds = getattr(session, "_polymarket_api_creds", None)
        if not creds:
            raise RuntimeError("Polymarket API creds missing; call create_or_derive_api_creds")
        api_key = creds.get("api_key")
        api_secret = creds.get("api_secret")
        api_passphrase = creds.get("api_passphrase")

        entry = getattr(session, "_apis", {}).get(API_NAME, [])
        private_key = entry[0] if entry else None
        addr = _A.from_key(private_key).address if private_key else None

        ts = int(time.time())
        request_path = path
        url = f"{self.rest_api}{request_path}"
        payload_obj = dict(body) if isinstance(body, dict) else body
        if payload_obj is None:
            serialized = ""
        elif isinstance(payload_obj, str):
            serialized = payload_obj
        else:
            serialized = json.dumps(payload_obj, separators=(",", ":"), ensure_ascii=False)
        secret_bytes = base64.urlsafe_b64decode(api_secret)
        msg = f"{ts}{method}{request_path}{serialized}"
        sig = hmac.new(secret_bytes, msg.encode("utf-8"), hashlib.sha256).digest()
        sign_b64 = base64.urlsafe_b64encode(sig).decode("utf-8")

        headers = {
            "POLY_ADDRESS": addr,
            "POLY_SIGNATURE": sign_b64,
            "POLY_TIMESTAMP": str(ts),
            "POLY_API_KEY": api_key,
            "POLY_PASSPHRASE": api_passphrase,
            "Content-Type": "application/json",
        }

        async with session.request(method, url, headers=headers, data=(serialized or None)) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(f"Polymarket {method} {path} failed: {resp.status} {text}")
            try:
                return await resp.json()
            except Exception:
                return await resp.text()

    def _get_signing_context(self) -> tuple[str, str, str]:
        from eth_account import Account as _A

        session = getattr(self.client, "_session", None)
        apis = getattr(session, "_apis", {}) if session else {}
        entry = list(apis.get(API_NAME, [])) if isinstance(apis, dict) else []
        private_key = entry[0] if entry and entry[0] else None
        if not private_key:
            raise RuntimeError("Polymarket private key not configured in apis.json")
        if not str(private_key).startswith("0x"):
            private_key = f"0x{private_key}"
            try:
                # Normalize cached session key to avoid repeated normalization work
                if session and isinstance(apis, dict):
                    apis[API_NAME][0] = private_key
            except Exception:
                pass

        cache_key = (private_key, self.funder)
        cached = getattr(self, "_signing_ctx_cache", None)
        if cached and cached.get("key") == cache_key:
            return cached["ctx"]

        signer_addr = _A.from_key(private_key).address
        maker_addr = self.funder or signer_addr
        ctx = (private_key, maker_addr, signer_addr)
        self._signing_ctx_cache = {"key": cache_key, "ctx": ctx}
        return ctx

    async def _build_signed_order(
        self,
        *,
        private_key: str,
        maker_addr: str,
        signer_addr: str,
        token_id: str,
        side: str,
        price: float,
        size: float,
        tick_size: str | float | None,
        fee_rate_bps: int | None,
        expiration: int | None,
        taker: str,
        neg_risk: bool,
        nonce: int | None,
    ) -> dict[str, Any]:
        side = side.upper()

        tick = await self._resolve_tick_size(token_id, tick_size)
        fee_bps = await self._resolve_fee_rate(token_id, fee_rate_bps)

        price_d, size_d, amt_d = self._rounding_for_tick(tick)
        price = float(self._round_normal(price, price_d))

        if side == "BUY":
            taker_amt_raw = self._round_down(float(size), size_d)
            maker_amt_raw = taker_amt_raw * price
            if self._decimal_places(maker_amt_raw) > amt_d:
                tmp = self._round_up(maker_amt_raw, amt_d + 4)
                maker_amt_raw = tmp if self._decimal_places(tmp) <= amt_d else self._round_down(tmp, amt_d)
        elif side == "SELL":
            maker_amt_raw = self._round_down(float(size), size_d)
            taker_amt_raw = maker_amt_raw * price
            if self._decimal_places(taker_amt_raw) > amt_d:
                tmp = self._round_up(taker_amt_raw, amt_d + 4)
                taker_amt_raw = tmp if self._decimal_places(tmp) <= amt_d else self._round_down(tmp, amt_d)
        else:
            raise ValueError("side must be 'BUY' or 'SELL'")

        maker_amount = self._to_token_decimals(maker_amt_raw)
        taker_amount = self._to_token_decimals(taker_amt_raw)

        contract = self._contracts(self.chain_id, neg_risk)
        side_flag = 0 if side == "BUY" else 1
        sig_type = int(self.signature_type)

        try:
            return Auth.sign_polymarket_order2(
                private_key=private_key,
                chain_id=self.chain_id,
                exchange_address=contract["exchange"],
                order={
                    "maker": maker_addr,
                    "signer": signer_addr,
                    "taker": taker or ZERO_ADDRESS,
                    "tokenId": str(token_id),
                    "makerAmount": int(maker_amount),
                    "takerAmount": int(taker_amount),
                    "expiration": int(expiration or 0),
                    "nonce": int(nonce or 0),
                    "feeRateBps": int(fee_bps or 0),
                    "side": side_flag,
                    "signatureType": sig_type,
                },
            )
        except RuntimeError:
            # Fallback when coincurve is unavailable
            return Auth.sign_polymarket_order(
                private_key=private_key,
                chain_id=self.chain_id,
                exchange_address=contract["exchange"],
                order={
                    "maker": maker_addr,
                    "signer": signer_addr,
                    "taker": taker or ZERO_ADDRESS,
                    "tokenId": str(token_id),
                    "makerAmount": int(maker_amount),
                    "takerAmount": int(taker_amount),
                    "expiration": int(expiration or 0),
                    "nonce": int(nonce or 0),
                    "feeRateBps": int(fee_bps or 0),
                    "side": side_flag,
                    "signatureType": sig_type,
                },
            )

    async def _build_signed_market_order(
        self,
        *,
        private_key: str,
        maker_addr: str,
        signer_addr: str,
        token_id: str,
        side: str,
        amount: float,
        price: float,
        tick_size: str | float | None,
        fee_rate_bps: int | None,
        taker: str,
        neg_risk: bool,
        nonce: int | None,
    ) -> dict[str, Any]:
        side = side.upper()
        tick = await self._resolve_tick_size(token_id, tick_size)
        fee_bps = await self._resolve_fee_rate(token_id, fee_rate_bps)

        price_d, size_d, amt_d = self._rounding_for_tick(tick)
        price = float(self._round_normal(price, price_d))
        if price <= 0:
            raise ValueError("market price must be positive")

        amt = float(amount)
        if amt <= 0:
            raise ValueError("amount must be greater than 0")

        maker_amt_raw = self._round_down(amt, size_d)
        if maker_amt_raw <= 0:
            raise ValueError("amount too small for current tick size")

        if side == "BUY":
            taker_amt_raw = maker_amt_raw / price
        elif side == "SELL":
            taker_amt_raw = maker_amt_raw * price
        else:
            raise ValueError("side must be 'BUY' or 'SELL'")

        if self._decimal_places(taker_amt_raw) > amt_d:
            tmp = self._round_up(taker_amt_raw, amt_d + 4)
            taker_amt_raw = tmp if self._decimal_places(tmp) <= amt_d else self._round_down(tmp, amt_d)

        maker_amount = self._to_token_decimals(maker_amt_raw)
        taker_amount = self._to_token_decimals(taker_amt_raw)

        contract = self._contracts(self.chain_id, neg_risk)
        side_flag = 0 if side == "BUY" else 1
        sig_type = int(self.signature_type)

        try:
            return Auth.sign_polymarket_order2(
                private_key=private_key,
                chain_id=self.chain_id,
                exchange_address=contract["exchange"],
                order={
                    "maker": maker_addr,
                    "signer": signer_addr,
                    "taker": taker or ZERO_ADDRESS,
                    "tokenId": str(token_id),
                    "makerAmount": int(maker_amount),
                    "takerAmount": int(taker_amount),
                    "expiration": 0,
                    "nonce": int(nonce or 0),
                    "feeRateBps": int(fee_bps or 0),
                    "side": side_flag,
                    "signatureType": sig_type,
                },
            )
        except RuntimeError:
            # Fallback when coincurve is unavailable
            return Auth.sign_polymarket_order(
                private_key=private_key,
                chain_id=self.chain_id,
                exchange_address=contract["exchange"],
                order={
                    "maker": maker_addr,
                    "signer": signer_addr,
                    "taker": taker or ZERO_ADDRESS,
                    "tokenId": str(token_id),
                    "makerAmount": int(maker_amount),
                    "takerAmount": int(taker_amount),
                    "expiration": 0,
                    "nonce": int(nonce or 0),
                    "feeRateBps": int(fee_bps or 0),
                    "side": side_flag,
                    "signatureType": sig_type,
                },
            )

    async def _resolve_tick_size(self, token_id: str, tick_size: str | float | None) -> str:
        if tick_size is not None:
            return str(tick_size)
        cached = self._tick_size_cache.get(token_id)
        now = time.time()
        if cached and (now - cached[1]) < TICK_SIZE_CACHE_TTL_SECS:
            return cached[0]
        tick_resp = await self.get_tick_size(token_id)
        if isinstance(tick_resp, dict):
            resolved = str(
                tick_resp.get("minimum_tick_size") or tick_resp.get("tick_size") or "0.01"
            )
        else:
            resolved = str(tick_resp)
        self._tick_size_cache[token_id] = (resolved, now)
        return resolved

    async def _resolve_fee_rate(self, token_id: str, fee_rate_bps: int | None) -> int:
        if fee_rate_bps is not None:
            return int(fee_rate_bps)
        return 0
        

    async def _signed_request_via_session(
        self, method: str, path: str, body: Mapping[str, Any] | list[Any] | None
    ) -> Any:
        import time, base64, hmac, hashlib
        from eth_account import Account as _A
        import aiohttp

        method = method.upper()
        session: aiohttp.ClientSession = getattr(self.client, "_session", None)
        if session is None:
            raise RuntimeError("pybotters client session missing")
        creds = getattr(session, "_polymarket_api_creds", None)
        if not creds:
            raise RuntimeError("Polymarket API creds missing; call create_or_derive_api_creds")
        api_key = creds.get("api_key")
        api_secret = creds.get("api_secret")
        api_passphrase = creds.get("api_passphrase")

        # Reuse signing context cache
        private_key, _, signer_addr = self._get_signing_context()

        cache_key = (api_key, api_secret, api_passphrase, private_key)
        cached = getattr(self, "_rest_sign_cache", None)
        if cached and cached.get("key") == cache_key:
            secret_bytes = cached["secret"]
        else:
            secret_bytes = base64.urlsafe_b64decode(api_secret)
            self._rest_sign_cache = {"key": cache_key, "secret": secret_bytes}

        ts = int(time.time())
        request_path = path
        url = f"{self.rest_api}{request_path}"
        if isinstance(body, dict):
            payload_obj = dict(body)
        else:
            payload_obj = body
        if payload_obj is None:
            serialized = ""
        elif isinstance(payload_obj, str):
            serialized = payload_obj
        else:
            serialized = json.dumps(payload_obj, separators=(",", ":"), ensure_ascii=False)
        msg = f"{ts}{method}{request_path}{serialized}"
        sig = hmac.new(secret_bytes, msg.encode("utf-8"), hashlib.sha256).digest()
        sign_b64 = base64.urlsafe_b64encode(sig).decode("utf-8")

        headers = {
            "POLY_ADDRESS": signer_addr,
            "POLY_SIGNATURE": sign_b64,
            "POLY_TIMESTAMP": str(ts),
            "POLY_API_KEY": api_key,
            "POLY_PASSPHRASE": api_passphrase,
            "Content-Type": "application/json",
        }

        async with session.request(method, url, headers=headers, data=(serialized or None)) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(f"Polymarket {method} {path} failed: {resp.status} {text}")
            try:
                return await resp.json()
            except Exception:
                return await resp.text()

    async def post_orders(
        self,
        orders: Iterable[tuple[Mapping[str, Any], str]],
        *,
        owner: str | None = None,
    ) -> Any:
        owner_key = self._owner_key(owner)
        body = [
            {
                "order": dict(order),
                "owner": owner_key,
                "orderType": order_type,
            }
            for order, order_type in orders
        ]
        return await self._signed_request_via_session("POST", "/orders", body)

    async def place_orders(
        self,
        items: Iterable[Mapping[str, Any]],
        *,
        owner: str | None = None,
    ) -> Any:
        """Create, sign and submit multiple orders.

        Each item must include: token_id, side, price, size
        Optional per-item: tick_size, fee_rate_bps, expiration, taker, neg_risk, nonce, order_type
        .. code:: json

            [
                {
                    "errorMsg": "",
                    "orderID": "0x4b9c3ee4dee8653f15f716653e8ac83f0a086a38597e6ec4b72be2389c79b8b4",
                    "takingAmount": "",
                    "makingAmount": "",
                    "status": "live",
                    "success": true
                },
                {
                    "errorMsg": "",
                    "orderID": "0xb3507e9fda9541c3e038afcb4f24b96efcfa667d46cf5e9e52c41620711818df",
                    "takingAmount": "",
                    "makingAmount": "",
                    "status": "live",
                    "success": true
                }
            ]
        """
        private_key, maker_addr, signer_addr = self._get_signing_context()
        owner_key = self._owner_key(owner)

        result_body: list[dict[str, Any]] = []
        for it in items:
            token_id = str(it["token_id"])
            side = str(it["side"]).upper()
            price = float(it["price"])
            size = float(it["size"])
            order_type = str(it.get("order_type", "GTC"))
            tick_size = it.get("tick_size")
            fee_rate_bps = it.get("fee_rate_bps")
            expiration = it.get("expiration")
            taker = it.get("taker", ZERO_ADDRESS)
            neg_risk = bool(it.get("neg_risk", False))
            nonce = it.get("nonce")

            signed = await self._build_signed_order(
                private_key=private_key,
                maker_addr=maker_addr,
                signer_addr=signer_addr,
                token_id=token_id,
                side=side,
                price=price,
                size=size,
                tick_size=tick_size,
                fee_rate_bps=fee_rate_bps,
                expiration=expiration,
                taker=taker,
                neg_risk=neg_risk,
                nonce=nonce,
            )

            result_body.append(
                {
                    "order": signed,
                    "owner": owner_key,
                    "orderType": order_type,
                }
            )

        return await self._signed_request_via_session("POST", "/orders", result_body)

    async def cancel(self, order_id: str) -> Any:
        """
        {'not_canceled': {}, 'canceled': ['0xb3507e9fda9541c3e038afcb4f24b96efcfa667d46cf5e9e52c41620711818df', '0x4b9c3ee4dee8653f15f716653e8ac83f0a086a38597e6ec4b72be2389c79b8b4']}
        """
        return await self._signed_request_via_session("DELETE", "/order", {"orderID": order_id})

    async def cancel_orders(self, order_ids: Sequence[str]) -> Any:
        """
        {'not_canceled': {}, 'canceled': ['0xb3507e9fda9541c3e038afcb4f24b96efcfa667d46cf5e9e52c41620711818df', '0x4b9c3ee4dee8653f15f716653e8ac83f0a086a38597e6ec4b72be2389c79b8b4']}
        """
        return await self._signed_request_via_session("DELETE", "/orders", list(order_ids))

    async def cancel_all(self) -> Any:
        """
        {'not_canceled': {}, 'canceled': ['0xb3507e9fda9541c3e038afcb4f24b96efcfa667d46cf5e9e52c41620711818df', '0x4b9c3ee4dee8653f15f716653e8ac83f0a086a38597e6ec4b72be2389c79b8b4']}
        """
        return await self._signed_request_via_session("DELETE", "/cancel-all", None)

    async def cancel_market_orders(self, market: str = "", asset_id: str = "") -> Any:
        body = {"market": market, "asset_id": asset_id}
        return await self._signed_request_via_session("DELETE", "/cancel-market-orders", body)

    async def get_order(self, order_id: str) -> Any:
        """
            {
                "id": "0x4c47db1458b36d535106cdb450f20a27f4ec6ba458b9a86dc4a69afb8a81215c",
                "status": "MATCHED",
                "owner": "d6dba4d1-b21d-4272-ab9a-5ef8e8bf23bb",
                "maker_address": "0x03C3B0236c5a01051381482E77f2210349073A1d",
                "market": "0x42dc093dfcdd9ba2962baab1bb5de6c7209b14ed5d3d1f7d19dec12c14cbb489",
                "asset_id": "16982568567216474731533472146787083736159238827774998324575366977332426392345",
                "side": "BUY",
                "original_size": "1.8518",
                "size_matched": "1.85185",
                "price": "0.54",
                "outcome": "Up",
                "expiration": "0",
                "order_type": "FOK",
                "associate_trades": [
                    "e16c9c49-7f4e-492e-9cb0-8778e54ad38a"
                ],
                "created_at": 1763701801
            }
        """
        return await self._rest("GET", f"/data/order/{order_id}")

    async def get_orders(self, params: Mapping[str, Any] | None = None) -> list[Any]:
        return await self._paginate("/data/orders", params)

    async def get_trades(self, params: Mapping[str, Any] | None = None) -> list[Any]:
        return await self._paginate("/data/trades", params)
    

    async def get_notifications(self, signature_type: int | None = None) -> Any:
        sig = signature_type if signature_type is not None else self.signature_type
        query = {"signature_type": str(sig)}
        return await self._rest("GET", "/notifications", params=query)

    async def drop_notifications(self, ids: Sequence[str] | None = None) -> Any:
        params = {"ids": ",".join(ids)} if ids else None
        return await self._rest("DELETE", "/notifications", params=params)

    async def get_balance_allowance(self, **params: Any) -> Any:
        query = dict(params or {})
        query.setdefault("signature_type", self.signature_type)
        return await self._rest("GET", "/balance-allowance", params=query or None)

    async def update_balance_allowance(self, **params: Any) -> Any:
        body = dict(params or {})
        body.setdefault("signature_type", self.signature_type)
        return await self._rest("POST", "/balance-allowance/update", json=body or None)
    
    async def get_usdc(self):
        data = await self.get_balance_allowance(asset_type='COLLATERAL')
        balance = float(data.get('balance', 0.0))
        if balance > 0:
            balance = balance / 1e6
        return balance
    
    async def get_position(self, token_id: str) -> Any:
        data = await self.get_balance_allowance(asset_type='CONDITIONAL', token_id=token_id)
        position = float(data.get('balance', 0.0))
        if position > 0:
            position = position / 1e6
        return position

    async def get_mergeable_positions(
        self,
        *,
        size_threshold: float = 0.1,
        limit: int = 100,
        sort_by: str = "TOKENS",
        sort_direction: str = "DESC",
        user: str | None = None,
        neg_risk: bool = False,
        mergeable: bool = True,
    ) -> Any:
        params = {
            "sizeThreshold": str(size_threshold),
            "limit": str(limit),
            "sortBy": sort_by,
            "sortDirection": sort_direction,
            "mergeable": str(mergeable).lower(),
        }
        if user is not None:
            params["user"] = user
        else:
            params['user'] = self.funder
            
        if neg_risk:
            params["negRisk"] = "true"
        return await self._rest("GET", "/positions", params=params, host=DEFAULT_DATA_ENDPOINT)


    async def merge_tokens_strict(
        self,
        condition_id: str,
        amount: float | None = None,
        neg_risk: bool = False,
        *,
        rpc_url: str | None = None,
        wait_timeout: int | None = 120,
        verbose: bool = False,
    ) -> bool:
        """严格按外部示例通过 Safe 合并头寸，返回 True/False。"""
        return await asyncio.to_thread(
            self._merge_tokens_strict_sync,
            condition_id,
            amount,
            neg_risk,
            rpc_url,
            wait_timeout,
            verbose,
        )

    def _merge_tokens_strict_sync(
        self,
        condition_id: str,
        amount: float | None,
        neg_risk: bool,
        rpc_url: str | None,
        wait_timeout: int | None,
        verbose: bool,
    ) -> bool:
        try:
            rpc = rpc_url or os.getenv("RPC_URL")
            if not rpc:
                raise RuntimeError("RPC_URL is required for merge_tokens_strict")
            # 使用独立 provider，避免共享缓存的速率限制
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
            with suppress(Exception):
                from web3.middleware import geth_poa_middleware, ExtraDataToPOAMiddleware
                try:
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                except Exception:
                    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            from eth_account import Account as _A

            pk_env = os.getenv("PK")
            if pk_env:
                private_key = pk_env
            else:
                private_key, _, _ = self._get_signing_context()
            account = _A.from_key(private_key)
            signer_addr = account.address
            safe_address_env = os.getenv("PROXY_WALLET") or self.funder
            if not safe_address_env:
                raise RuntimeError("Safe/proxy wallet address缺失，请在 PROXY_WALLET 或 funder 配置")
            safe_address = w3.to_checksum_address(safe_address_env)

            cfg = self._contracts(self.chain_id, neg_risk)
            ctf_addr = w3.to_checksum_address(cfg["conditional_tokens"])
            coll_addr = w3.to_checksum_address(cfg["collateral"])
            adapter_addr = cfg.get("neg_risk_adapter") or NEG_RISK_ADAPTER_ADDRESS
            if verbose:
                print(
                    f"[merge_tokens_strict] rpc={getattr(w3.provider, 'endpoint_uri', '')} "
                    f"signer={signer_addr} safe={safe_address} neg_risk={neg_risk}"
                )

            ctf_contract = w3.eth.contract(address=ctf_addr, abi=ctf_abi)
            if amount is None:
                parent_collection_id = bytes(32)
                cond_bytes = bytes.fromhex(condition_id[2:] if condition_id.startswith("0x") else condition_id)
                collection_id_0 = ctf_contract.functions.getCollectionId(parent_collection_id, cond_bytes, 1).call()
                collection_id_1 = ctf_contract.functions.getCollectionId(parent_collection_id, cond_bytes, 2).call()
                position_id_0 = ctf_contract.functions.getPositionId(coll_addr, collection_id_0).call()
                position_id_1 = ctf_contract.functions.getPositionId(coll_addr, collection_id_1).call()
                balance_0 = ctf_contract.functions.balanceOf(safe_address, position_id_0).call()
                balance_1 = ctf_contract.functions.balanceOf(safe_address, position_id_1).call()
                amount_wei = min(balance_0, balance_1)
                if amount_wei == 0:
                    if verbose:
                        print("Merge failed: No tokens to merge")
                    return False
                if verbose:
                    print(f"[merge_tokens_strict] balance0={balance_0} balance1={balance_1} amount_wei={amount_wei}")
            else:
                amount_wei = int(float(amount) * (10 ** USDCE_DIGITS))
                if verbose:
                    print(f"[merge_tokens_strict] amount_input={amount} amount_wei={amount_wei}")

            parent_collection_id_hex = ZERO_BYTES32
            partition = [1, 2]

            data = ctf_contract.functions.mergePositions(
                coll_addr,
                bytes.fromhex(parent_collection_id_hex[2:]),
                bytes.fromhex(condition_id[2:] if condition_id.startswith("0x") else condition_id),
                partition,
                amount_wei,
            )._encode_transaction_data()

            safe = w3.eth.contract(address=safe_address, abi=safe_abi)
            nonce_safe = safe.functions.nonce().call()
            to = adapter_addr if neg_risk else ctf_addr
            if verbose:
                print(f"[merge_tokens_strict] to={to} safe_nonce={nonce_safe}")

            tx_hash_bytes = safe.functions.getTransactionHash(
                w3.to_checksum_address(to),
                0,
                bytes.fromhex(data[2:]),
                0,
                0,
                0,
                0,
                w3.to_checksum_address(ZERO_ADDRESS),
                w3.to_checksum_address(ZERO_ADDRESS),
                nonce_safe,
            ).call()

            hash_bytes = Web3.to_bytes(hexstr=tx_hash_bytes.hex() if hasattr(tx_hash_bytes, "hex") else tx_hash_bytes)
            signature_obj = _A._sign_hash(hash_bytes, private_key)
            r = signature_obj.r.to_bytes(32, byteorder="big")
            s = signature_obj.s.to_bytes(32, byteorder="big")
            v = signature_obj.v.to_bytes(1, byteorder="big")
            signature = r + s + v

            tx = safe.functions.execTransaction(
                w3.to_checksum_address(to),
                0,
                bytes.fromhex(data[2:]),
                0,
                0,
                0,
                0,
                w3.to_checksum_address(ZERO_ADDRESS),
                w3.to_checksum_address(ZERO_ADDRESS),
                signature,
            ).build_transaction(
                {
                    "from": account.address,
                    "nonce": w3.eth.get_transaction_count(account.address),
                    "gas": 500000,
                    "gasPrice": w3.eth.gas_price,
                }
            )
            if verbose:
                print(
                    f"[merge_tokens_strict] send from={account.address} nonce={tx['nonce']} "
                    f"gas={tx['gas']} gasPrice={tx['gasPrice']}"
                )

            signed_tx = account.sign_transaction(tx)
            raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
            if raw_tx is None:
                raise RuntimeError("Signed transaction missing rawTransaction/raw_transaction")
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            if verbose:
                print(f"[merge_tokens_strict] sent tx={tx_hash.hex()} safe_nonce={nonce_safe}")

            if wait_timeout and wait_timeout > 0:
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=wait_timeout, poll_latency=2)
                if verbose and receipt:
                    print(f"[merge_tokens_strict] receipt status={receipt.get('status')} gasUsed={receipt.get('gasUsed')}")
                if receipt.get("status") == 1:
                    if verbose:
                        print(f"Merge successful! Amount: {amount_wei / 10 ** USDCE_DIGITS} USDC")
                    return True
                if verbose:
                    print("Merge failed: Transaction reverted")
                return False
            return True
        except Exception as exc:
            # 按用户要求：失败直接抛出，不做重试或静默 False
            raise

    @staticmethod
    def _normalize_condition_hex(value: str, field: str) -> str:
        if not value:
            raise ValueError(f"{field} is required")
        if isinstance(value, bytes):
            value = value.hex()
        v = str(value)
        if not v.startswith("0x"):
            v = f"0x{v}"
        if len(v) != 66:
            raise ValueError(f"{field} must be 32-byte hex string")
        return v

    def _normalize_split_amount(self, amount: float | int, raw_amount: bool) -> int:
        if raw_amount:
            if isinstance(amount, float) and not float(amount).is_integer():
                raise ValueError("raw_amount=True expects integer base-unit amount")
            amount_int = int(amount)
            if amount_int <= 0:
                raise ValueError("amount must be positive")
            return amount_int
        value = float(amount)
        if value <= 0:
            raise ValueError("amount must be positive")
        return self._to_token_decimals(value)

    async def claim_positions(
        self,
        *,
        user: str | None = None,
        dry_run: bool = False,
        rpc_url: str | None = None,
        rpc_urls: Sequence[str] | None = None,
        gas: int = 300000,
        verbose: bool = False,
        limit: int = 500,
        include_receipt: bool = False,
    ) -> list[dict[str, Any]]:
        """自动拉取 data-api 的 redeemable 头寸并逐个 claim。

        只对满足 redeemable==True 且 curPrice==1 且 size>0 的仓位执行，index_set=1<<outcomeIndex。
        始终使用 Safe 方式执行 redeemPositions（owner 私钥签名）。
        """
        # 默认用代理钱包/资金钱包
        if user is None:
            entry = self._api_entry()
            user = entry[2] if entry and len(entry) > 2 else None
        if not user:
            raise RuntimeError("Polymarket claim_positions 需要提供 user (proxy wallet)")
        if not self.funder:
            self.funder = user

        # 构造候选 RPC 列表 (单个 rpc_url 优先, 其次用户传入 rpc_urls, 最后内置默认)
        candidates: list[str] = []
        if rpc_url:
            candidates.append(rpc_url)
        for u in (rpc_urls or []):
            if u and u not in candidates:
                candidates.append(u)
        for u in DEFAULT_POLYGON_RPCS:
            if u not in candidates:
                candidates.append(u)

        params = {"user": user, "limit": limit, "mergeable": "true", 'sizeThreshold': '.1', 'offset': '0'}
        positions = await self._rest(
            "GET",
            "/positions",
            params=params,
            host=DEFAULT_DATA_ENDPOINT,
        )

        claimable: list[dict[str, Any]] = []
        for pos in positions or []:
            try:
                size = float(pos.get("size", 0) or 0)
            except Exception:
                size = 0.0
            redeemable = bool(pos.get("redeemable"))
            try:
                cur_price = float(pos.get("curPrice", 0) or 0)
            except Exception:
                cur_price = 0.0

            condition_id = pos.get("conditionId")
            outcome_idx = pos.get("outcomeIndex") or pos.get("outcome_index") or 0
            if (
                not condition_id
                or not redeemable
                or size <= 0
                or cur_price != 1
            ):
                continue
            try:
                idx_set = 1 << int(outcome_idx)
            except Exception:
                idx_set = 1
            claimable.append(
                {
                    "condition_id": condition_id,
                    "index_sets": [idx_set],
                    "size": size,
                    "outcome": pos.get("outcome"),
                    "title": pos.get("title"),
                }
            )

        results: list[dict[str, Any]] = []
        for item in claimable:
            if dry_run:
                results.append({**item, "tx": None, "dry_run": True})
                continue
            tx_hash = await asyncio.to_thread(
                self._claim_via_safe_sync,
                candidates,
                item["condition_id"],
                item["index_sets"],
                gas,
                verbose,
            )
            result_row = {**item, "tx": tx_hash, "dry_run": False}
            if include_receipt:
                try:
                    receipt_info = await self.decode_claim_receipt(
                        tx_hash,
                        rpc_url=rpc_url or (rpc_urls[0] if rpc_urls else None),
                    )
                    result_row.update({"receipt": receipt_info})
                except Exception as exc:  # pragma: no cover - 辅助信息获取失败
                    result_row.update({"receipt_error": str(exc)})
            results.append(result_row)
        return results

    async def get_usdc_web3(
        self,
        wallet: str = None,
        rpc_urls: Sequence[str] | None = None,
    ) -> float:
        if wallet is None:
            # 找代理钱包, apis['polymarket'][2]
            entry = self._api_entry()
            if not entry or len(entry) < 3 or not entry[2]:
                raise RuntimeError("Polymarket funder wallet address is not configured")
            wallet = entry[2]

        urls = list(rpc_urls or [])
        if not urls:
            urls.extend(DEFAULT_POLYGON_RPCS)

        last_error: Exception | None = None
        for url in urls:
            try:
                balance = await asyncio.to_thread(self._call_usdc_balance, url, wallet)
                return balance
            except Exception as exc:  # pragma: no cover - network failure fallback
                last_error = exc
                continue

        raise RuntimeError("Unable to fetch USDC balance") from last_error

    @staticmethod
    def _call_usdc_balance(rpc_url: str, wallet: str) -> float:
        w3 = _get_web3(rpc_url)
        contract = w3.eth.contract(
            address=w3.to_checksum_address(USDC_CONTRACT),
            abi=ERC20_BALANCE_OF_ABI,
        )
        balance = contract.functions.balanceOf(w3.to_checksum_address(wallet)).call()
        return balance / 10 ** 6

    # ------------------------------------------------------------------
    # Internal utilities

    async def decode_claim_receipt(
        self,
        tx_hash: str,
        *,
        rpc_url: str | None = None,
    ) -> dict[str, Any]:
        if not tx_hash:
            raise ValueError("tx_hash is required")
        url = rpc_url or DEFAULT_POLYGON_RPCS[0]
        return await asyncio.to_thread(self._decode_payout_receipt_sync, tx_hash, url)

    def _decode_payout_receipt_sync(self, tx_hash: str, rpc_url: str) -> dict[str, Any]:
        w3 = _get_web3(rpc_url)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        contract_cfg = self._contracts(self.chain_id, False)
        ctf_addr = w3.to_checksum_address(contract_cfg["conditional_tokens"])
        ctf = w3.eth.contract(address=ctf_addr, abi=CONDITIONAL_TOKENS_ABI)

        decoded = []
        try:
            decoded = ctf.events.PayoutRedemption().process_receipt(receipt)
        except Exception:
            decoded = []

        if decoded:
            ev = decoded[0]["args"]
            index_sets = [int(x) for x in ev.get("indexSets", [])]
            payout = int(ev.get("payout", 0))
            return {
                "status": receipt.status,
                "gasUsed": receipt.gasUsed,
                "indexSets": index_sets,
                "payout": payout,
                "redeemer": ev.get("redeemer"),
                "collateralToken": ev.get("collateralToken"),
                "conditionId": ev.get("conditionId").hex()
                if hasattr(ev.get("conditionId"), "hex")
                else ev.get("conditionId"),
            }

        return {"status": receipt.status, "gasUsed": receipt.gasUsed}

    def _claim_via_safe_sync(
        self,
        rpc_urls: Sequence[str],
        condition_id: str,
        index_sets: list[int],
        gas: int,
        verbose: bool = False,
    ) -> str:
        from eth_account import Account as _A
        from time import sleep
        from web3 import Web3
        from web3.exceptions import Web3RPCError

        # Prefer explicit RPC_URL env, then user-provided list
        candidates: list[str] = []
        env_rpc = os.getenv("RPC_URL")
        if env_rpc:
            candidates.append(env_rpc)
        for u in rpc_urls:
            if u and u not in candidates:
                candidates.append(u)
        if not candidates:
            candidates = list(DEFAULT_POLYGON_RPCS)

        last_error: Exception | None = None
        w3 = None
        rpc_used = None
        for url in candidates:
            try:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 30}))
                with suppress(Exception):
                    from web3.middleware import geth_poa_middleware, ExtraDataToPOAMiddleware
                    try:
                        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    except Exception:
                        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                rpc_used = url
                break
            except Exception as exc:
                last_error = exc
                continue
        if w3 is None:
            raise RuntimeError(f"All RPC endpoints failed: {candidates}") from last_error

        pk_env = os.getenv("PK")
        if pk_env:
            private_key = pk_env
        else:
            private_key, _, _ = self._get_signing_context()
        signer_addr = _A.from_key(private_key).address
        safe_addr = self.funder
        if not safe_addr:
            raise RuntimeError("Safe/proxy wallet address未知, 请在 apis['polymarket'][2] 或构造函数 funder 设置")

        ctf_addr = self._contracts(self.chain_id, False)["conditional_tokens"]
        ctf = w3.eth.contract(address=w3.to_checksum_address(ctf_addr), abi=CONDITIONAL_TOKENS_ABI)
        safe = w3.eth.contract(address=w3.to_checksum_address(safe_addr), abi=SAFE_ABI)

        cond_bytes = bytes.fromhex(condition_id.replace("0x", ""))
        if len(cond_bytes) != 32:
            raise ValueError("condition_id must be 32-byte hex string")

        redeem_calldata = ctf.encode_abi(
            "redeemPositions",
            args=[
                w3.to_checksum_address(USDC_CONTRACT),
                bytes(32),
                cond_bytes,
                index_sets,
            ],
        )

        safe_tx_gas = 0
        base_gas = 0
        gas_price = 0
        gas_token = ZERO_ADDRESS
        refund_receiver = ZERO_ADDRESS
        value = 0
        operation = 0  # CALL

        try:
            safe_nonce = safe.functions.nonce().call()
        except Web3RPCError as exc:
            # 速率限制等错误直接抛出，便于调用层切换 RPC
            raise RuntimeError(f"获取 Safe nonce 失败 (rpc={rpc_used}): {exc}") from exc
        except Exception as exc:
            raise RuntimeError("无法获取 Safe nonce, 请确认 funder 地址为有效 Safe") from exc

        try:
            safe_tx_hash = safe.functions.getTransactionHash(
                w3.to_checksum_address(ctf_addr),
                value,
                redeem_calldata,
                operation,
                safe_tx_gas,
                base_gas,
                gas_price,
                w3.to_checksum_address(gas_token),
                w3.to_checksum_address(refund_receiver),
                safe_nonce,
            ).call()
        except Web3RPCError as exc:
            raise RuntimeError(f"Safe getTransactionHash 调用失败 (rpc={rpc_used}): {exc}") from exc
        except Exception as exc:
            raise RuntimeError("Safe getTransactionHash 调用失败") from exc

        signed = _A._sign_hash(safe_tx_hash, private_key)  # eth_sign 风格
        sig_bytes = (
            int(signed.r).to_bytes(32, "big")
            + int(signed.s).to_bytes(32, "big")
            + bytes([signed.v])
        )

        try:
            acct = _A.from_key(private_key)
            sender = acct.address
            # 使用 pending 避免重复使用已在 mempool 的 nonce 触发 replacement underpriced
            nonce = w3.eth.get_transaction_count(sender)
            gas_price_chain = w3.eth.gas_price
        except Exception as exc:
            raise RuntimeError("获取 sender nonce/gas_price 失败") from exc

        tx = safe.functions.execTransaction(
            w3.to_checksum_address(ctf_addr),
            value,
            redeem_calldata,
            operation,
            safe_tx_gas,
            base_gas,
            gas_price,
            w3.to_checksum_address(gas_token),
            w3.to_checksum_address(refund_receiver),
            sig_bytes,
        ).build_transaction(
            {
                "from": sender,
                "nonce": nonce,
                "gas": gas,
                "gasPrice": gas_price_chain,
            }
        )

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        send_errors: list[str] = []
        for attempt in range(3):
            try:
                raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
                if raw_tx is None:  # pragma: no cover
                    raise AttributeError("Signed transaction missing rawTransaction/raw_transaction")
                tx_hash = w3.eth.send_raw_transaction(raw_tx)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, poll_latency=2, timeout=180)
                if receipt.get("status") != 1:
                    raise RuntimeError(f"Safe redeemPositions failed status!=1: {tx_hash.hex()}")
                if verbose:
                    print(
                        {
                            "tx": tx_hash.hex(),
                            "safe_nonce": safe_nonce,
                            "wallet": sender,
                            "gasPrice": gas_price_chain,
                            "gas": gas,
                            "rpc_used": rpc_used or getattr(w3.provider, "endpoint_uri", "unknown"),
                        }
                    )
                return tx_hash.hex()
            except Exception as exc:
                send_errors.append(str(exc))
                if verbose:
                    print(f"Safe redeem attempt {attempt+1} failed: {exc}")
                sleep(0.5)
                continue
        raise RuntimeError(f"Safe redeem all attempts failed: {' | '.join(send_errors)}")

    async def _fetch_event(self, slug: str) -> dict | None:
        resp = await self.client.get(GAMMA_EVENTS_API, params={"slug": slug})
        payload = await resp.json()
        if isinstance(payload, list) and payload:
            return payload[0]
        return None

    async def find_active_market(
        self,
        *,
        base_slug: str = DEFAULT_BASE_SLUG,
        interval: int = DEFAULT_INTERVAL,
        window: int = DEFAULT_WINDOW,
    ) -> tuple[str, dict, dict]:
        
        """
        返回值: slug, event, market
        https://docs.polymarket.com/api-reference/markets/get-market-by-id
        """
    
        async def _try_slug(slug: str | None) -> tuple[str, dict, dict] | None:
            if not slug:
                return None
            event = await self._fetch_event(slug)
            if not event:
                return None

            event = {k: parse_field(v) for k, v in event.items()}
            for market in event.get("markets", []):
                if not _accepting_orders(market):
                    continue
                market = {k: parse_field(v) for k, v in market.items()}
                return slug, event, market
            return None

        if base_slug == HOURLY_BITCOIN_BASE_SLUG:
            hourly_slug = _compose_hourly_slug(base_slug)
            hourly_match = await _try_slug(hourly_slug)
            if hourly_match:
                return hourly_match

        now_ts = int(datetime.now(UTC).timestamp())
        base_ts = (now_ts // interval) * interval

        for offset in _iter_offsets(window):
            ts = base_ts + offset * interval
            if ts < 0:
                continue
            slug = f"{base_slug}-{ts}"
            result = await _try_slug(slug)
            if result:
                return result

        raise RuntimeError(
            f"未在 {base_slug} 的 +/-{window} 个区间内找到可交易的市场"
        )

    async def resolve_active_market_tokens(
        self,
        *,
        base_slug: str = DEFAULT_BASE_SLUG,
        interval: int = DEFAULT_INTERVAL,
        window: int = DEFAULT_WINDOW,
    ) -> tuple[str, dict, dict, list[Any], list[Any]]:
        slug, event, market = await self.find_active_market(
            base_slug=base_slug,
            interval=interval,
            window=window,
        )

        outcomes = _parse_list(market.get("outcomes"))
        token_ids = _parse_list(market.get("clobTokenIds"))

        if not outcomes or not token_ids:
            raise RuntimeError("market 数据缺少 outcomes 或 clobTokenIds 字段")
        if len(outcomes) != len(token_ids):
            raise RuntimeError("outcomes 与 clobTokenIds 数量不匹配")

        return slug, event, market, outcomes, token_ids

    async def _rest(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        host: str | None = None,
    ) -> Any:
        
        url = f"{host}{path}" if host else f"{self.rest_api}{path}"
        request_kwargs: dict[str, Any] = {}
        if params:
            request_kwargs["params"] = {k: v for k, v in params.items() if v is not None}
        if json is not None:
            request_kwargs["json"] = json

        requester = getattr(self.client, method.lower())
        resp = await requester(url, **request_kwargs)
        if resp.status >= 400:
            text = await resp.text()
            raise RuntimeError(f"Polymarket {method} {path} failed: {resp.status} {text}")
        if resp.content_length == 0:
            return None
        return await resp.json()

    async def _paginate(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
    ) -> list[Any]:
        filters = {k: v for k, v in (params or {}).items() if v is not None}
        cursor = "MA=="
        results: list[Any] = []
        while cursor != END_CURSOR:
            query = dict(filters)
            if cursor:
                query["next_cursor"] = cursor
            payload = await self._rest("GET", path, params=query or None)
            cursor = payload.get("next_cursor", END_CURSOR)
            results.extend(payload.get("data", []))
        return results

    def _token_list(self, token_ids: Sequence[str] | str) -> list[str]:
        if isinstance(token_ids, str):
            tokens = [token_ids]
        else:
            tokens = list(token_ids)
        tokens = [tid for tid in tokens if tid]
        if not tokens:
            raise ValueError("token_ids must not be empty")
        return tokens

    def _owner_key(self, owner: str | None = None) -> str:
        if owner:
            return owner
        creds = self._api_creds()
        api_key = creds.get("api_key") if creds else None
        if not api_key:
            raise RuntimeError("Polymarket API key missing; call create_or_derive_api_creds first")
        return api_key

    def _api_entry(self) -> list[Any] | None:
        session = getattr(self.client, "_session", None)
        if session is None:
            return None
        apis = getattr(session, "_apis", None) or session.__dict__.get("_apis")
        if apis is None:
            return None
        return apis.get(API_NAME)

    def _api_creds(self) -> dict[str, Any] | None:
        session = getattr(self.client, "_session", None)
        if session is None:
            return None
        return getattr(session, "_polymarket_api_creds", None)

    def _store_api_creds(self, data: Mapping[str, Any]) -> None:
        session = getattr(self.client, "_session", None)
        if session is None:
            raise RuntimeError("pybotters Client session not initialized for Polymarket creds")
        creds = {
            "api_key": data.get("apiKey") or data.get("api_key"),
            "api_secret": data.get("secret") or data.get("api_secret"),
            "api_passphrase": data.get("passphrase") or data.get("api_passphrase"),
        }
        if not creds["api_key"] or not creds["api_secret"] or not creds["api_passphrase"]:
            raise RuntimeError("Polymarket API creds response missing key/secret/passphrase")
        session.__dict__["_polymarket_api_creds"] = creds
        apis = session.__dict__.get("_apis")
        if isinstance(apis, dict):
            entry = list(apis.get(API_NAME, []))
            while len(entry) < 7:
                entry.append("")
            entry[4] = creds["api_key"]
            entry[5] = creds["api_secret"]
            entry[6] = creds["api_passphrase"]
            apis[API_NAME] = entry

    def _ensure_session_entry(
        self,
        *,
        private_key: str | None,
        funder: str | None,
        chain_id: int | None,
    ) -> None:
        session = getattr(self.client, "_session", None)
        if session is None:
            raise RuntimeError("pybotters.Client session not initialized")
        apis = getattr(session, "_apis", None)
        if apis is None:
            raise RuntimeError("pybotters Client missing _apis; load apis.json when creating the client")

        entry = list(apis.get(API_NAME, []))
        if not entry and not private_key:
            return

        packed = entry[2] if len(entry) > 2 else None
        if not isinstance(packed, (list, tuple)):
            packed = None

        def _packed_value(idx: int) -> Any | None:
            if packed is None:
                return None
            if idx >= len(packed):
                return None
            value = packed[idx]
            if isinstance(value, str):
                value = value.strip()
            return value or None

        packed_api_key = _packed_value(0)
        packed_api_secret = _packed_value(1)
        packed_passphrase = _packed_value(2)
        packed_chain_id = _packed_value(3)
        packed_wallet = _packed_value(4)

        while len(entry) < 3:
            entry.append("")

        existing_pk = entry[0] if entry else None
        normalized_pk: str | None = None
        candidate_pk = private_key or existing_pk
        if candidate_pk:
            candidate_pk = str(candidate_pk)
            normalized_pk = (
                candidate_pk if candidate_pk.startswith("0x") else f"0x{candidate_pk}"
            )

        if not normalized_pk:
            raise RuntimeError("Polymarket需要钱包私钥 (apis['polymarket'][0])")

        entry[0] = normalized_pk

        existing_wallet = entry[2] if isinstance(entry[2], str) and entry[2] else None
        effective_wallet = funder or packed_wallet or existing_wallet or self.funder
        if effective_wallet:
            entry[2] = effective_wallet
            self.funder = effective_wallet
        else:
            entry[2] = ""

        derived_chain_id: int | None = None
        if packed_chain_id is not None:
            try:
                derived_chain_id = int(packed_chain_id)
            except (TypeError, ValueError):
                derived_chain_id = None
        if chain_id is None and derived_chain_id is not None:
            self.chain_id = derived_chain_id

        if packed_api_key and packed_api_secret and packed_passphrase:
            session.__dict__["_polymarket_api_creds"] = {
                "api_key": packed_api_key,
                "api_secret": packed_api_secret,
                "api_passphrase": packed_passphrase,
            }

        apis[API_NAME] = entry
        session.__dict__["_apis"] = apis
        session.__dict__["_polymarket_chain_id"] = self.chain_id
        session.__dict__["_polymarket_signature_type"] = self.signature_type
        self.auth = True

    @staticmethod
    def load_poly_api():
        from dotenv import load_dotenv

        load_dotenv()
        pk = os.getenv("PK")
        api_key = os.getenv("CLOB_API_KEY")
        api_secret = os.getenv("CLOB_API_SECRET")
        passphrase = os.getenv("CLOB_API_PASSPHRASE")
        chain_id = os.getenv("CHAIN_ID") or 137
        wallet_address = os.getenv("POLY_WALLET_ADDRESS")
        return [pk, "", (api_key, api_secret, passphrase, chain_id, wallet_address)]

@lru_cache(maxsize=8)
def _get_web3(rpc_url: str | None):
    """创建 web3 对象, 带多 RPC 备用与重试.

    逻辑:
    1. 优先使用传入 rpc_url (如果提供)
    2. 失败则按 DEFAULT_POLYGON_RPCS 顺序依次尝试
    3. 任一连接成功立即返回, 全部失败抛出统一异常
    """
    from web3 import Web3

    candidates: list[str] = []
    if rpc_url:
        candidates.append(rpc_url)
    for u in DEFAULT_POLYGON_RPCS:
        if u not in candidates:
            candidates.append(u)

    last_error: Exception | None = None
    for url in candidates:
        try:
            provider = Web3.HTTPProvider(url, request_kwargs={"timeout": 7})
            w3 = Web3(provider)
            if w3.is_connected():
                return w3
            last_error = RuntimeError(f"RPC not connected: {url}")
        except Exception as exc:  # pragma: no cover - 网络异常
            last_error = exc
            continue

    raise RuntimeError(f"Failed to connect Polygon RPCs: {candidates}") from last_error
