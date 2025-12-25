from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Literal, Sequence

import pybotters

from .models.coinw import CoinwFuturesDataStore

logger = logging.getLogger(__name__)


class Coinw:
    """CoinW 永续合约客户端（REST + WebSocket）。"""

    def __init__(
        self,
        client: pybotters.Client,
        *,
        rest_api: str | None = None,
        ws_url: str | None = None,
        web_api: str | None = None,
    ) -> None:
        self.client = client
        self.store = CoinwFuturesDataStore()

        self.rest_api = rest_api or "https://api.coinw.com"
        self.ws_url_public = ws_url or "wss://ws.futurescw.com/perpum"
        self.ws_url_private = self.ws_url_public
        self.web_api = web_api or "https://futuresapi.coinw.com"

        self._ws_private: pybotters.ws.WebSocketApp | None = None
        self._ws_private_ready = asyncio.Event()
        self._ws_headers = {
            "Origin": "https://www.coinw.com",
            "Referer": "https://www.coinw.com/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            ),
        }

    async def __aenter__(self) -> "Coinw":
        await self.update("detail")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - symmetry
        return None

    async def update(
        self,
        update_type: Literal[
            "detail",
            "ticker",
            "orders",
            "position",
            "balance",
            "all",
        ] = "all",
        *,
        position_type: Literal["execute", "plan", "planTrigger"] = "execute",
        page: int | None = None,
        page_size: int | None = None,
        instrument: str | None = None,
    ) -> None:
        """刷新本地缓存，使用 CoinW REST API。

        - detail: ``GET /v1/perpum/instruments`` （公共）
        - ticker: ``GET /v1/perpumPublic/tickers`` （公共）
        - orders: ``GET /v1/perpum/orders/open`` （私有，需要 ``instrument``）
        - position: ``GET /v1/perpum/positions`` （私有，需要 ``instrument``）
        - balance: ``GET /v1/perpum/account/getUserAssets`` （私有）
        """

        requests: list[Any] = []

        include_detail = update_type in {"detail", "all"}
        include_ticker = update_type in {"ticker", "all"}
        include_orders = update_type in {"orders", "all"}
        include_position = update_type in {"position", "all"}
        include_balance = update_type in {"balance", "all"}

        if include_detail:
            requests.append(self.client.get(f"{self.rest_api}/v1/perpum/instruments"))

        if include_ticker:
            requests.append(self.client.get(f"{self.rest_api}/v1/perpumPublic/tickers"))

        if include_orders:
            if not instrument:
                raise ValueError("instrument is required when updating orders")
            params: dict[str, Any] = {
                "instrument": instrument,
                "positionType": position_type,
            }
            if page is not None:
                params["page"] = page
            if page_size is not None:
                params["pageSize"] = page_size
            requests.append(
                self.client.get(
                    f"{self.rest_api}/v1/perpum/orders/open",
                    params=params,
                )
            )

        if include_position:
            requests.append(
                self.client.get(f"{self.rest_api}/v1/perpum/positions/all")
            )

        if include_balance:
            requests.append(
                self.client.get(f"{self.rest_api}/v1/perpum/account/getUserAssets")
            )

        if not requests:
            raise ValueError(f"update_type err: {update_type}")

        await self.store.initialize(*requests)

    async def place_order(
        self,
        instrument: str,
        *,
        direction: Literal["long", "short"],
        leverage: int,
        quantity: float | str,
        quantity_unit: Literal[0, 1, 2, "quote", "contract", "base"] = 0,
        position_model: Literal[0, 1, "isolated", "cross"] = 0,
        position_type: Literal["execute", "plan", "planTrigger"] = "execute",
        price: float | None = None,
        trigger_price: float | None = None,
        trigger_type: Literal[0, 1] | None = None,
        stop_loss_price: float | None = None,
        stop_profit_price: float | None = None,
        third_order_id: str | None = None,
        use_almighty_gold: bool | None = None,
        gold_id: int | None = None,
    ) -> dict[str, Any]:
        """``POST /v1/perpum/order`` 下单。"""

        payload: dict[str, Any] = {
            "instrument": instrument,
            "direction": self._normalize_direction(direction),
            "leverage": int(leverage),
            "quantityUnit": self._normalize_quantity_unit(quantity_unit),
            "quantity": self._format_quantity(quantity),
            "positionModel": self._normalize_position_model(position_model),
            "positionType": position_type,
        }

        if price is not None:
            payload["openPrice"] = price
        if trigger_price is not None:
            payload["triggerPrice"] = trigger_price
        if trigger_type is not None:
            payload["triggerType"] = int(trigger_type)
        if stop_loss_price is not None:
            payload["stopLossPrice"] = stop_loss_price
        if stop_profit_price is not None:
            payload["stopProfitPrice"] = stop_profit_price
        if third_order_id:
            payload["thirdOrderId"] = third_order_id
        if use_almighty_gold is not None:
            payload["useAlmightyGold"] = int(bool(use_almighty_gold))
        if gold_id is not None:
            payload["goldId"] = int(gold_id)

        res = await self.client.post(
            f"{self.rest_api}/v1/perpum/order",
            data=payload,
        )

        data = await res.json()
        return self._ensure_ok("place_order", data)

    async def close_position(
        self,
        open_id: str | int,
        *,
        position_type: Literal["plan", "planTrigger", "execute"] = "plan",
        close_num: str | float | int | None = None,
        close_rate: str | float | int | None = None,
        order_price: str | float | None = None,
        instrument: str | None = None,
    ) -> dict[str, Any]:
        """关闭单个仓位（``DELETE /v1/perpum/positions``）。

        Params
        ------
        open_id: ``openId`` / 持仓唯一 ID。
        position_type: 订单类型 ``plan`` / ``planTrigger`` / ``execute``。
        close_num: 按合约数量平仓（与 ``close_rate`` 至少指定其一）。
        close_rate: 按比例平仓（0-1）。
        order_price: 限价平仓时指定价格。
        instrument: 交易品种（部分情况下需要传入，例如限价单）。
        """

        if close_num is None and close_rate is None:
            raise ValueError("close_num or close_rate must be provided")

        payload: dict[str, Any] = {
            "id": str(open_id),
            "positionType": position_type,
        }
        if close_num is not None:
            payload["closeNum"] = str(close_num)
        if close_rate is not None:
            payload["closeRate"] = str(close_rate)
        if order_price is not None:
            payload["orderPrice"] = str(order_price)
        if instrument is not None:
            payload["instrument"] = instrument

        res = await self.client.delete(
            f"{self.rest_api}/v1/perpum/positions",
            data=payload,
        )
        data = await res.json()
        return self._ensure_ok("close_position", data)

    async def place_order_web(
        self,
        instrument: str,
        *,
        direction: Literal["long", "short"],
        leverage: int | str,
        quantity_unit: Literal[0, 1, 2],
        quantity: str | float | int,
        position_model: Literal[0, 1] = 1,
        position_type: Literal["plan", "planTrigger", "execute"] = 'plan',
        open_price: str | float | None = None,
        contract_type: int = 1,
        data_type: str = "trade_take",
        device_id: str,
        token: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """使用 Web 前端接口下单，绕过部分 API 频控策略。

        注意此接口需要传入真实浏览器参数，如 ``device_id`` 与 ``token``。
        """

        if not device_id or not token:
            raise ValueError("device_id and token are required for place_order_web")

        url = f"{self.web_api}/v1/futuresc/thirdClient/trade/{instrument}/open"

        payload: dict[str, Any] = {
            "instrument": instrument,
            "direction": direction,
            "leverage": str(leverage),
            "quantityUnit": quantity_unit,
            "quantity": str(quantity),
            "positionModel": position_model,
            "positionType": position_type,
            "contractType": contract_type,
            "dataType": data_type,
        }
        if open_price is not None:
            payload["openPrice"] = str(open_price)

        base_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh_CN",
            "appversion": "100.100.100",
            "cache-control": "no-cache",
            "clienttag": "web",
            "content-type": "application/json",
            "cwdeviceid": device_id,
            "deviceid": device_id,
            "devicename": "Chrome V141.0.0.0 (macOS)",
            "language": "zh_CN",
            "logintoken": token,
            "origin": "https://www.coinw.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://www.coinw.com/",
            "sec-ch-ua": '"Microsoft Edge";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "selecttype": "USD",
            "systemversion": "macOS 10.15.7",
            "thirdappid": "coinw",
            "thirdapptoken": token,
            "token": token,
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 "
                "Safari/537.36 Edg/141.0.0.0"
            ),
            "withcredentials": "true",
            "x-authorization": token,
            "x-language": "zh_CN",
            "x-locale": "zh_CN",
            "x-requested-with": "XMLHttpRequest",
        }
        if headers:
            base_headers.update(headers)

        res = await self.client.post(
            url,
            json=payload,
            headers=base_headers,
            auth=None,
        )
        return await res.json()

    async def cancel_order(self, order_id: str | int) -> dict[str, Any]:
        """``DELETE /v1/perpum/order`` 取消单个订单。"""

        res = await self.client.delete(
            f"{self.rest_api}/v1/perpum/order",
            data={"id": str(order_id)},
        )
        data = await res.json()
        return self._ensure_ok("cancel_order", data)

    async def sub_personal(self) -> None:
        """订阅订单、持仓、资产私有频道。"""

        ws_app = await self._ensure_private_ws()
        payloads = [
            {"event": "sub", "params": {"biz": "futures", "type": "order"}},
            # {"event": "sub", "params": {"biz": "futures", "type": "position"}},
            {"event": "sub", "params": {"biz": "futures", "type": "position_change"}},
            {"event": "sub", "params": {"biz": "futures", "type": "assets"}},
        ]
        for payload in payloads:
            if ws_app.current_ws.closed:
                raise ConnectionError("CoinW private websocket closed before subscription.")
            await ws_app.current_ws.send_json(payload)
            await asyncio.sleep(0.05)

    async def sub_orderbook(
        self,
        pair_codes: Sequence[str] | str,
        *,
        depth_limit: int | None = 1,
        biz: str = "futures",
        stale_timeout: float = 5,
    ) -> pybotters.ws.WebSocketApp:
        """订阅 ``type=depth`` 订单簿数据，批量控制发送频率。"""

        if isinstance(pair_codes, str):
            pair_codes = [pair_codes]

        pair_list = [code for code in pair_codes if code]
        if not pair_list:
            raise ValueError("pair_codes must not be empty")

        self.store.book.limit = depth_limit

        subscriptions = [
            {"event": "sub", "params": {"biz": biz, "type": "depth", "pairCode": code}}
            for code in pair_list
        ]

        ws_app = self.client.ws_connect(
            self.ws_url_public,
            hdlr_json=self.store.onmessage,
            headers=self._ws_headers,
        )
        await ws_app._event.wait()

        chunk_size = 10

        async def send_subs(target: pybotters.ws.WebSocketApp) -> None:
            for idx in range(0, len(subscriptions), chunk_size):
                batch = subscriptions[idx : idx + chunk_size]
                for msg in batch:
                    await target.current_ws.send_json(msg)
                if idx + chunk_size < len(subscriptions):
                    await asyncio.sleep(2.05)

        await send_subs(ws_app)

        ws_ref: dict[str, pybotters.ws.WebSocketApp] = {"app": ws_app}

        async def monitor() -> None:
            poll_interval = 1.0
            while True:
                await asyncio.sleep(poll_interval)
                last_update = self.store.book.last_update
                if not last_update:
                    continue
                if time.time() - last_update < stale_timeout:
                    continue

                logger.warning(f"CoinW订单簿超过{stale_timeout:.1f}秒未更新，正在重连。")
                try:
                    current = ws_ref["app"]
                    if current.current_ws and not current.current_ws.closed:
                        await current.current_ws.close()
                except Exception:
                    logger.exception("Error closing stale CoinW orderbook websocket")

                try:
                    new_ws = self.client.ws_connect(
                        self.ws_url_public,
                        hdlr_json=self.store.onmessage,
                        headers=self._ws_headers,
                    )
                    await new_ws._event.wait()
                    await send_subs(new_ws)
                    ws_ref["app"] = new_ws
                except Exception:
                    logger.exception("Failed to reconnect CoinW orderbook websocket")

        asyncio.create_task(monitor())

        return ws_app

    async def _ensure_private_ws(self) -> pybotters.ws.WebSocketApp:

        ws_app = self.client.ws_connect(
            self.ws_url_private,
            hdlr_json=self.store.onmessage,
            headers=self._ws_headers,
        )
        await ws_app._event.wait()
        await ws_app.current_ws._wait_authtask()

        return ws_app

    @staticmethod
    def _normalize_direction(direction: str) -> str:
        allowed = {"long", "short"}
        value = str(direction).lower()
        if value not in allowed:
            raise ValueError(f"Unsupported direction: {direction}")
        return value

    @staticmethod
    def _normalize_quantity_unit(
        unit: Literal[0, 1, 2, "quote", "contract", "base"],
    ) -> int:
        mapping = {
            0: 0,
            1: 1,
            2: 2,
            "quote": 0,
            "contract": 1,
            "base": 2,
        }
        try:
            return mapping[unit]  # type: ignore[index]
        except KeyError as exc:  # pragma: no cover - guard
            raise ValueError(f"Unsupported quantity_unit: {unit}") from exc

    @staticmethod
    def _normalize_position_model(
        model: Literal[0, 1, "isolated", "cross"],
    ) -> int:
        mapping = {
            0: 0,
            1: 1,
            "isolated": 0,
            "cross": 1,
        }
        try:
            return mapping[model]  # type: ignore[index]
        except KeyError as exc:  # pragma: no cover - guard
            raise ValueError(f"Unsupported position_model: {model}") from exc

    @staticmethod
    def _format_quantity(quantity: float | str) -> str:
        if isinstance(quantity, str):
            return quantity
        return str(quantity)

    @staticmethod
    def _ensure_ok(operation: str, data: Any) -> dict[str, Any]:
        """CoinW REST 成功时返回 ``{'code': 0, ...}``。"""

        if not isinstance(data, dict) or data.get("code") != 0:
            raise RuntimeError(f"{operation} failed: {data}")
        payload = data.get("data")
        if isinstance(payload, dict):
            return payload
        return {"data": payload}
