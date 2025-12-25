from __future__ import annotations

import asyncio
import logging
import json
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Any, Literal, Sequence

import pybotters

from lighter.api.account_api import AccountApi
from lighter.api.order_api import OrderApi
from lighter.api.candlestick_api import CandlestickApi
from lighter.api_client import ApiClient
from lighter.configuration import Configuration
from lighter.signer_client import SignerClient

from .models.lighter import LighterDataStore, _maybe_to_dict

logger = logging.getLogger(__name__)


class Lighter:
    """Lighter exchange client (REST + WebSocket) built on top of the official SDK."""

    def __init__(
        self,
        client: pybotters.Client,
        *,
        configuration: Configuration | None = None,
        l1_address: str | None = None,
        secret: str | None = None,
        api_key_index: int = 3,
        api_client: ApiClient | None = None,
        order_api: OrderApi | None = None,
        candlestick_api: CandlestickApi | None = None,
        account_api: AccountApi | None = None,
        ws_url: str | None = None,
    ) -> None:
        self.client = client
        self.store = LighterDataStore()
        self.l1_address = l1_address
        self.account_index: int | None = None
        self.secret:str = secret
        self.api_key_index = api_key_index

        self.configuration = configuration or Configuration.get_default()
        self._api_client = api_client or ApiClient(configuration=self.configuration)
        self._owns_api_client = api_client is None

        self.order_api = order_api or OrderApi(self._api_client)
        self.candlestick_api = candlestick_api or CandlestickApi(self._api_client)
        self.account_api = account_api or AccountApi(self._api_client)
        self.signer: SignerClient = None

        base_host = self.configuration.host.rstrip("/")
        default_ws_url = f"{base_host.replace('https://', 'wss://')}/stream"
        self.ws_url = ws_url or default_ws_url
        self.id_to_symbol: dict[str, str] = {}

    async def __aenter__(self) -> "Lighter":
        await self.update("detail")

        # 设置id_to_symbol映射
        for detail in self.store.detail.find():
            market_id = detail.get("market_id")
            symbol = detail.get("symbol")
            if market_id is not None and symbol is not None:
                self.id_to_symbol[str(market_id)] = symbol
        
        self.store.set_id_to_symbol(self.id_to_symbol)

        # 尝试自动设置account_index
        if self.l1_address is not None:
            subact = await self.account_api.accounts_by_l1_address(
                l1_address=self.l1_address
            )
            self.account_index = subact.sub_accounts[0].index

        if self.secret:

            self.signer = SignerClient(
                url=self.configuration.host,
                private_key=self.secret,
                account_index=self.account_index if self.account_index is not None else -1,
                api_key_index=self.api_key_index,
            )

        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_api_client:
            await self._api_client.close()

    @property
    def auth(self):
        if not self.signer:
            raise RuntimeError("SignerClient is required for auth token generation")
        auth, err = self.signer.create_auth_token_with_expiry(SignerClient.DEFAULT_10_MIN_AUTH_EXPIRY)
        if err is not None:
            raise Exception(err)
        return auth

    def get_contract_id(self, symbol: str) -> str | None:
        """Helper that resolves a symbol to its `market_id`."""
        detail = self.store.detail.get({"symbol": symbol}) or self.store.detail.get({"market_id": symbol})
        if not detail:
            return None
        market_id = detail.get("market_id")
        if market_id is None and detail.get("order_book_index") is not None:
            market_id = detail["order_book_index"]
        return str(market_id) if market_id is not None else None

    def _get_detail_entry(self, symbol: str | None = None, market_index: int | None = None) -> dict[str, Any] | None:
        if symbol:
            entry = self.store.detail.get({"symbol": symbol})
            if entry:
                return entry

        if market_index is not None:
            entries = self.store.detail.find({"market_id": market_index})
            if entries:
                return entries[0]

        return None

    async def update(
        self,
        update_type: Literal[
            "detail",
            "orders",
            "history_order",
            "history_orders",
            "account",
            "positions",
            "all",
        ] = "all",
        *,
        symbol: str | None = None,
        limit: int = 50,
    ) -> None:
        """Refresh cached data via Lighter REST endpoints."""

        tasks: list[tuple[str, Any]] = []

        include_detail = update_type in {"detail", "all"}
        include_orders = update_type in {"orders", "all"}
        include_history = update_type in {"history_order", "history_orders", "all"}
        include_account = update_type in {"account", "positions", "all"}
        account_index = self.account_index


        if include_detail:
            # Use raw HTTP to avoid strict SDK model validation issues (e.g., status 'inactive').
            url = f"{self.configuration.host.rstrip('/')}/api/v1/orderBooks"
            tasks.append(("detail", self.client.get(url)))

        if include_orders:
            if account_index is None or symbol is None:
                if update_type == "orders":
                    raise ValueError("account_index and symbol are required to update orders")
            else:
                cid = self.get_contract_id(symbol)
                tasks.append(
                    (
                        "orders",
                        self.order_api.account_active_orders(
                            account_index=account_index,
                            market_id=int(cid),
                            auth=self.auth
                        ),
                    )
                )

        if include_history:
            if account_index is None:
                raise ValueError("account_index is required to update history orders")
            else:
                tasks.append(
                    (
                        "history_orders",
                        self.order_api.account_inactive_orders(
                            account_index=account_index,
                            limit=limit,
                            auth=self.auth
                        ),
                    )
                )

        if include_account:
            if account_index is None:
                if update_type in {"account", "positions"}:
                    raise ValueError("account_index is required to update account data")
            else:
                tasks.append(
                    (
                        "account",
                        self.account_api.account(
                            by="index",
                            value=str(account_index),
                        ),
                    )
                )

        if not tasks:
            logger.debug("No REST requests enqueued for Lighter update_type=%s", update_type)
            return

        results: dict[str, Any] = {}
        for key, coroutine in tasks:
            try:
                resp = await coroutine
                if key == "detail":
                    # Parse JSON body for detail endpoint
                    results[key] = await resp.json()
                else:
                    results[key] = resp
            except Exception:
                logger.exception("Lighter REST request %s failed", key)
                raise

        if "detail" in results:
            self.store.detail._onresponse(results["detail"])

        if "orders" in results:
            self.store.orders._onresponse(results["orders"])

        if "history_orders" in results:
            self.store.orders._onresponse(results["history_orders"])

        if "account" in results:
            account_payload = results["account"]
            self.store.accounts._onresponse(account_payload)
            self.store.positions._onresponse(account_payload)

    async def sub_orderbook(
        self,
        symbols: Sequence[str] | str,
        *,
        account_ids: Sequence[int] | int | None = None,
        depth_limit: int | None = None,
    ) -> pybotters.ws.WebSocketApp:
        """Subscribe to order book (and optional account) websocket streams by symbol."""

        if isinstance(symbols, str):
            symbol_list = [symbols]
        else:
            symbol_list = list(symbols)

        if not symbol_list and not account_ids:
            raise ValueError("At least one symbol or account_id must be provided")

        needs_detail = any(self.get_contract_id(sym) is None for sym in symbol_list)
        if needs_detail and symbol_list:
            try:
                await self.update("detail")
            except Exception:
                logger.exception("Failed to refresh Lighter market metadata for symbol resolution")
                raise

        order_book_ids: list[str] = []
        for sym in symbol_list:
            market_id = self.get_contract_id(sym)
            if market_id is None:
                if sym.isdigit():
                    market_id = sym
                else:
                    raise ValueError(f"Unknown symbol: {sym}")
            market_id_str = str(market_id)
            order_book_ids.append(market_id_str)
            self.store.book.id_to_symbol[market_id_str] = sym

        account_id_list: list[str] = []
        if account_ids is not None:
            if isinstance(account_ids, int):
                account_id_list = [str(account_ids)]
            else:
                account_id_list = [str(aid) for aid in account_ids]

        if not order_book_ids and not account_id_list:
            raise ValueError("No valid symbols or account_ids resolved for subscription")

        if depth_limit is not None:
            self.store.book.limit = depth_limit

        order_book_channels = [f"order_book/{mid}" for mid in order_book_ids]
        account_channels = [f"account_all/{aid}" for aid in account_id_list]

        send_payload = [
            {"type": "subscribe", "channel": channel} for channel in order_book_channels + account_channels
        ]

        ws_app = self.client.ws_connect(
            self.ws_url,
            send_json=send_payload,
            hdlr_json=self.store.onmessage,
        )

        await ws_app._event.wait()
        return ws_app


    async def sub_orders(
        self,
        account_ids: Sequence[int] | int = None,
    ) -> pybotters.ws.WebSocketApp:
        """Subscribe to order updates via Account All Orders stream.

        Channel per docs: "account_all_orders/{ACCOUNT_ID}" (requires auth).
        Response carries an "orders" mapping of market_id -> [Order].
        """
        if account_ids:
            if isinstance(account_ids, int):
                account_id_list = [str(account_ids)]
            else:
                account_id_list = [str(aid) for aid in account_ids]
        else:
            account_id_list = [self.account_index]

        channels = [f"account_all_orders/{aid}" for aid in account_id_list]
        send_payload = [
            {"type": "subscribe", "channel": channel, "auth": self.auth}
            for channel in channels
        ]

        ws_app = self.client.ws_connect(
            self.ws_url,
            send_json=send_payload,
            hdlr_json=self.store.onmessage,
        )
        await ws_app._event.wait()
        return ws_app
    
    

    async def sub_kline(
        self,
        symbols: Sequence[str] | str,
        *,
        resolutions: Sequence[str] | str,
    ) -> pybotters.ws.WebSocketApp:
        """Subscribe to trade streams and aggregate into klines in the store.

        - symbols: list of symbols (e.g., ["BTC-USD"]) or a single symbol; may also be numeric market_ids.
        - resolutions: list like ["1m", "5m"] or a single resolution; added to kline store for aggregation.
        """

        # Normalize inputs
        symbol_list = [symbols] if isinstance(symbols, str) else list(symbols)
        res_list = [resolutions] if isinstance(resolutions, str) else list(resolutions)

        if not symbol_list:
            raise ValueError("At least one symbol must be provided")
        if not res_list:
            raise ValueError("At least one resolution must be provided")

        # Ensure market metadata for symbol->market_id resolution
        needs_detail = any(self.get_contract_id(sym) is None and not str(sym).isdigit() for sym in symbol_list)
        if needs_detail:
            try:
                await self.update("detail")
            except Exception:
                logger.exception("Failed to refresh Lighter market metadata for kline subscription")
                raise

        # Resolve market ids and populate id->symbol mapping for klines store
        trade_market_ids: list[str] = []
        for sym in symbol_list:
            market_id = self.get_contract_id(sym)
            if market_id is None:
                if str(sym).isdigit():
                    market_id = str(sym)
                    symbol_for_map = str(sym)
                else:
                    raise ValueError(f"Unknown symbol: {sym}")
            else:
                symbol_for_map = sym
            market_id_str = str(market_id)
            trade_market_ids.append(market_id_str)
            # ensure klines store can resolve symbol from market id
            self.store.klines.id_to_symbol[market_id_str] = symbol_for_map

        # Register resolutions into kline store aggregation list
        for r in res_list:
            if r not in self.store.klines._res_list:
                self.store.klines._res_list.append(r)

        # Build subscribe payload for trade channels
        channels = [f"trade/{mid}" for mid in trade_market_ids]
        send_payload = [{"type": "subscribe", "channel": ch} for ch in channels]

        ws_app = self.client.ws_connect(
            self.ws_url,
            send_json=send_payload,
            hdlr_json=self.store.onmessage,
        )

        await ws_app._event.wait()
        return ws_app

    async def place_order(
        self,
        symbol: str,
        *,
        base_amount: float,
        price: float,
        is_ask: bool,
        order_type: Literal[
            "limit",
            "market",
            "stop-loss",
            "stop-loss-limit",
            "take-profit",
            "take-profit-limit",
            "twap",
        ] = "limit",
        time_in_force: Literal["ioc", "gtc", "post_only"] = "gtc",
        reduce_only: bool = False,
        trigger_price: float | None = None,
        order_expiry: int | None = None,
        nonce: int | None = None,
        api_key_index: int | None = None,
        client_order_index: int = 0,
    ) -> dict[str, Any]:
        """Submit an order through the signer client using human-readable inputs."""

        if self.signer is None:
            raise RuntimeError("SignerClient is required for placing orders")

        market_index = self.get_contract_id(symbol)
        if market_index is None:
            raise ValueError(f"Unknown symbol: {symbol}")
        market_index = int(market_index)

        detail = self._get_detail_entry(symbol=symbol, market_index=market_index)
        if detail is None:
            await self.update("detail")
            detail = self._get_detail_entry(symbol=symbol, market_index=market_index)
        if detail is None:
            raise ValueError(f"Market metadata unavailable for symbol: {symbol}")

        order_type_map = {
            "limit": self.signer.ORDER_TYPE_LIMIT,
            "market": self.signer.ORDER_TYPE_MARKET,
            "stop-loss": self.signer.ORDER_TYPE_STOP_LOSS,
            "stop-loss-limit": self.signer.ORDER_TYPE_STOP_LOSS_LIMIT,
            "take-profit": self.signer.ORDER_TYPE_TAKE_PROFIT,
            "take-profit-limit": self.signer.ORDER_TYPE_TAKE_PROFIT_LIMIT,
            "twap": self.signer.ORDER_TYPE_TWAP,
        }
        tif_map = {
            "ioc": self.signer.ORDER_TIME_IN_FORCE_IMMEDIATE_OR_CANCEL,
            "gtc": self.signer.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME,
            "post_only": self.signer.ORDER_TIME_IN_FORCE_POST_ONLY,
        }

        try:
            order_type_code = order_type_map[order_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported order_type: {order_type}") from exc

        try:
            tif_code = tif_map[time_in_force]
        except KeyError as exc:
            raise ValueError(f"Unsupported time_in_force: {time_in_force}") from exc

        # Per WS/API docs, OrderExpiry can be 0 with ExpiredAt computed by signer.
        # Use caller-provided value if given; otherwise default to 0 to avoid
        # "OrderExpiry is invalid" errors on some markets.
        expiry = order_expiry if order_expiry is not None else 0
        nonce_value = nonce if nonce is not None else -1
        api_key_idx = api_key_index if api_key_index is not None else self.api_key_index

        # ----- Precision and min constraints handling -----
        # Prefer explicitly supported decimals. Avoid using quote decimals to infer size.
        price_decimals = (
            detail.get("supported_price_decimals")
            or detail.get("price_decimals")
            or 0
        )
        size_decimals = (
            detail.get("supported_size_decimals")
            or detail.get("size_decimals")
            or 0
        )

        # Optional constraints provided by the API
        # Strings like "10.000000" may be returned – normalize via Decimal for accuracy
        def _to_decimal(v, default: str | int = 0):
            try:
                if v is None or v == "":
                    return Decimal(str(default))
                return Decimal(str(v))
            except Exception:
                return Decimal(str(default))

        min_base_amount = _to_decimal(detail.get("min_base_amount"), 0)
        min_quote_amount = _to_decimal(detail.get("min_quote_amount"), 0)
        order_quote_limit = _to_decimal(detail.get("order_quote_limit"), 0)

        # Use Decimal for precise arithmetic and quantization
        d_price = Decimal(str(price))
        d_size = Decimal(str(base_amount))
        quant_price = Decimal(1) / (Decimal(10) ** int(price_decimals)) if int(price_decimals) > 0 else Decimal(1)
        quant_size = Decimal(1) / (Decimal(10) ** int(size_decimals)) if int(size_decimals) > 0 else Decimal(1)

        # Round price/size to allowed decimals (half up to the nearest tick)
        d_price = d_price.quantize(quant_price, rounding=ROUND_HALF_UP)
        d_size = d_size.quantize(quant_size, rounding=ROUND_HALF_UP)

        # Ensure minimum notional and minimum base constraints
        # If violating, adjust size upward to the smallest valid amount respecting size tick
        if min_quote_amount > 0:
            notional = d_price * d_size
            if notional < min_quote_amount:
                # required size to reach min notional
                required = (min_quote_amount / d_price).quantize(quant_size, rounding=ROUND_HALF_UP)
                if required > d_size:
                    d_size = required
        if min_base_amount > 0 and d_size < min_base_amount:
            d_size = min_base_amount.quantize(quant_size, rounding=ROUND_HALF_UP)

        # Respect optional maximum notional limit if provided (>0)
        if order_quote_limit and order_quote_limit > 0:
            notional = d_price * d_size
            if notional > order_quote_limit:
                # Reduce size down to the maximum allowed notional (floor to tick)
                max_size = (order_quote_limit / d_price).quantize(quant_size, rounding=ROUND_DOWN)
                if max_size <= 0:
                    raise ValueError("order would exceed order_quote_limit and cannot be reduced to a positive size")
                d_size = max_size

        # Convert to integer representation expected by signer
        price_scale = 10 ** int(price_decimals)
        size_scale = 10 ** int(size_decimals)

        price_int = int((d_price * price_scale).to_integral_value(rounding=ROUND_HALF_UP))
        base_amount_int = int((d_size * size_scale).to_integral_value(rounding=ROUND_HALF_UP))

        trigger_price_int = (
            int((Decimal(str(trigger_price)) * price_scale).to_integral_value(rounding=ROUND_HALF_UP))
            if trigger_price is not None
            else self.signer.NIL_TRIGGER_PRICE
        )

        created_tx, response, error = await self.signer.create_order(
            market_index=market_index,
            client_order_index=client_order_index,
            base_amount=base_amount_int,
            price=price_int,
            is_ask=is_ask,
            order_type=order_type_code,
            time_in_force=tif_code,
            reduce_only=reduce_only,
            trigger_price=trigger_price_int,
            order_expiry=expiry,
            nonce=nonce_value,
            api_key_index=api_key_idx,
        )

        if error:
            raise RuntimeError(f"Lighter create_order failed: {error}")
        if response is None:
            raise RuntimeError("Lighter create_order returned no response")

        if hasattr(created_tx, "to_json"):
            request_payload = json.loads(created_tx.to_json())
        else:
            request_payload = str(created_tx)
        response_payload = response.to_dict() if hasattr(response, "to_dict") else _maybe_to_dict(response)

        # return {
        #     "request": request_payload,
        #     "response": response_payload,
        # }
        return response_payload

    async def cancel_order(
        self,
        symbol: str,
        order_index: int,
        *,
        nonce: int | None = None,
        api_key_index: int | None = None,
    ) -> dict[str, Any]:
        """Cancel a single order using the signer client."""

        market_index = self.get_contract_id(symbol)
        if market_index is None:
            raise ValueError(f"Unknown symbol: {symbol}")
        market_index = int(market_index)

        if self.signer is None:
            raise RuntimeError("SignerClient is required for cancelling orders")

        nonce_value = nonce if nonce is not None else -1
        api_key_idx = api_key_index or self.api_key_index

        cancel_tx, response, error = await self.signer.cancel_order(
            market_index=market_index,
            order_index=order_index,
            nonce=nonce_value,
            api_key_index=api_key_idx,
        )

        if error:
            raise RuntimeError(f"Lighter cancel_order failed: {error}")
        if response is None:
            raise RuntimeError("Lighter cancel_order returned no response")

        if hasattr(cancel_tx, "to_json"):
            request_payload = json.loads(cancel_tx.to_json())
        else:
            request_payload = str(cancel_tx)
        response_payload = response.to_dict() if hasattr(response, "to_dict") else _maybe_to_dict(response)
        return {
            "request": request_payload,
            "response": response_payload,
        }

    async def update_kline(
        self,
        symbol: str,
        *,
        resolution: str,
        start_timestamp: int,
        end_timestamp: int,
        count_back: int,
        set_timestamp_to_end: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch candlesticks and update the Kline store.

        Parameters
        - symbol: market symbol, e.g. "BTC-USD".
        - resolution: e.g. "1m", "5m", "1h".
        - start_timestamp: epoch milliseconds.
        - end_timestamp: epoch milliseconds.
        - count_back: number of bars to fetch.
        - set_timestamp_to_end: if True, API sets last bar timestamp to the end.
        """

        market_id = self.get_contract_id(symbol)
        if market_id is None:
            # try to refresh metadata once
            await self.update("detail")
            market_id = self.get_contract_id(symbol)
        if market_id is None:
            raise ValueError(f"Unknown symbol: {symbol}")

        resp = await self.candlestick_api.candlesticks(
            market_id=int(market_id),
            resolution=resolution,
            start_timestamp=int(start_timestamp),
            end_timestamp=int(end_timestamp),
            count_back=int(count_back),
            set_timestamp_to_end=bool(set_timestamp_to_end) if set_timestamp_to_end is not None else None,
        )

        # Update store
        self.store.klines._onresponse(resp, symbol=symbol, resolution=resolution)

        payload = _maybe_to_dict(resp) or {}
        items = payload.get("candlesticks") or []
        # attach symbol/resolution to return
        out: list[dict[str, Any]] = []
        for it in items:
            if hasattr(it, "to_dict"):
                d = it.to_dict()
            elif hasattr(it, "model_dump"):
                d = it.model_dump()
            else:
                d = dict(it) if isinstance(it, dict) else {"value": it}
            d["symbol"] = symbol
            d["resolution"] = resolution
            out.append(d)
        return out
