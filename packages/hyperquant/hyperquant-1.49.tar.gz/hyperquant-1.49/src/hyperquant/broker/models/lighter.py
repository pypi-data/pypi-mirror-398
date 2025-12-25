from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Iterable, Literal, Sequence

from pybotters.store import DataStore, DataStoreCollection

if TYPE_CHECKING:
    from pybotters.typedefs import Item
    from pybotters.ws import ClientWebSocketResponse


def _maybe_to_dict(payload: Any) -> Any:
    """Convert pydantic models to dict, keeping plain dict/list untouched."""
    if payload is None:
        return None
    if hasattr(payload, "to_dict"):
        return payload.to_dict()
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload


class Book(DataStore):
    """Order book snapshots sourced from Lighter websocket feeds."""

    _KEYS = ["s", "S", "p"]

    def _init(self) -> None:
        self.limit: int | None = None
        self.id_to_symbol: dict[str, str] = {} # broker设置
        self._last_update: float = 0.0
        self._state: dict[str, dict[str, dict[float, float]]] = {}
        self._visible: dict[str, dict[str, dict[float, dict[str, Any]]]] = {}

    @staticmethod
    def _market_id_from_channel(channel: str | None) -> str | None:
        if not channel:
            return None
        if ":" in channel:
            return channel.split(":", 1)[1]
        if "/" in channel:
            return channel.split("/", 1)[1]
        return channel


    @staticmethod
    def _make_entry(symbol: str, side: Literal["a", "b"], price: float, size: float) -> dict[str, Any]:
        return {
            "s": symbol,
            "S": side,
            "p": f"{price}",
            "q": f"{abs(size)}",
        }

    def _on_message(self, msg: dict[str, Any]) -> None:
        msg_type = msg.get("type")
        if msg_type not in {"subscribed/order_book", "update/order_book"}:
            return

        market_id = self._market_id_from_channel(msg.get("channel"))
        if market_id is None:
            return

        order_book = msg.get("order_book")
        if not isinstance(order_book, dict):
            return

        state = self._state.setdefault(market_id, {"ask": {}, "bid": {}})
        visible = self._visible.setdefault(market_id, {"a": {}, "b": {}})

        symbol = self.id_to_symbol.get(market_id)
        if symbol is None:
            symbol = market_id

        for side_name, updates_data in (("ask", order_book.get("asks")), ("bid", order_book.get("bids"))):
            side_state = state[side_name]
            if not updates_data:
                continue
            for level in updates_data:
                price = level.get("price")
                size = level.get("size") or level.get("remaining_base_amount") or level.get("base_amount")
                if price is None or size is None:
                    continue
                try:
                    price_val = float(price)
                    size_val = float(size)
                except (TypeError, ValueError):
                    continue
                if size_val <= 0:
                    side_state.pop(price_val, None)
                else:
                    side_state[price_val] = size_val

        def build_visible(side_name: Literal["ask", "bid"]) -> dict[float, dict[str, Any]]:
            side_state = state[side_name]
            reverse = side_name == "bid"
            sorted_levels = sorted(side_state.items(), reverse=reverse)
            if self.limit is not None:
                sorted_levels = sorted_levels[: self.limit]
            entry_side = "a" if side_name == "ask" else "b"
            return {
                price: self._make_entry(symbol, entry_side, price, size)
                for price, size in sorted_levels
            }

        new_visible = {
            "a": build_visible("ask"),
            "b": build_visible("bid"),
        }

        removals: list[dict[str, Any]] = []
        updates: list[dict[str, Any]] = []

        for side_key in ("a", "b"):
            prev_side = visible[side_key]
            next_side = new_visible[side_key]

            for price, entry in prev_side.items():
                if price not in next_side:
                    removals.append({k: entry[k] for k in self._KEYS})

            for price, entry in next_side.items():
                prev_entry = prev_side.get(price)
                if prev_entry is None or prev_entry.get("q") != entry.get("q"):
                    updates.append(entry)

        if removals:
            self._delete(removals)
        if updates:
            self._update(updates)

        self._visible[market_id] = new_visible
        self._last_update = time.time()

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
    """Market metadata."""

    _KEYS = ["symbol"]

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        order_books = payload.get("order_books") or payload.get("order_book_details") or []

        if isinstance(order_books, dict):
            order_books = list(order_books.values())

        normalized: list[dict[str, Any]] = []
        for entry in order_books or []:
            if not isinstance(entry, dict):
                continue
            market_id = entry.get("market_id") or entry.get("id")
            symbol = entry.get("symbol")
            if market_id is None and symbol is None:
                continue
            record = dict(entry)
            if market_id is None and symbol is not None:
                record["market_id"] = symbol
            normalized.append(record)

        self._clear()
        if normalized:
            self._insert(normalized)


