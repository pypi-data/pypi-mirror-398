from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Literal

import pybotters

from .models.bitget import BitgetDataStore
from .lib.util import fmt_value

logger = logging.getLogger(__name__)


class Bitget:
    """Bitget public/privileged client (REST + WS).

    默认只支持单向持仓（One-way mode）。
    """

    def __init__(
        self,
        client: pybotters.Client,
        *,
        rest_api: str | None = None,
        ws_url: str | None = None,
    ) -> None:
        self.client = client
        self.store = BitgetDataStore()

        self.rest_api = rest_api or "https://api.bitget.com"
        self.ws_url = ws_url or "wss://ws.bitget.com/v2/ws/public"
        self.ws_url_private = ws_url or "wss://ws.bitget.com/v2/ws/private"

        self.ws_app = None
        self.has_sub_personal = False
  

    async def __aenter__(self) -> "Bitget":
        await self.update("detail")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - symmetry
        pass

    async def sub_personal(self) -> None:
        sub_msg = {
            "op": "subscribe",
            "args": [
                {"instType": "USDT-FUTURES", "channel": "orders", "instId": "default"},
                {
                    "instType": "USDT-FUTURES",
                    "channel": "positions",
                    "instId": "default",
                },
                {"instType": "USDT-FUTURES", "channel": "account", "coin": "default"},
            ],
        }
        self.ws_app = await self._ensure_private_ws()
        

        await self.ws_app.current_ws.send_json(sub_msg)


        self.has_sub_personal = True

    async def update(
        self,
        update_type: Literal["detail", "ticker", "all"] = "all",
    ) -> None:
        """Refresh cached REST resources."""

        requests: list[Any] = []

        if update_type in {"detail", "all"}:
            requests.append(
                self.client.get(
                    f"{self.rest_api}/api/v2/mix/market/contracts",
                    params={"productType": "usdt-futures"},
                )
            )

        if update_type in {"ticker", "all"}:
            requests.append(
                self.client.get(
                    f"{self.rest_api}/api/v2/mix/market/tickers",
                    params={"productType": "usdt-futures"},
                )
            )

        if not requests:
            raise ValueError(f"update_type err: {update_type}")

        await self.store.initialize(*requests)

    async def place_order(
        self,
        symbol: str,
        *,
        direction: Literal["buy", "sell", "long", "short", "0", "1"],
        volume: float,
        price: float | None = None,
        order_type: Literal[
            "market",
            "limit_gtc",
            "limit_ioc",
            "limit_fok",
            "limit_post_only",
            "limit",
        ] = "market",
        margin_mode: Literal["isolated", "crossed"] = "crossed",
        product_type: str = "USDT-FUTURES",
        margin_coin: str = "USDT",
        reduce_only: bool | None = None,
        offset_flag: Literal["open", "close", "0", "1"] | None = None,
        client_order_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        请求成功返回示例:

        .. code:: json

            {
                "clientOid": "121211212122",
                "orderId": "121211212122"
            }
        """

        side = self._normalize_direction(direction)
        order_type_code, force_code = self._resolve_order_type(order_type)

        if reduce_only is None:
            reduce_only = self._normalize_offset(offset_flag)

        detail = self._get_detail_entry(symbol)
        volume_str = self._format_with_step(
            volume, detail.get("step_size") or detail.get("stepSize")
        )

        payload: dict[str, Any] = {
            "symbol": symbol,
            "productType": product_type,
            "marginMode": margin_mode,
            "marginCoin": margin_coin,
            "side": side,
            "size": volume_str,
            "orderType": order_type_code,
        }

        if force_code:
            payload["force"] = force_code

        if order_type_code == "limit":
            if price is None:
                raise ValueError("price is required for Bitget limit orders")
            payload["price"] = self._format_with_step(
                price,
                detail.get("tick_size") or detail.get("tickSize"),
            )
        elif price is not None:
            logger.debug("Price %.8f ignored for market order", price)

        if reduce_only is True:
            payload["reduceOnly"] = "YES"
        elif reduce_only is False:
            payload["reduceOnly"] = "NO"

        if client_order_id:
            payload["clientOid"] = client_order_id

        res = await self.client.post(
            f"{self.rest_api}/api/v2/mix/order/place-order",
            data=payload,
        )
        data = await res.json()
        return self._ensure_ok("place_order", data)

    async def cancel_order(
        self,
        order_sys_id: str,
        *,
        symbol: str,
        margin_mode: Literal["isolated", "crossed"],
        product_type: str = "USDT-FUTURES",
        margin_coin: str = "USDT",
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """Cancel an order via ``POST /api/v2/mix/order/cancel-order``."""

        payload = {
            "symbol": symbol,
            "productType": product_type,
            "marginMode": margin_mode,
            "marginCoin": margin_coin,
        }

        if client_order_id:
            payload["clientOid"] = client_order_id
        else:
            payload["orderId"] = order_sys_id

        res = await self.client.post(
            f"{self.rest_api}/api/v2/mix/order/cancel-order",
            data=payload,
        )
        data = await res.json()
        return self._ensure_ok("cancel_order", data)

    async def sub_orderbook(self, symbols: list[str], channel: str = "books1") -> None:
        """Subscribe to Bitget order-book snapshots/updates."""

        submsg = {"op": "subscribe", "args": []}
        for symbol in symbols:
            submsg["args"].append(
                {"instType": "USDT-FUTURES", "channel": channel, "instId": symbol}
            )

        self.client.ws_connect(
            self.ws_url,
            send_json=submsg,
            hdlr_json=self.store.onmessage,
        )

    def _get_detail_entry(self, symbol: str) -> dict[str, Any]:
        detail = self.store.detail.get({"symbol": symbol})
        if not detail:
            raise ValueError(
                f"Unknown Bitget instrument: {symbol}. Call update('detail') first or provide valid symbol."
            )
        return detail

    async def _ensure_private_ws(self):
        wsqueue = pybotters.WebSocketQueue()
        ws_app = self.client.ws_connect(
            self.ws_url_private,
            hdlr_json=self.store.onmessage,
        )
        # async for msg in wsqueue:
        #     print(msg)

        await ws_app._event.wait()
        await ws_app.current_ws._wait_authtask()
        return ws_app

    @staticmethod
    def _format_with_step(value: float, step: Any) -> str:
        if step in (None, 0, "0"):
            return str(value)
        try:
            step_float = float(step)
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            return str(value)
        if step_float <= 0:
            return str(value)
        return fmt_value(value, step_float)

    @staticmethod
    def _normalize_direction(direction: str) -> str:
        mapping = {
            "buy": "buy",
            "long": "buy",
            "0": "buy",
            "sell": "sell",
            "short": "sell",
            "1": "sell",
        }
        key = str(direction).lower()
        try:
            return mapping[key]
        except KeyError as exc:  # pragma: no cover - guard
            raise ValueError(f"Unsupported direction: {direction}") from exc

    @staticmethod
    def _normalize_offset(
        offset: Literal["open", "close", "0", "1"] | None,
    ) -> bool | None:
        if offset is None:
            return None
        mapping = {
            "open": False,
            "0": False,
            "close": True,
            "1": True,
        }
        key = str(offset).lower()
        if key in mapping:
            return mapping[key]
        raise ValueError(f"Unsupported offset_flag: {offset}")

    @staticmethod
    def _resolve_order_type(order_type: str) -> tuple[str, str | None]:
        mapping = {
            "market": ("market", None),
            "limit": ("limit", "gtc"),
            "limit_gtc": ("limit", "gtc"),
            "limit_ioc": ("limit", "ioc"),
            "limit_fok": ("limit", "fok"),
            "limit_post_only": ("limit", "post_only"),
        }
        key = str(order_type).lower()
        try:
            return mapping[key]
        except KeyError as exc:  # pragma: no cover - guard
            raise ValueError(f"Unsupported order_type: {order_type}") from exc

    @staticmethod
    def _ensure_ok(operation: str, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict) or data.get("code") != "00000":
            raise RuntimeError(f"{operation} failed: {data}")
        return data.get("data") or {}
