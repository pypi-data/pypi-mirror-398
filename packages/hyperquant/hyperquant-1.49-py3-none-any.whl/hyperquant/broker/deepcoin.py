from __future__ import annotations

import asyncio
import logging
import time
from contextlib import suppress
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN, ROUND_HALF_UP
from typing import Any, Sequence, Literal

import pybotters

from .models.deepcoin import DeepCoinDataStore

logger = logging.getLogger(__name__)


class DeepCoin:
    """DeepCoin 合约客户端（REST + WebSocket）。"""

    def __init__(
        self,
        client: pybotters.Client,
        *,
        rest_api: str | None = None,
        ws_public: str | None = None,
        ws_private: str | None = None,
        inst_type: str = "SWAP",
    ) -> None:
        self.client = client
        self.store = DeepCoinDataStore()

        self.rest_api = rest_api or "https://api.deepcoin.com"
        self.ws_public = (
            ws_public
            or "wss://stream.deepcoin.com/streamlet/trade/public/swap?platform=api"
        )
        self.ws_private = ws_private or "wss://stream.deepcoin.com/v1/private"
        self.inst_type = inst_type

        self._ws_public: pybotters.ws.WebSocketApp | None = None
        self._ws_public_ready = asyncio.Event()
        self._ws_private: pybotters.ws.WebSocketApp | None = None
        self._ws_private_ready = asyncio.Event()
        self._listen_key: str | None = None
        self._listen_key_expire_at: float = 0.0
        self._listen_key_task: asyncio.Task | None = None
        self._listen_key_lock = asyncio.Lock()

    async def __aenter__(self) -> "DeepCoin":
        await self.update("detail")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - symmetry
        await self.aclose()

    async def aclose(self) -> None:
        if self._ws_public is not None:
            await self._ws_public.current_ws.close()
            self._ws_public = None
            self._ws_public_ready.clear()
        if self._ws_private is not None:
            await self._ws_private.current_ws.close()
            self._ws_private = None
            self._ws_private_ready.clear()
        if self._listen_key_task is not None:
            self._listen_key_task.cancel()
            with suppress(Exception):
                await self._listen_key_task
            self._listen_key_task = None
        self._listen_key = None
        self._listen_key_expire_at = 0.0

    async def update(
        self,
        update_type: Literal[
            "all", "detail", "ticker", "orders", "positions", "balances", "trades", "orders-history"
        ] = "all",
        *,
        inst_type: str | None = None,
        inst_id: str | None = None,
        symbol: str | None = None,
        page: int = 1,
        limit: int | None = None,
    ) -> None:
        """刷新本地缓存（detail / ticker / 私有数据）。"""

        inst = inst_type or self.inst_type
        requests: list[Any] = []

        include_detail = update_type in {"detail", "all"}
        include_ticker = update_type in {"ticker", "all"}
        include_orders = update_type in {"orders"} or (update_type == "all" and inst_id)
        include_history_orders = update_type in {"orders-history"}
        include_positions = update_type in {"position", "positions", "all"}
        include_balances = update_type in {"balance", "balances", "account", "all"}
        include_trades = update_type in {"trade", "trades"} or (
            update_type == "all" and inst_id
        )

        if include_detail:
            params = {"instType": inst}
            requests.append(
                self.client.get(
                    f"{self.rest_api}/deepcoin/market/instruments", params=params
                )
            )

        if include_ticker:
            params = {"instType": inst}
            requests.append(
                self.client.get(
                    f"{self.rest_api}/deepcoin/market/tickers", params=params
                )
            )
        
        if include_history_orders:
            params = {"instType": inst}
            if limit:
                params["limit"] = limit

            requests.append(
                self.client.get(
                    f"{self.rest_api}/deepcoin/trade/orders-history",
                    params=params,
                )
            )

        if include_orders:
            if not inst_id:
                raise ValueError("inst_id is required when updating orders")
            params = {"instId": inst_id, "index": page}
            if limit is not None:
                params["limit"] = limit
            requests.append(
                self.client.get(
                    f"{self.rest_api}/deepcoin/trade/v2/orders-pending",
                    params=params,
                )
            )

        if include_positions:
            params = {"instType": inst}

            requests.append(
                self.client.get(
                    f"{self.rest_api}/deepcoin/account/positions",
                    params=params,
                )
            )

        if include_balances:
            params = {"instType": inst}
            requests.append(
                self.client.get(
                    f"{self.rest_api}/deepcoin/account/balances",
                    params=params,
                )
            )

        if include_trades:
            if not inst_id:
                raise ValueError("inst_id is required when updating trades")
            params = {"instId": inst_id}
            if limit is not None:
                params["limit"] = limit
            requests.append(
                self.client.get(
                    f"{self.rest_api}/deepcoin/trade/fills",
                    params=params,
                )
            )

        if not requests:
            raise ValueError(f"Unsupported update_type: {update_type}")

        await self.store.initialize(*requests)

    async def sub_ticker(
        self,
        symbols: Sequence[str] | str,
        *,
        resume_no: int = -1,
        local_no_start: int = 1,
        action: str = "1",
    ) -> pybotters.ws.WebSocketApp:
        """订阅 PO 频道（顶深度行情）。"""

        if isinstance(symbols, str):
            symbol_list = [symbols]
        else:
            symbol_list = list(symbols)

        if not symbol_list:
            raise ValueError("symbols must not be empty")

        payload: list[dict[str, Any]] = []
        for idx, symbol in enumerate(symbol_list):
            payload.append(
                {
                    "SendTopicAction": {
                        "Action": action,
                        "FilterValue": f"DeepCoin_{symbol}",
                        "LocalNo": local_no_start + idx,
                        "ResumeNo": resume_no,
                        "TopicID": "7",
                    }
                }
            )

        ws_app = self.client.ws_connect(
            self.ws_public,
            send_json=payload if len(payload) > 1 else payload[0],
            hdlr_json=self.store.onmessage,
        )

        await ws_app._event.wait()
        self._ws_public = ws_app
        self._ws_public_ready.set()
        return ws_app

    async def sub_orderbook(
        self,
        symbols: Sequence[str] | str,
        **kwargs: Any,
    ) -> pybotters.ws.WebSocketApp:
        """订阅顶档深度（PO 频道）的别名。"""

        return await self.sub_ticker(symbols, **kwargs)

    async def _acquire_listen_key(self) -> str:
        res = await self.client.get(f"{self.rest_api}/deepcoin/listenkey/acquire")
        payload = await res.json()
        data = payload.get("data") or {}
        listen_key = data.get("listenkey")
        if not listen_key:
            raise RuntimeError(f"Failed to acquire DeepCoin listenKey: {payload}")
        expire_time = data.get("expire_time")
        self._listen_key = listen_key
        self._listen_key_expire_at = (
            float(expire_time) if expire_time else time.time() + 3600
        )
        return listen_key

    async def _extend_listen_key(self) -> None:
        if not self._listen_key:
            raise RuntimeError("listenKey not initialized")
        params = {"listenkey": self._listen_key}
        res = await self.client.get(
            f"{self.rest_api}/deepcoin/listenkey/extend", params=params
        )
        payload = await res.json()
        data = payload.get("data") or {}
        expire_time = data.get("expire_time")
        if expire_time:
            self._listen_key_expire_at = float(expire_time)

    async def _ensure_listen_key(self) -> str:
        async with self._listen_key_lock:
            now = time.time()
            if self._listen_key and now < self._listen_key_expire_at - 300:
                return self._listen_key
            if self._listen_key and now < self._listen_key_expire_at - 60:
                await self._extend_listen_key()
                return self._listen_key
            return await self._acquire_listen_key()

    async def _keep_listen_key_alive(self) -> None:
        try:
            while True:
                await asyncio.sleep(1800)
                if self._listen_key is None:
                    continue
                try:
                    await self._extend_listen_key()
                except Exception:
                    logger.exception("DeepCoin listenKey keepalive failed")
        except asyncio.CancelledError:  # pragma: no cover - task control flow
            pass

    async def sub_private(self) -> pybotters.ws.WebSocketApp:
        """订阅私有频道，推送订单/资金/持仓/成交。"""

        if self._ws_private is not None and not self._ws_private.closed:
            return self._ws_private

        listen_key = await self._ensure_listen_key()
        url = f"{self.ws_private}?listenKey={listen_key}"
        ws_app = self.client.ws_connect(
            url,
            hdlr_json=self.store.onmessage,
        )
        await ws_app._event.wait()
        self._ws_private = ws_app
        self._ws_private_ready.set()
        if self._listen_key_task is None or self._listen_key_task.done():
            self._listen_key_task = asyncio.create_task(self._keep_listen_key_alive())
        return ws_app

    # ------------------------------------------------------------------
    # Helpers

    async def _ensure_detail_cache(self) -> None:
        if not self.store.detail.find():
            await self.update("detail")

    async def _resolve_instrument(
        self,
        inst_id: str | None = None,
        symbol: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        await self._ensure_detail_cache()

        entries = list(self.store.detail.find())

        def _enrich(detail: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
            if not detail:
                return None
            inst = detail.get("instId")
            if not inst:
                base = detail.get("baseCcy") or detail.get("base")
                quote = detail.get("quoteCcy") or detail.get("quote")
                inst_type = detail.get("instType")
                if base and quote:
                    inst = f"{base}-{quote}"
                    if inst_type:
                        inst = f"{inst}-{str(inst_type).upper()}"
            if inst:
                detail = dict(detail)
                detail["instId"] = inst
                return inst, detail
            return None

        if inst_id:
            search_keys = {
                inst_id,
                inst_id.upper(),
                inst_id.replace("-", ""),
                inst_id.replace("-", "").upper(),
            }
            for detail in entries:
                inst = str(detail.get("instId", ""))
                if inst and inst in search_keys:
                    enriched = _enrich(detail)
                    if enriched:
                        return enriched
                s_val = str(detail.get("s", ""))
                if s_val and s_val in search_keys:
                    enriched = _enrich(detail)
                    if enriched:
                        return enriched

        if symbol:
            normalized_symbol = symbol.replace("-", "").upper()
            for detail in entries:
                s_val = str(detail.get("s", "")).upper()
                inst = str(detail.get("instId", ""))
                inst_compact = inst.replace("-", "").upper()
                if normalized_symbol in {s_val, inst_compact}:
                    enriched = _enrich(detail)
                    if enriched:
                        return enriched

            if normalized_symbol.endswith("USDT") and self.inst_type.upper() == "SWAP":
                base = normalized_symbol[:-4]
                guess = f"{base}-USDT-SWAP"
                return await self._resolve_instrument(inst_id=guess)

        # fallback: refresh detail and try again
        await self.update("detail")
        if inst_id or symbol:
            return await self._resolve_instrument(inst_id=inst_id, symbol=symbol)

        raise ValueError(
            "Unable to resolve instrument; please provide inst_id or symbol"
        )

    @staticmethod
    def _to_decimal(value: float | str | Decimal) -> Decimal:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def _quantize(
        value: Decimal, step: str | float | Decimal | None, rounding
    ) -> Decimal:
        if step is None:
            return value
        step_dec = Decimal(str(step))
        if step_dec == 0:
            return value
        return (value / step_dec).to_integral_value(rounding=rounding) * step_dec

    @staticmethod
    def _ceil_to_step(value: Decimal, step: str | float | Decimal | None) -> Decimal:
        if step is None:
            return value
        step_dec = Decimal(str(step))
        if step_dec == 0:
            return value
        return (value / step_dec).to_integral_value(rounding=ROUND_CEILING) * step_dec

    @staticmethod
    def _decimal_to_str(value: Decimal) -> str:
        s = format(value, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s or "0"
    
    def inst_id_to_symbol(self, inst_id: str) -> str:
        """将 DeepCoin 的 inst_id 转换为标准 symbol 格式。"""
        parts = inst_id.split("-")
        if len(parts) >= 2:
            base = parts[0]
            quote = parts[1]
            return f"{base}{quote}"
        return inst_id
    
    def symbol_to_inst_id(self, symbol: str) -> str:
        """将标准 symbol 格式转换为 DeepCoin 的 inst_id 格式。"""
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            quote = "USDT"
        elif symbol.endswith("USD"):
            base = symbol[:-3]
            quote = "USD"
        else:
            raise ValueError(f"Unsupported symbol format: {symbol}")
        return f"{base}-{quote}-SWAP"

    # ------------------------------------------------------------------
    # Trading APIs

    async def place_order(
        self,
        *,
        inst_id: str | None = None,
        symbol: str | None = None,
        side: Literal["buy", "sell"],
        ord_type: Literal["limit", "market", "post_only", "ioc"],
        qty_contract: float | str | None = None,
        qty_base: float | str | None = None,
        price: float | str | None = None,
        td_mode: Literal["isolated", "cross"] = "cross",
        pos_side: Literal["long", "short", "net"] | None = None,
        mrg_position: Literal["merge", "split"] | None = None,
        reduce_only: bool | None = None,
        ccy: str | None = None,
        cl_ord_id: str | None = None,
        tag: str | None = None,
        close_pos_id: str | None = None,
        tgt_ccy: str | None = None,
        tp_trigger_px: float | str | None = None,
        sl_trigger_px: float | str | None = None,
    ) -> dict[str, Any]:
        """``POST /deepcoin/trade/order`` with precision auto-adjustment.

        {'ordId': '1001113832243662', 'clOrdId': '', 'tag': '', 'sCode': '0', 'sMsg': ''}
        """

        resolved_inst_id, detail = await self._resolve_instrument(
            inst_id=inst_id, symbol=symbol
        )

        lot_step = detail.get("lotSz") or detail.get("step_size")
        tick_step = detail.get("tickSz") or detail.get("tick_size")
        min_size = detail.get("minSz")

        if qty_contract is None and qty_base is None:
            raise ValueError("Either qty_contract or qty_base must be provided")

        contract_value_raw = (
            detail.get("ctVal")
            or detail.get("contractValue")
            or detail.get("faceValue")
            or "1"
        )
        try:
            contract_value_dec = Decimal(str(contract_value_raw))
        except Exception:
            contract_value_dec = Decimal("1")
        if contract_value_dec <= 0:
            contract_value_dec = Decimal("1")

        qty_contract_dec: Decimal | None = None

        if qty_contract is not None:
            qty_contract_dec = self._to_decimal(qty_contract)

        if qty_base is not None:
            qty_base_dec = self._to_decimal(qty_base)
            converted = qty_base_dec / contract_value_dec
            if qty_contract_dec is None:
                qty_contract_dec = converted
            elif abs(qty_contract_dec - converted) > Decimal("1e-8"):
                qty_contract_dec = converted

        if qty_contract_dec is None:
            raise ValueError("Unable to determine qty_contract from inputs")

        qty_contract_dec = self._quantize(qty_contract_dec, lot_step, ROUND_DOWN)
        if min_size is not None:
            min_dec = self._to_decimal(min_size)
            if qty_contract_dec < min_dec:
                qty_contract_dec = self._ceil_to_step(min_dec, lot_step)
        if qty_contract_dec <= 0:
            raise ValueError("qty_contract is too small after precision adjustment")

        payload: dict[str, Any] = {
            "instId": resolved_inst_id,
            "tdMode": td_mode,
            "side": side,
            "ordType": ord_type,
            "sz": self._decimal_to_str(qty_contract_dec),
        }
        if detail.get("instType"):
            payload["instType"] = detail["instType"]

        inst_id_upper = resolved_inst_id.upper()
        requires_pos = inst_id_upper.endswith("-SWAP")
        if requires_pos:
            if pos_side is None:
                effective_pos = "long" if side == "buy" else "short"
            else:
                effective_pos = pos_side
            payload["posSide"] = effective_pos
            if mrg_position or td_mode == "cross":
                payload["mrgPosition"] = mrg_position or "merge"
        elif pos_side is not None:
            payload["posSide"] = pos_side
        if mrg_position and not requires_pos:
            payload["mrgPosition"] = mrg_position

        if ord_type in {"limit", "post_only"}:
            if price is None:
                raise ValueError("price is required for limit/post_only orders")
            price_dec = self._quantize(
                self._to_decimal(price), tick_step, ROUND_HALF_UP
            )
            if price_dec <= 0:
                raise ValueError("price must be positive after precision adjustment")
            payload["px"] = self._decimal_to_str(price_dec)
        elif price is not None:
            price_dec = self._quantize(
                self._to_decimal(price), tick_step, ROUND_HALF_UP
            )
            if price_dec > 0:
                payload["px"] = self._decimal_to_str(price_dec)

        if reduce_only is not None:
            payload["reduceOnly"] = bool(reduce_only)
        if ccy:
            payload["ccy"] = ccy
        if cl_ord_id:
            payload["clOrdId"] = cl_ord_id
        if tag:
            payload["tag"] = tag
        if close_pos_id:
            payload["closePosId"] = close_pos_id
        if tgt_ccy:
            payload["tgtCcy"] = tgt_ccy

        if tp_trigger_px is not None:
            tp_dec = self._quantize(
                self._to_decimal(tp_trigger_px), tick_step, ROUND_HALF_UP
            )
            payload["tpTriggerPx"] = self._decimal_to_str(tp_dec)
        if sl_trigger_px is not None:
            sl_dec = self._quantize(
                self._to_decimal(sl_trigger_px), tick_step, ROUND_HALF_UP
            )
            payload["slTriggerPx"] = self._decimal_to_str(sl_dec)

        res = await self.client.post(
            f"{self.rest_api}/deepcoin/trade/order",
            data=payload,
        )
        data:dict = await res.json()
        code = data.get("code", '0')
        if code != '0':
            raise RuntimeError(f"Failed to place order: {data.get('msg','')}")
        
        data = data.get("data", {})
        sccode = str(data.get("sCode", ""))
        smsg = data.get("sMsg", "")
        if sccode != "0":
            raise RuntimeError(f"Failed to place order: {sccode} {smsg}")
        return data

    async def cancel_order(
        self,
        *,
        inst_id: str | None = None,
        symbol: str | None = None,
        ord_id: str,
    ) -> dict[str, Any]:
        resolved_inst_id, _ = await self._resolve_instrument(
            inst_id=inst_id, symbol=symbol
        )
        payload = {"instId": resolved_inst_id, "ordId": ord_id}
        res = await self.client.post(
            f"{self.rest_api}/deepcoin/trade/cancel-order",
            data=payload,
        )
        resp = await res.json()
        data = resp.get("data", {})
        sc_code = str(data.get("sCode", ""))
        if sc_code != "0":
            raise RuntimeError(f"Failed to cancel order: {resp}")
        return data

    async def get_price_list(
        self,
    ) -> dict[str, Any]:
        
        """
        返回值示例:
        .. code :: json
            {
                "code": 0,
                "msg": "OK",
                "data": [
                    {
                        "ProductGroup": "SwapU",
                        "InstrumentID": "LAYERUSDT",
                        "OpenPrice": 0.2015,
                        "LastPrice": 0.2039,
                        "MarkedPrice": 0.204,
                        "LowerLimitPrice": 0.1022,
                        "UpperLimitPrice": 0.3065,
                        "HighestPrice": 0.2085,
                        "LowestPrice": 0.1929,
                        "Volume": 9747616,
                        "Turnover": 1961292.57819997,
                        "AskPrice1": 0.204,
                        "BidPrice1": 0.2039,
                        "Volume24": 13529402,
                        "Turnover24": 2721574.44530007
                    }
                ]
            }
        """
        
        # https://www.deepcoin.com/v2/public/query/swap/price-list?system=SwapU

        res = await self.client.get(
            f"{self.rest_api}/v2/public/query/swap/price-list",
            params={"system": "SwapU"},
        )

        return await res.json()