class Orders(DataStore):
    """Active orders."""

    _KEYS = ["order_id"]

    def _init(self) -> None:
        self.id_to_symbol: dict[str, str] = {}  # broker设置

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        order_id = entry.get("order_id") or entry.get("orderId")
        if order_id is None:
            return None
        normalized = dict(entry)
        normalized["order_id"] = str(order_id)
        return normalized

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        orders = payload.get("orders") or []
        items: list[dict[str, Any]] = []
        for entry in orders:
            if not isinstance(entry, dict):
                continue
            normalized = self._normalize(entry)
            if self.id_to_symbol:
                market_id = entry.get("market_index")
                if market_id is not None:
                    symbol = self.id_to_symbol.get(str(market_id))
                    if symbol is not None and normalized is not None:
                        normalized["symbol"] = symbol

            if normalized:
                items.append(normalized)
                
        self._clear()
        if items:
            self._insert(items)

    def _on_message(self, msg: dict[str, Any]) -> None:
        """Handle websocket incremental updates for orders.

        For WS updates we should not clear-and-reinsert. Instead:
        - For fully filled or cancelled orders => delete
        - Otherwise => update/insert
        """
        if not isinstance(msg, dict):
            return

        orders_obj = msg.get("orders")
        if orders_obj is None:
            account = msg.get("account")
            if isinstance(account, dict):
                orders_obj = account.get("orders")
        if not orders_obj:
            return

        # Normalize orders to a flat list of dicts
        if isinstance(orders_obj, dict):
            raw_list: list[dict[str, Any]] = []
            for _, lst in orders_obj.items():
                if isinstance(lst, list):
                    raw_list.extend([o for o in lst if isinstance(o, dict)])
        elif isinstance(orders_obj, list):
            raw_list = [o for o in orders_obj if isinstance(o, dict)]
        else:
            return

        def _is_terminal(order: dict[str, Any]) -> bool:
            status = str(order.get("status", "")).lower()
            if status in {"cancelled", "canceled", "executed", "filled", "closed", "done"}:
                return True
            rem = order.get("remaining_base_amount")
            try:
                return float(rem) <= 0 if rem is not None else False
            except Exception:
                return False


        for entry in raw_list:
            normalized = self._normalize(entry)
            if normalized is None:
                continue
            # enrich with symbol if mapping is available
            if self.id_to_symbol:
                market_id = entry.get("market_index")
                if market_id is not None:
                    symbol = self.id_to_symbol.get(str(market_id))
                    if symbol is not None:
                        normalized["symbol"] = symbol

            self._update([normalized])
            if _is_terminal(entry):
                self._delete([normalized])





