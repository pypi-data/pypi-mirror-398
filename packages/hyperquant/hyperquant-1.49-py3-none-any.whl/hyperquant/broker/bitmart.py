from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any, Literal, Optional, Sequence

import pybotters

from .models.bitmart import BitmartDataStore


class Book():
    def __init__(self):
        self.limit: int | None = None
        self.store = {}
    
    def on_message(self, msg: dict[str, Any], ws=None) -> None:
        data = msg.get("data")
        if not isinstance(data, dict):
            return
        symbol = data.get("symbol")
        self.store[symbol] = data
    
    def find(self, query: dict[str, Any]) -> dict[str, Any] | None:
        s = query.get("s")
        S = query.get("S")
        item = self.store.get(s)
        if item:
            if S == "a":
                return [{"s": s, "S": "a", "p": item["asks"][0]['price'], "q": item["asks"][0]['vol']}]
            elif S == "b":
                return [{"s": s, "S": "b", "p": item["bids"][0]['price'], "q": item["bids"][0]['vol']}]
        else:
            return []
            
class BitmartDataStore2(BitmartDataStore):
    def _init(self):
        self.bk = Book()
        return super()._init()

    @property
    def book(self) -> Book:
        return self.bk


class Bitmart:
    """Bitmart 合约交易（REST + WebSocket）。"""

    def __init__(
        self,
        client: pybotters.Client,
        *,
        public_api: str | None = None,
        forward_api: str | None = None,
        ws_url: str | None = None,
        account_index: int | None = None,
        apis: str = None
    ) -> None:
        self.client = client
        self.store = BitmartDataStore2()

        self.public_api = public_api or "https://contract-v2.bitmart.com"
        self.private_api = "https://derivatives.bitmart.com"
        self.forward_api = f'{self.private_api}/gw-api/contract-tiger/forward'
        self.ws_url = ws_url or "wss://contract-ws-v2.bitmart.com/v1/ifcontract/realTime"
        self.api_ws_url = "wss://openapi-ws-v2.bitmart.com/api?protocol=1.1"
        self.api_url = "https://api-cloud-v2.bitmart.com"
        self.account_index = account_index
        self.apis = apis
        self.symbol_to_contract_id: dict[str, str] = {}
        self.book = Book()

    async def __aenter__(self) -> "Bitmart":
        await self.update("detail")
        asyncio.create_task(self.auto_refresh())
        
        for entry in self.store.detail.find():
            contract_id = entry.get("contract_id")
            symbol = entry.get("name") or entry.get("display_name")
            if contract_id is None or symbol is None:
                continue
            self.symbol_to_contract_id[str(symbol)] = str(contract_id)

        return self
    
    async def auto_refresh(self, sec=3600, test=False) -> None:
        """每隔一小时刷新token"""
        client = self.client
        while not client._session.closed:

            await asyncio.sleep(sec)

            if client._session.__dict__["_apis"].get("bitmart") is None:
                continue

            # 执行请求
            res = await client.post(
                f"{self.private_api}/gw-api/gateway/token/v2/renew",
            )

            print(await res.text())
            resp:dict = await res.json()
            if resp.get("success") is False:
                raise ValueError(f"Bitmart refreshToken error: {resp}")

            data:dict = resp.get("data", {})
            new_token = data.get("accessToken")
            secret = data.get("accessSalt")

            # 加载原来的apis
            apis_dict = client._load_apis(self.apis)
            
            device = apis_dict['bitmart'][2]

            apis_dict["bitmart"] = [new_token, secret, device]

            client._session.__dict__["_apis"] = client._encode_apis(apis_dict)
            
            if test:
                print("Bitmart token refreshed.")
                break

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - symmetry
        return None

    def get_contract_id(self, symbol: str) -> str | None:
        """Resolve contract ID from cached detail data."""
        detail = (
            self.store.detail.get({"name": symbol})
            or self.store.detail.get({"display_name": symbol})
            or self.store.detail.get({"contract_id": symbol})
        )
        if detail is None:
            return None
        contract_id = detail.get("contract_id")
        if contract_id is None:
            return None
        return str(contract_id)

    def _get_detail_entry(
        self,
        *,
        symbol: str | None = None,
        market_index: int | None = None,
    ) -> dict[str, Any] | None:
        if symbol:
            entry = (
                self.store.detail.get({"name": symbol})
                or self.store.detail.get({"display_name": symbol})
            )
            if entry:
                return entry

        if market_index is not None:
            entries = self.store.detail.find({"contract_id": market_index})
            if entries:
                return entries[0]
            entries = self.store.detail.find({"contract_id": str(market_index)})
            if entries:
                return entries[0]

        return None

    @staticmethod
    def _normalize_enum(
        value: int | str,
        mapping: dict[str, int],
        field: str,
    ) -> int:
        if isinstance(value, str):
            key = value.lower()
            try:
                return mapping[key]
            except KeyError as exc:
                raise ValueError(f"Unsupported {field}: {value}") from exc
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Unsupported {field}: {value}") from exc

    async def update(
        self,
        update_type: Literal[
            "detail",
            "orders",
            "positions",
            "balances",
            "account",
            "all",
            "history_orders",
            "ticker",
        ] = "all",
        *,
        orders_params: dict[str, Any] | None = None,
        positions_params: dict[str, Any] | None = None,
    ) -> None:
        """Refresh cached REST resources."""

        tasks: dict[str, Any] = {}

        include_detail = update_type in {"detail", "all"}
        include_orders = update_type in {"orders", "all"}
        include_positions = update_type in {"positions", "all"}
        include_balances = update_type in {"balances", "account", "all"}
        include_history_orders = update_type in {"history_orders"}
        include_ticker = update_type in {"ticker", "all"}

        if include_detail:
            tasks["detail"] = self.client.get(f"{self.public_api}/v1/ifcontract/contracts_all")

        if include_orders:
            params = {
                "status": 3,
                "size": 200,
                "orderType": 0,
                "offset": 0,
                "direction": 0,
                "type": 1,
            }
            if orders_params:
                params.update(orders_params)
            tasks["orders"] = self.client.get(
                f"{self.forward_api}/v1/ifcontract/userAllOrders",
                params=params,
            )

        if include_positions:
            params = {"status": 1}
            if positions_params:
                params.update(positions_params)
            tasks["positions"] = self.client.get(
                f"{self.forward_api}/v1/ifcontract/userPositions",
                params=params,
            )

        if include_balances:
            tasks["balances"] = self.client.get(
                f"{self.forward_api}/v1/ifcontract/copy/trade/user/info",
            )

        if include_history_orders:
            d_params = {"offset": 0, "status": 60, "size": 20, "type": 1}
            d_params.update(orders_params or {})
            tasks["history_orders"] = self.client.get(
                f"{self.forward_api}/v1/ifcontract/userAllOrders",
                params=d_params,
            )

        if include_ticker:
            tasks["ticker"] = self.client.get(
                f"{self.public_api}/v1/ifcontract/tickers"
            )

        if not tasks:
            raise ValueError(f"Unsupported update_type: {update_type}")

        results: dict[str, Any] = {}
        for key, req in tasks.items():
            res = await req
            if res.content_type and "json" in res.content_type:
                results[key] = await res.json()
            else:
                text = await res.text()
                try:
                    results[key] = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Unexpected response format for {key}: {res.content_type} {text[:200]}"
                    ) from exc

        if "detail" in results:
            resp = results["detail"]
            if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
                raise ValueError(f"Bitmart detail API error: {resp}")
            self.store.detail._onresponse(resp)
            for entry in self.store.detail.find():
                contract_id = entry.get("contract_id")
                symbol = entry.get("name") or entry.get("display_name")
                if contract_id is None or symbol is None:
                    continue

        if "orders" in results:
            resp = results["orders"]
            if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
                raise ValueError(f"Bitmart orders API error: {resp}")
            self.store.orders._onresponse(resp)

        if "positions" in results:
            resp = results["positions"]
            if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
                raise ValueError(f"Bitmart positions API error: {resp}")
            self.store.positions._onresponse(resp)

        if "balances" in results:
            resp = results["balances"]
            if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
                raise ValueError(f"Bitmart balances API error: {resp}")
            self.store.balances._onresponse(resp)

        if "ticker" in results:
            resp = results["ticker"]
            if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
                raise ValueError(f"Bitmart ticker API error: {resp}")
            self.store.ticker._onresponse(resp)

        if "history_orders" in results:
            resp = results["history_orders"]
            if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
                raise ValueError(f"Bitmart history_orders API error: {resp}")
            self.store.orders._onresponse(resp)

    async def sub_orderbook(
        self,
        symbols: Sequence[str] | str,
        *,
        depth_limit: int | None = None,
    ) -> pybotters.ws.WebSocketApp:
        """Subscribe order book channel(s)."""

        if isinstance(symbols, str):
            symbols = [symbols]
        

        if not symbols:
            raise ValueError("symbols must not be empty")
        if depth_limit is not None:
            self.store.book.limit = depth_limit
        
        hdlr_json = self.store.book.on_message

        channels: list[str] = []
        for symbol in symbols:
            channels.append(f"futures/depthAll5:{symbol}@100ms")

        if not channels:
            raise ValueError("No channels resolved for subscription")

        payload = {"action": "subscribe", "args": channels}

        ws_app = self.client.ws_connect(
            self.api_ws_url,
            send_json=payload,
            hdlr_json=hdlr_json,
            autoping=False,
        )

        await ws_app._event.wait()
        return ws_app
  

    def gen_order_id(self):
        ts = int(time.time() * 1000)  # 13位毫秒时间戳
        rand = random.randint(100000, 999999)  # 6位随机数
        return int(f"{ts}{rand}")
    
    async def place_order(
        self,
        symbol: str,
        *,
        category: Literal[1,2,"limit","market"] = "limit",
        price: float,
        qty: Optional[float] = None,
        qty_contract: Optional[int] = None,
        side: Literal[1, 2, 3, 4, "open_long", "close_short", "close_long", "open_short", "buy", "sell"] = "open_long",
        mode: Literal[1, 2, 3, 4, "gtc", "ioc", "fok", "maker_only", "maker-only", "post_only"] = "gtc",
        open_type: Literal[1, 2, "cross", "isolated"] = "isolated",
        leverage: int | str = 10,
        reverse_vol: int | float = 0,
        trigger_price: float | None = None,
        custom_id: int | str | None = None,
        extra_params: dict[str, Any] | None = None,
        use_api: bool = False,
    ) -> int:
        """Submit an order via ``submitOrder``.
        返回值: order_id (int)
        """
        if qty is None and qty_contract is None:
            raise ValueError("Either qty or qty_contract must be provided.")

        contract_id = self.get_contract_id(symbol)
        if contract_id is None:
            raise ValueError(f"Unknown symbol: {symbol}")
        contract_id_int = int(contract_id)

        detail = self._get_detail_entry(symbol=symbol, market_index=contract_id_int)
        if detail is None:
            await self.update("detail")
            detail = self._get_detail_entry(symbol=symbol, market_index=contract_id_int)
        if detail is None:
            raise ValueError(f"Market metadata unavailable for symbol: {symbol}")

        if qty is not None:

            contract_size_str = detail.get("contract_size") or detail.get("vol_unit") or "1"
            try:
                contract_size_val = float(contract_size_str)
            except (TypeError, ValueError):
                contract_size_val = 1.0
            if contract_size_val <= 0:
                raise ValueError(f"Invalid contract_size for {symbol}: {contract_size_str}")

            contracts_float = float(qty) / contract_size_val
            contracts_int = int(round(contracts_float))
            if contracts_int <= 0:
                raise ValueError(
                    f"Volume too small for contract size ({contract_size_val}): volume={qty}"
                )

        if qty_contract is not None:
            contracts_int = int(qty_contract)
            if contracts_int <= 0:
                raise ValueError(f"Volume must be positive integer contracts: volume={qty_contract}")

        price_unit = detail.get("price_unit") or 1
        try:
            price_unit_val = float(price_unit)
        except (TypeError, ValueError):
            price_unit_val = 1.0
        if price_unit_val <= 0:
            price_unit_val = 1.0

        price_value = float(price)
        adjusted_price = int(price_value / price_unit_val) * price_unit_val

        category = self._normalize_enum(
            category,
            {
                "limit": 1,
                "market": 2,
            },
            "category",
        )

        if category == 2:  # market
            adjusted_price = 0.0
        price_fmt = f"{adjusted_price:.15f}".rstrip("0").rstrip(".") or "0"

        way_value = self._normalize_enum(
            side,
            {
                "open_long": 1,
                "close_short": 2,
                "close_long": 3,
                "open_short": 4,
                "buy": 1,
                "sell": 4,
            },
            "way",
        )
        mode_value = self._normalize_enum(
            mode,
            {
                "gtc": 1,
                "fok": 2,
                "ioc": 3,
                "maker_only": 4,
                "maker-only": 4,
                "post_only": 4,
            },
            "mode",
        )
        open_type_value = self._normalize_enum(
            open_type,
            {
                "cross": 1,
                "isolated": 2,
            },
            "open_type",
        )

        if use_api:
            # Official API path
            order_type_str = "limit" if category == 1 else "market"
            open_type_str = "cross" if open_type_value == 1 else "isolated"
            client_oid = str(custom_id or self.gen_order_id())
            api_payload: dict[str, Any] = {
                "symbol": symbol,
                "client_order_id": client_oid,
                "side": way_value,
                "type": order_type_str,
                "mode": mode_value,
                "leverage": str(leverage),
                "open_type": open_type_str,
                "size": int(contracts_int),
            }
            if order_type_str == "limit":
                api_payload["price"] = price_fmt
            if extra_params:
                api_payload.update(extra_params)
            # Ensure leverage is synchronized via official API before placing order
            try:
                lev_payload = {
                    "symbol": symbol,
                    "leverage": str(leverage),
                    "open_type": open_type_str,
                }
                res_lev = await self.client.post(
                    f"{self.api_url}/contract/private/submit-leverage",
                    json=lev_payload,
                )
                txt_lev = await res_lev.text()
                try:
                    resp_lev = json.loads(txt_lev)
                    if resp_lev.get("code") != 1000:
                        # ignore and proceed; order may still pass
                        pass
                except json.JSONDecodeError:
                    pass
                await asyncio.sleep(0.05)
            except Exception:
                pass

            res = await self.client.post(
                f"{self.api_url}/contract/private/submit-order",
                json=api_payload,
            )
            # Parse response (some errors may return text/plain containing JSON)
            text = await res.text()
            try:
                resp = json.loads(text)
            except json.JSONDecodeError:
                raise ValueError(f"Bitmart API submit-order non-json response: {text[:200]}")
            if resp.get("code") != 1000:
                # Auto-sync leverage once if required, then retry once
                if resp.get("code") in (40012,):
                    try:
                        # Retry leverage sync via official API then retry the order
                        lev_payload = {
                            "symbol": symbol,
                            "leverage": str(leverage),
                            "open_type": open_type_str,
                        }
                        await self.client.post(
                            f"{self.api_url}/contract/private/submit-leverage",
                            json=lev_payload,
                        )
                        await asyncio.sleep(0.05)
                        res2 = await self.client.post(
                            f"{self.api_url}/contract/private/submit-order",
                            json=api_payload,
                        )
                        text2 = await res2.text()
                        try:
                            resp2 = json.loads(text2)
                        except json.JSONDecodeError:
                            raise ValueError(
                                f"Bitmart API submit-order non-json response: {text2[:200]}"
                            )
                        if resp2.get("code") == 1000:
                            return resp2.get("data", {}).get("order_id")
                        else:
                            raise ValueError(f"Bitmart API submit-order error: {resp2}")
                    except Exception:
                        # Fall through to raise original error if sync failed
                        pass
                raise ValueError(f"Bitmart API submit-order error: {resp}")
            return resp.get("data", {}).get("order_id")
        else:
            payload: dict[str, Any] = {
                "place_all_order": False,
                "contract_id": contract_id_int,
                "category": category,
                "price": price_fmt,
                "vol": contracts_int,
                "way": way_value,
                "mode": mode_value,
                "open_type": open_type_value,
                "leverage": leverage,
                "reverse_vol": reverse_vol,
            }

            if trigger_price is not None:
                payload["trigger_price"] = trigger_price

            payload["custom_id"] = custom_id or self.gen_order_id()
            
            if extra_params:
                payload.update(extra_params)
            
            res = await self.client.post(
                f"{self.forward_api}/v1/ifcontract/submitOrder",
                json=payload,
            )
            resp = await res.json()
            
            if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
                raise ValueError(f"Bitmart submitOrder error: {resp}")
            return resp.get("data", {}).get("order_id")

    async def cancel_order(
        self,
        symbol: str,
        order_ids: Sequence[int | str],
        *,
        nonce: int | None = None,
    ) -> dict[str, Any]:
        """Cancel one or multiple orders."""

        contract_id = self.get_contract_id(symbol)
        if contract_id is None:
            raise ValueError(f"Unknown symbol: {symbol}")

        payload = {
            "orders": [
                {
                    "contract_id": int(contract_id),
                    "orders": [int(order_id) for order_id in order_ids],
                }
            ],
            "nonce": nonce if nonce is not None else int(time.time()),
        }

        res = await self.client.post(
            f"{self.forward_api}/v1/ifcontract/cancelOrders",
            json=payload,
        )
        resp = await res.json()
        if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
            raise ValueError(f"Bitmart cancelOrders error: {resp}")
        return resp

    async def get_leverage(
        self,
        *,
        symbol: str | None = None,
        contract_id: int | str | None = None,
    ) -> dict[str, Any]:
        """
        获取指定合约的杠杆信息（可通过 contract_id 或 symbol 查询）。

        参数:
            symbol (str | None): 合约符号，例如 "BTCUSDT"。如果未传入 contract_id，则会自动解析。
            contract_id (int | str | None): 合约 ID，可直接指定。

        返回:
            dict[str, Any]: 杠杆信息字典，典型返回结构如下:
            {
                "contract_id": 1,
                "leverage": 96,             # 当前杠杆倍数
                "open_type": 2,             # 开仓类型 (1=全仓, 2=逐仓)
                "max_leverage": {
                    "contract_id": 1,
                    "leverage": "200",      # 最大可用杠杆倍数
                    "open_type": 0,
                    "imr": "0.005",         # 初始保证金率
                    "mmr": "0.0025",        # 维持保证金率
                    "value": "0"
                }
            }

        异常:
            ValueError: 当未提供 symbol 或 contract_id，或接口返回错误时抛出。

        示例:
            data = await bitmart.get_leverage(symbol="BTCUSDT")
            print(data["leverage"])  # 输出当前杠杆倍数
        """
        if contract_id is None:
            if symbol is not None:
                contract_id = self.get_contract_id(symbol)
            if contract_id is None:
                raise ValueError("Either contract_id or a valid symbol must be provided to get leverage info.")
        res = await self.client.get(
            f"{self.forward_api}/v1/ifcontract/getLeverage",
            params={"contract_id": contract_id},
        )
        resp = await res.json()
        if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
            raise ValueError(f"Bitmart getLeverage error: {resp}")
        return resp.get("data")

    async def bind_leverage(
        self,
        *,
        symbol: str | None = None,
        contract_id: int | str | None = None,
        leverage: int | str,
        open_type: Literal[1, 2] = 2,
    ) -> None:
        """
        绑定（设置）指定合约的杠杆倍数。

        参数:
            symbol (str | None): 合约符号，例如 "BTCUSDT"。若未传入 contract_id，会自动解析。
            contract_id (int | str | None): 合约 ID，可直接指定。
            leverage (int | str): 要设置的杠杆倍数，如 20、50、100。
            open_type (int): 开仓模式，1＝全仓（Cross），2＝逐仓（Isolated）。

        返回:
            None — 如果接口调用成功，不返回任何内容。
                   若失败则抛出 ValueError。

        异常:
            ValueError: 当未提供 symbol 或 contract_id，或接口返回错误时抛出。

        示例:
            await bitmart.bind_leverage(symbol="BTCUSDT", leverage=50, open_type=2)
        """
        if contract_id is None:
            if symbol is not None:
                contract_id = self.get_contract_id(symbol)
            if contract_id is None:
                raise ValueError("Either contract_id or a valid symbol must be provided to bind leverage.")

        payload = {
            "contract_id": int(contract_id),
            "leverage": leverage,
            "open_type": open_type,
        }

        res = await self.client.post(
            f"{self.forward_api}/v1/ifcontract/bindLeverage",
            json=payload,
        )
        resp = await res.json()
        if resp.get("success") is False or resp.get("errno") not in (None, "OK"):
            raise ValueError(f"Bitmart bindLeverage error: {resp}")
        return None