class Accounts(DataStore):
    """Account level balances and metadata."""

    _KEYS = ["account_index"]

    def _normalize_account(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        account_index = entry.get("account_index") or entry.get("index")
        if account_index is None:
            return None
        normalized = dict(entry)
        normalized["account_index"] = account_index
        normalized.pop("positions", None)
        return normalized

    def _on_accounts(self, accounts: Iterable[dict[str, Any]]) -> None:
        normalized: list[dict[str, Any]] = []
        for account in accounts:
            if not isinstance(account, dict):
                continue
            record = self._normalize_account(account)
            if record:
                normalized.append(record)
        if not normalized:
            return
        keys = [{"account_index": record["account_index"]} for record in normalized]
        self._delete(keys)
        self._insert(normalized)

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        accounts = payload.get("accounts") or []
        self._on_accounts(accounts)

    def _on_message(self, msg: dict[str, Any]) -> None:
        account = msg.get("account")
        if not isinstance(account, dict):
            return
        self._on_accounts([account])


class Positions(DataStore):
    """Per-market positions grouped by account."""

    _KEYS = ["account_index", "market_id"]

    def _init(self) -> None:
        self.id_to_symbol: dict[str, str] = {}  # broker设置

    @staticmethod
    def _normalize(
        account_index: Any,
        position: dict[str, Any],
    ) -> dict[str, Any] | None:
        market_id = position.get("market_id")
        if account_index is None or market_id is None:
            return None
        normalized = dict(position)
        normalized["account_index"] = account_index
        normalized["market_id"] = market_id
        return normalized

    def _update_positions(
        self,
        account_index: Any,
        positions: Sequence[dict[str, Any]] | None,
    ) -> None:
        if positions is None:
            return
        items: list[dict[str, Any]] = []
        for position in positions:
            if not isinstance(position, dict):
                continue
            record = self._normalize(account_index, position)
            if record:
                items.append(record)
        if not items:
            return
        keys = [{"account_index": item["account_index"], "market_id": item["market_id"]} for item in items]
        self._delete(keys)
        self._insert(items)

    def _onresponse(self, data: Any) -> None:
        payload = _maybe_to_dict(data) or {}
        accounts = payload.get("accounts") or []
        for account in accounts:
            if not isinstance(account, dict):
                continue
            account_index = account.get("account_index") or account.get("index")
            positions = account.get("positions")
            self._update_positions(account_index, positions)

    def _on_message(self, msg: dict[str, Any]) -> None:
        account = msg.get("account")
        if not isinstance(account, dict):
            return
        account_index = account.get("account_index") or account.get("index")
        positions = account.get("positions")
        self._update_positions(account_index, positions)


class Klines(DataStore):
    """Candlestick/Kline store keyed by (symbol, resolution, timestamp).

    - Maintains a list of active resolutions in ``_res_list`` (populated by REST updates).
    - Updates candles in real-time by aggregating trade websocket messages.
    """

    _KEYS = ["symbol", "resolution", "timestamp"]

    def _init(self) -> None:
        self.id_to_symbol: dict[str, str] = {}
        self._current_symbol: str | None = None
        self._res_list: list[str] = []
        # Track last processed trade_id to deduplicate snapshot trades after reconnect
        self._last_trade_id_by_market: dict[str, int] = {}
        self._last_trade_id_by_symbol: dict[str, int] = {}

    @staticmethod
    def _resolution_to_ms(resolution: str) -> int | None:
        try:
            res = resolution.strip().lower()
        except Exception:
            return None
        # Common forms: 1m, 5m, 1h, 1d; also allow pure digits => seconds
        unit = res[-1]
        num_part = res[:-1] if unit in {"s", "m", "h", "d", "w"} else res
        try:
            n = int(num_part)
        except Exception:
            return None
        if unit == "s":
            return n * 1000
        if unit == "m" or unit not in {"s", "h", "d", "w"}:  # default minutes if no unit
            return n * 60 * 1000
        if unit == "h":
            return n * 60 * 60 * 1000
        if unit == "d":
            return n * 24 * 60 * 60 * 1000
        if unit == "w":
            return n * 7 * 24 * 60 * 60 * 1000
        return None

    @staticmethod
    def _market_id_from_channel(channel: str | None) -> str | None:
        if not channel:
            return None
        if ":" in channel:
            return channel.split(":", 1)[1]
        if "/" in channel:
            return channel.split("/", 1)[1]
        return channel

    def _compose_item(
        self,
        *,
        symbol: str,
        resolution: str,
        ts: int,
        price: float,
        size: float,
        last_trade_id: int | None,
        open_price: float | None = None,
    ) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "resolution": resolution,
            "timestamp": ts,
            "open": price if open_price is None else float(open_price),
            "high": price,
            "low": price,
            "close": price,
            "volume0": abs(size),
            "volume1": abs(size) * price,
            "last_trade_id": last_trade_id or 0,
        }

    def _ensure_backfill(self, *, symbol: str, resolution: str, new_bucket_ts: int) -> None:
        """Backfill missing empty bars up to (but not including) new_bucket_ts.

        Uses the last known close as O/H/L/C for synthetic bars and zero volume.
        """
        step = self._resolution_to_ms(resolution)
        if not step:
            return
        # find the last existing bar before new_bucket_ts
        rows = self.find({"symbol": symbol, "resolution": resolution})
        prev = None
        prev_ts = None
        for r in rows:
            try:
                ts = int(r.get("timestamp"))
            except Exception:
                continue
            if ts < new_bucket_ts and (prev_ts is None or ts > prev_ts):
                prev = r
                prev_ts = ts
        if prev is None or prev_ts is None:
            return
        expected = prev_ts + step
        while expected < new_bucket_ts:
            prev_close = float(prev.get("close"))
            fill_item = {
                "symbol": symbol,
                "resolution": resolution,
                "timestamp": expected,
                "open": prev_close,
                "high": prev_close,
                "low": prev_close,
                "close": prev_close,
                "volume0": 0.0,
                "volume1": 0.0,
                "last_trade_id": int(prev.get("last_trade_id", 0)) if prev.get("last_trade_id") is not None else 0,
            }
            self._insert([fill_item])
            prev = fill_item
            expected += step

    def _merge_trade(self, *, symbol: str, trade_ts_ms: int, price: float, size: float, last_trade_id: int | None) -> None:
        # Iterate active resolutions
        for res in list(self._res_list):
            interval_ms = self._resolution_to_ms(res)
            if not interval_ms:
                continue
            bucket_ts = (trade_ts_ms // interval_ms) * interval_ms
            # Upsert logic
            existing = self.get({"symbol": symbol, "resolution": res, "timestamp": bucket_ts})
            if existing is None:
                # backfill any missing empty bars before creating a new bucket
                self._ensure_backfill(symbol=symbol, resolution=res, new_bucket_ts=bucket_ts)
                # open should be previous bar's close if exists; if none, fall back to current price
                prev = None
                rows = self.find({"symbol": symbol, "resolution": res})
                prev_ts = None
                for r in rows:
                    try:
                        ts = int(r.get("timestamp"))
                    except Exception:
                        continue
                    if ts < bucket_ts and (prev_ts is None or ts > prev_ts):
                        prev = r
                        prev_ts = ts
                open_px = float(prev.get("close")) if prev is not None else price
                self._insert([
                    self._compose_item(
                        symbol=symbol,
                        resolution=res,
                        ts=bucket_ts,
                        price=price,
                        size=size,
                        last_trade_id=last_trade_id,
                        open_price=open_px,
                    )
                ])
                continue
            # merge into existing
            updated = dict(existing)
            o = float(updated.get("open", price))
            h = float(updated.get("high", price))
            l = float(updated.get("low", price))
            c = float(updated.get("close", price))
            v0 = float(updated.get("volume0", 0.0))
            v1 = float(updated.get("volume1", 0.0))
            p = float(price)
            s = abs(float(size))
            updated["open"] = o
            updated["high"] = max(h, p)
            updated["low"] = min(l, p)
            updated["close"] = p
            updated["volume0"] = v0 + s
            updated["volume1"] = v1 + s * p
            if last_trade_id is not None:
                try:
                    updated["last_trade_id"] = max(int(last_trade_id), int(updated.get("last_trade_id", 0)))
                except Exception:
                    updated["last_trade_id"] = int(last_trade_id)
            self._update([updated])

    def _onresponse(self, data: Any, *, symbol: str | None = None, resolution: str | None = None) -> None:
        payload = _maybe_to_dict(data) or {}
        candlesticks = payload.get("candlesticks") or []
        res = payload.get("resolution") or resolution
        if res not in self._res_list and res is not None:
            self._res_list.append(res)

        sym = symbol or self._current_symbol

        # Sort incoming bars by timestamp to backfill in order
        items: list[dict[str, Any]] = []
        for c in sorted((candlesticks or []), key=lambda x: x.get("timestamp", 0)):
            if not isinstance(c, dict):
                continue
            entry = dict(c)
            if sym is not None:
                entry["symbol"] = sym
            if res is not None:
                entry["resolution"] = res
            items.append(entry)

        # Insert or update per bar; backfill gaps before inserting new bars
        for entry in items:
            sym_i = entry.get("symbol")
            res_i = entry.get("resolution")
            ts_i = entry.get("timestamp")
            if sym_i is None or res_i is None or ts_i is None:
                continue
            if self.get({"symbol": sym_i, "resolution": res_i, "timestamp": ts_i}) is None:
                self._ensure_backfill(symbol=sym_i, resolution=res_i, new_bucket_ts=int(ts_i))
                self._insert([entry])
            else:
                self._update([entry])

        # Update last_trade_id baseline (by symbol) from REST bars if available
        if sym is not None:
            max_tid = 0
            for e in items:
                try:
                    tid = int(e.get("last_trade_id", 0))
                except Exception:
                    tid = 0
                if tid > max_tid:
                    max_tid = tid
            if max_tid:
                prev = self._last_trade_id_by_symbol.get(sym, 0)
                if max_tid > prev:
                    self._last_trade_id_by_symbol[sym] = max_tid

    def _on_message(self, msg: dict[str, Any]) -> None:
        msg_type = msg.get("type")
        if msg_type not in {"subscribed/trade", "update/trade"}:
            return
        market_id = self._market_id_from_channel(msg.get("channel"))
        if market_id is None:
            return
        market_id_str = str(market_id)
        symbol = self.id_to_symbol.get(market_id_str) or market_id_str
        trades = msg.get("trades") or []
        # Baseline last trade_id from market and symbol
        base_last_tid = max(
            self._last_trade_id_by_market.get(market_id_str, 0),
            self._last_trade_id_by_symbol.get(symbol, 0),
        )
        # Process in ascending trade_id order for stability
        try:
            trades_sorted = sorted(trades, key=lambda x: int(x.get("trade_id", 0)))
        except Exception:
            trades_sorted = trades

        last_tid = base_last_tid
        for t in trades_sorted:
            if not isinstance(t, dict):
                continue
            ts = t.get("timestamp")
            price = t.get("price")
            size = t.get("size")
            trade_id = t.get("trade_id")
            try:
                ts = int(ts)
                p = float(price)
                s = float(size)
                tid = int(trade_id) if trade_id is not None else 0
            except Exception:
                continue
            # Skip stale or duplicate snapshot trades
            if tid and last_tid and tid <= last_tid:
                continue
            self._merge_trade(symbol=symbol, trade_ts_ms=ts, price=p, size=s, last_trade_id=tid)
            if tid > last_tid:
                last_tid = tid

        # Persist last processed trade_id for this market
        if last_tid and last_tid > base_last_tid:
            self._last_trade_id_by_market[market_id_str] = last_tid

    


class LighterDataStore(DataStoreCollection):
    """Data store collection for the Lighter exchange."""

    def _init(self) -> None:
        self._create("book", datastore_class=Book)
        self._create("detail", datastore_class=Detail)
        self._create("orders", datastore_class=Orders)
        self._create("accounts", datastore_class=Accounts)
        self._create("positions", datastore_class=Positions)
        self._create("klines", datastore_class=Klines)

    def set_id_to_symbol(self, id_to_symbol: dict[str, str]) -> None:
        self.id_to_symbol = id_to_symbol
        self.book.id_to_symbol = self.id_to_symbol
        self.orders.id_to_symbol = self.id_to_symbol
        self.positions.id_to_symbol = self.id_to_symbol
        self.klines.id_to_symbol = self.id_to_symbol

    def onmessage(self, msg: Item, ws: ClientWebSocketResponse | None = None) -> None:

        msg_type = msg.get("type")
        if msg_type == "ping":
            asyncio.create_task(ws.send_json({"type": "pong"}))
            return
        
        if isinstance(msg, dict):
            msg_type = msg.get("type")
            if msg_type in {"subscribed/order_book", "update/order_book"}:
                self.book._on_message(msg)
            elif msg_type in {"subscribed/account_all", "update/account_all"}:
                self.accounts._on_message(msg)
                self.positions._on_message(msg)
                self.orders._on_message(msg)
            elif msg_type in {"subscribed/account_all_orders", "update/account_all_orders"}:
                self.orders._on_message(msg)
            elif msg_type in {"subscribed/trade", "update/trade"}:
                self.klines._on_message(msg)


    @property
    def book(self) -> Book:
        """
        Lighter 深度快照。

        .. code:: json

            {
                "s": "BTC-USD",
                "S": "a",  # \"a\"=ask / \"b\"=bid
                "p": "50250.5",
                "q": "0.37"
            }
        """
        return self._get("book")

    @property
    def detail(self) -> Detail:
        """
        `lighter.models.OrderBookDetail` 元数据。

        .. code:: json

            [
                {
                    "symbol": "DOLO",
                    "market_id": 75,
                    "status": "active",
                    "taker_fee": "0.0000",
                    "maker_fee": "0.0000",
                    "liquidation_fee": "1.0000",
                    "min_base_amount": "30.0",
                    "min_quote_amount": "10.000000",
                    "supported_size_decimals": 1,
                    "supported_price_decimals": 5,
                    "supported_quote_decimals": 6,
                    "order_quote_limit": ""
                }
            ]
        """
        return self._get("detail")

    @property
    def orders(self) -> Orders:
        """
        活动订单（`lighter.models.Order`）。

        .. code:: json

            {
                "order_index": 21673573193817727,
                "client_order_index": 0,
                "order_id": "21673573193817727",
                "client_order_id": "0",
                "market_index": 75,
                "symbol": "DOLO",
                "owner_account_index": 311464,
                "initial_base_amount": "146.7",
                "price": "0.07500",
                "nonce": 281474963807871,
                "remaining_base_amount": "146.7",
                "is_ask": false,
                "base_size": 1467,
                "base_price": 7500,
                "filled_base_amount": "0.0",
                "filled_quote_amount": "0.000000",
                "side": "",
                "type": "limit",
                "time_in_force": "good-till-time",
                "reduce_only": false,
                "trigger_price": "0.00000",
                "order_expiry": 1764082202799,
                "status": "open",
                "trigger_status": "na",
                "trigger_time": 0,
                "parent_order_index": 0,
                "parent_order_id": "0",
                "to_trigger_order_id_0": "0",
                "to_trigger_order_id_1": "0",
                "to_cancel_order_id_0": "0",
                "block_height": 75734444,
                "timestamp": 1761663003,
                "created_at": 1761663003,
                "updated_at": 1761663003
            }
        """
        return self._get("orders")


    @property
    def accounts(self) -> Accounts:
        """
        账户概览（`lighter.models.DetailedAccount`）。

        .. code:: json
            [
                {
                    "code": 0,
                    "account_type": 0,
                    "index": 311464,
                    "l1_address": "0x5B3f0AdDfaf4c1d8729e266b22093545EFaE6c0e",
                    "cancel_all_time": 0,
                    "total_order_count": 1,
                    "total_isolated_order_count": 0,
                    "pending_order_count": 0,
                    "available_balance": "30.000000",
                    "status": 0,
                    "collateral": "30.000000",
                    "account_index": 311464,
                    "name": "",
                    "description": "",
                    "can_invite": false,
                    "referral_points_percentage": "",
                    "total_asset_value": "30",
                    "cross_asset_value": "30",
                    "shares": []
                }
            ]
        """
        return self._get("accounts")

    @property
    def positions(self) -> Positions:
        """
        账户持仓（`lighter.models.AccountPosition`）。

        .. code:: json

        [
            {
                "market_id": 75,
                "symbol": "DOLO",
                "initial_margin_fraction": "33.33",
                "open_order_count": 1,
                "pending_order_count": 0,
                "position_tied_order_count": 0,
                "sign": 1,
                "position": "129.8",
                "avg_entry_price": "0.08476",
                "position_value": "10.969398",
                "unrealized_pnl": "-0.032450",
                "realized_pnl": "0.000000",
                "liquidation_price": "0",
                "margin_mode": 0,
                "allocated_margin": "0.000000",
                "account_index": 311464
            }
        ]
        """
        return self._get("positions")

    @property
    def klines(self) -> "Klines":
        """
        K线/蜡烛图数据（`lighter.models.Candlesticks` -> `lighter.models.Candlestick`）。

        .. code:: json

            {
                "symbol": "BTC",
                "timestamp": 1730612700000,
                "open": 68970.5,
                "high": 69012.3,
                "low": 68890.0,
                "close": 68995.1,
                "volume0": 12.34,
                "volume1": 850000.0,
                "resolution": "1m"
            }
        """
        return self._get("klines")
