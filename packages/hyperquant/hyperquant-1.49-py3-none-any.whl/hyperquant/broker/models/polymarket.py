from __future__ import annotations

import json
from dataclasses import dataclass, field
from heapq import heappop, heappush
import time
from typing import TYPE_CHECKING, Any, Iterable

from pybotters.store import DataStore, DataStoreCollection
from pybotters.ws import ClientWebSocketResponse

if TYPE_CHECKING:
    from pybotters.typedefs import Item

   
class Position(DataStore):
    """Position DataStore keyed by Polymarket token id."""

    _KEYS = ["asset"]

    def _init(self) -> None:
        # 缓存LIVE订单已计入的size_matched: {order_id: size_matched}
        self._live_cache: dict[str, float] = {}


    def sorted(
        self, query: Item | None = None, limit: int | None = None
    ) -> dict[str, list[Item]]:
        """按ts降序排列，按outcome分组"""
        if query is None:
            query = {}
        result: dict[str, list[Item]] = {}
        for item in self:
            if all(k in item and query[k] == item[k] for k in query):
                outcome = item.get("outcome") or "unknown"
                if outcome not in result:
                    result[outcome] = []
                result[outcome].append(item)
        for outcome in result:
            result[outcome].sort(key=lambda x: (x.get("eventSlug") or '0'), reverse=True)
            if limit:
                result[outcome] = result[outcome][:limit]
        return result

    def _on_response(self, msg: list[Item]) -> None:
        if msg:
            self._clear()
            for rec in msg:
                rec["ts"] = 0
            self._update(msg)

    def on_trade(self, trade: Item) -> None:
        status = str(trade.get("status") or "").upper()
        if status not in {"MATCHED"}:
            return

        asset_id = trade.get("asset_id")
        outcome = trade.get("outcome")
        side = str(trade.get("side") or "").upper()
        size_raw = trade.get("size")
        price_raw = trade.get("price")


        if not asset_id or not outcome or side not in {"BUY", "SELL"}:
            return

        try:
            size = float(size_raw)
        except (TypeError, ValueError):
            return
        try:
            price = float(price_raw)
        except (TypeError, ValueError):
            price = None



        key = {"asset": asset_id, "outcome": outcome}
        existing = self.get(key) or {}

        cur_size = float(existing.get("size") or 0.0)
        cur_total_bought = float(existing.get("totalBought") or 0.0)
        cur_avg_price = float(existing.get("avgPrice") or 0.0)
        cur_cost = cur_size * cur_avg_price

        if side == "BUY":
            new_size = cur_size + size
            total_bought = cur_total_bought + size
            # 未拿到成交价时使用当前均价兜底，避免均价被拉低
            effective_price = price if price is not None else cur_avg_price
            new_cost = cur_cost + size * effective_price
        else:  # SELL
            new_size = cur_size - size
            total_bought = cur_total_bought
            # 卖出按照当前均价释放成本
            new_cost = cur_cost - min(size, cur_size) * cur_avg_price

        if new_size <= 0:
            new_size = 0.0
            avg_price = 0.0
            new_cost = 0.0
        else:
            avg_price = max(new_cost, 0.0) / new_size

        rec: dict[str, Any] = {
            "asset": asset_id,
            "outcome": outcome,
            "side": side,
            "size": new_size,
            "totalBought": total_bought,
            "avgPrice": avg_price,
        }

        if existing:
            self._update([rec])
        else:
            self._insert([rec])

    def _on_order(self, order: dict[str, Any]) -> None:
        """通过order更新持仓，处理LIVE时部分成交的增量统计"""
        # print(order)
        # order写入本地尝试后续分析
        with open("polymarket_orders.log", "a") as f:
            f.write(json.dumps(order) + "\n")
        order_id = order.get("id")
        asset_id = order.get("asset_id")
        outcome = order.get("outcome")
        side = str(order.get("side") or "").upper()
        size_matched = float(order.get("size_matched") or 0)
        price = float(order.get("price") or 0)
        status = str(order.get("status") or "").upper()

        if not order_id or not asset_id or not outcome or side not in {"BUY", "SELL"}:
            return

        cached = self._live_cache.get(order_id, 0.0)

        if status == "LIVE":
            # LIVE时计算增量
            delta = size_matched - cached
            if delta > 0:
                self._live_cache[order_id] = size_matched
                self._apply_trade(asset_id, outcome, side, delta, price)
        elif status in {"CANCELED", "MATCHED"}:
            # 订单完结：计算最终增量 = 最终size_matched - 已计入的cached
            delta = size_matched - cached
            if delta > 0:
                self._apply_trade(asset_id, outcome, side, delta, price)
            # 清理缓存
            self._live_cache.pop(order_id, None)

    def _apply_trade(self, asset_id: str, outcome: str, side: str, size: float, price: float) -> None:
        """应用成交到持仓"""
        if size <= 0:
            return

        key = {"asset": asset_id, "outcome": outcome}
        existing = self.get(key) or {}

        cur_size = float(existing.get("size") or 0.0)
        cur_total_bought = float(existing.get("totalBought") or 0.0)
        cur_avg_price = float(existing.get("avgPrice") or 0.0)
        cur_cost = cur_size * cur_avg_price

        if side == "BUY":
            new_size = cur_size + size
            total_bought = cur_total_bought + size
            effective_price = price if price else cur_avg_price
            new_cost = cur_cost + size * effective_price
        else:  # SELL
            new_size = cur_size - size
            total_bought = cur_total_bought
            new_cost = cur_cost - min(size, cur_size) * cur_avg_price

        if new_size <= 0:
            new_size = 0.0
            avg_price = 0.0
            new_cost = 0.0
        else:
            avg_price = max(new_cost, 0.0) / new_size

        rec: dict[str, Any] = {
            "asset": asset_id,
            "outcome": outcome,
            "side": side,
            "size": new_size,
            "totalBought": total_bought,
            "avgPrice": avg_price,
            "ts": int(time.time() * 1000),
        }

        if existing:
            self._update([rec])
        else:
            self._insert([rec])



class Fill(DataStore):
    """Fill records keyed by maker order id."""

    _KEYS = ["order_id"]

    @staticmethod
    def _from_trade(trade: dict[str, Any], maker: dict[str, Any]) -> dict[str, Any] | None:
        order_id = maker.get("order_id")
        if not order_id:
            return None

        record = {
            "order_id": order_id,
            "trade_id": trade.get("id"),
            "asset_id": maker.get("asset_id") or trade.get("asset_id"),
            "market": trade.get("market"),
            "outcome": maker.get("outcome") or trade.get("outcome"),
            "matched_amount": maker.get("matched_amount") or trade.get("size"),
            "price": maker.get("price") or trade.get("price"),
            "status": trade.get("status"),
            "match_time": trade.get("match_time") or trade.get("timestamp"),
            "maker_owner": maker.get("owner"),
            "taker_order_id": trade.get("taker_order_id"),
            "side": maker.get("side") or trade.get("side"),
        }

        for key in ("matched_amount", "price"):
            value = record.get(key)
            if value is None:
                continue
            try:
                record[key] = float(value)
            except (TypeError, ValueError):
                pass

        return record

    def _on_trade(self, trade: dict[str, Any]) -> None:
        status = str(trade.get("status") or "").upper()
        if status != "MATCHED":
            return
        maker_orders = trade.get("maker_orders") or []
        upserts: list[dict[str, Any]] = []
        for maker in maker_orders:
            record = self._from_trade(trade, maker)
            if not record:
                continue
            upserts.append(record)

        if not upserts:
            return

        for record in upserts:
            key = {"order_id": record["order_id"]}
            if self.get(key):
                self._update([record])
            else:
                self._insert([record])


class Order(DataStore):
    """User orders keyed by order id (REST + WS)."""

    _KEYS = ["id"]

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        oid = entry.get("id")
        if not oid:
            return None
        normalized = dict(entry)
        # numeric fields
        for field in ("price", "original_size", "size_matched"):
            val = normalized.get(field)
            try:
                if val is not None:
                    normalized[field] = float(val)
            except (TypeError, ValueError):
                pass
        return normalized

    def _on_response(self, items: list[dict[str, Any]] | dict[str, Any]) -> None:
        """增量同步：insert新增、update变更、delete消失的订单"""
        rows: list[dict[str, Any]] = []
        if isinstance(items, dict):
            items = [items]
        for it in items or []:
            norm = self._normalize(it)
            if norm:
                rows.append(norm)

        # 构建新订单id集合
        new_ids = {r["id"] for r in rows}

        # 删除不再存在的订单（传入完整状态）
        to_delete = [dict(item) for item in self if item["id"] not in new_ids]
        if to_delete:
            self._delete(to_delete)

        # 插入或更新
        for row in rows:
            existing = self.get({"id": row["id"]})
            if existing:
                # 有变化才update
                if any(existing.get(k) != row.get(k) for k in row):
                    self._update([row])
            else:
                self._insert([row])

    def _on_message(self, msg: dict[str, Any]) -> None:
        status = str(msg.get("status") or "").upper()
        # CANCELED MATCHED 删除
        order = self.get({"id": msg.get("id")})
        if not order:
            self._insert([msg])

        if status in {"CANCELED", "MATCHED"}:
            self._delete([msg])

class MyTrade(DataStore):
    """User trades keyed by trade id."""

    _KEYS = ["id"]

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any] | None:
        trade_id = entry.get("id")
        if not trade_id:
            return None
        normalized = dict(entry)
        for field in ("price", "size", "fee_rate_bps"):
            value = normalized.get(field)
            if value is None:
                continue
            try:
                normalized[field] = float(value)
            except (TypeError, ValueError):
                pass
        return normalized

    def _on_message(self, msg: dict[str, Any]) -> None:
        normalized = self._normalize(msg) or {}
        trade_id = normalized.get("id")
        if not trade_id:
            return
        if self.get({"id": trade_id}):
            self._update([normalized])
        else:
            self._insert([normalized])

class Trade(DataStore):
    """User trades keyed by trade id."""

    _KEYS = ["hash"]
    _MAXLEN = 500

    def _on_message(self, msg: dict[str, Any]) -> None:
        payload = msg or {}
        if payload:
            if payload.get("event_type") == "last_trade_price":
                transaction_hash = payload.get("transaction_hash")
                if transaction_hash:
                    payload.update({"hash": transaction_hash})
                    payload.pop("transaction_hash", None)
            else:
                if payload.get("transactionHash"):
                    payload.update({"hash": payload.get("transactionHash")})
                    payload.pop("transactionHash", None)

            self._insert([payload])

class Book(DataStore):
    """Full depth order book keyed by Polymarket token id."""

    _KEYS = ["s", "S", "p"]

    def _init(self) -> None:
        self.id_to_alias: dict[str, str] = {}

    def update_aliases(self, mapping: dict[str, str]) -> None:
        if not mapping:
            return
        self.id_to_alias.update(mapping)

    def _alias(self, asset_id: str | None) -> tuple[str, str | None] | tuple[None, None]:
        if asset_id is None:
            return None, None
        alias = self.id_to_alias.get(asset_id)
        return asset_id, alias

    def _normalize_levels(
        self,
        entries: Iterable[dict[str, Any]] | None,
        *,
        side: str,
        symbol: str,
        alias: str | None,
    ) -> list[dict[str, Any]]:
        if not entries:
            return []
        normalized: list[dict[str, Any]] = []
        for entry in entries:
            try:
                price = float(entry["price"])
                size = float(entry["size"])
            except (KeyError, TypeError, ValueError):
                continue
            record = {"s": symbol, "S": side, "p": price, "q": size}
            if alias is not None:
                record["alias"] = alias
            normalized.append(record)
        return normalized

    def _purge_missing_levels(
        self, *, symbol: str, side: str, new_levels: list[dict[str, Any]]
    ) -> None:
        """Remove levels no longer present in the latest snapshot."""
        existing = self.find({"s": symbol, "S": side})
        if not existing:
            return
        new_prices = {lvl["p"] for lvl in new_levels}
        stale = [
            {"s": symbol, "S": side, "p": level["p"]}
            for level in existing
            if level.get("p") not in new_prices
        ]
        if stale:
            self._delete(stale)

    def _on_message(self, msg: dict[str, Any]) -> None:
        msg_type = msg.get("event_type")
        if msg_type not in {"book", "price_change"}:
            return

        if msg_type == "book":
            asset_id = msg.get("asset_id") or msg.get("token_id")
            symbol, alias = self._alias(asset_id)
            if symbol is None:
                return
            bids = self._normalize_levels(msg.get("bids"), side="b", symbol=symbol, alias=alias)
            asks = self._normalize_levels(msg.get("asks"), side="a", symbol=symbol, alias=alias)
            self._purge_missing_levels(symbol=symbol, side="b", new_levels=bids)
            self._purge_missing_levels(symbol=symbol, side="a", new_levels=asks)
            if bids:
                self._insert(bids)
            if asks:
                self._insert(asks)
            return

        price_changes = msg.get("price_changes") or []
        updates: list[dict[str, Any]] = []
        removals: list[dict[str, Any]] = []
        for change in price_changes:
            asset_id = change.get("asset_id") or change.get("token_id")
            symbol, alias = self._alias(asset_id)
            if symbol is None:
                continue
            side = "b" if change.get("side") == "BUY" else "a"
            try:
                price = float(change["price"])
                size = float(change["size"])
            except (KeyError, TypeError, ValueError):
                continue
            record = {"s": symbol, "S": side, "p": price}
            if alias is not None:
                record["alias"] = alias
            if size == 0:
                removals.append({"s": symbol, "S": side, "p": price})
            else:
                record["q"] = size
                updates.append(record)

        if removals:
            self._delete(removals)
        if updates:
            self._update(updates)

    def sorted(
        self, query: Item | None = None, limit: int | None = None
    ) -> dict[str, list[Item]]:
        return self._sorted(
            item_key="S",
            item_asc_key="a",
            item_desc_key="b",
            sort_key="p",
            query=query,
            limit=limit,
        )

@dataclass
class _SideBook:
    is_ask: bool
    levels: dict[float, tuple[str, str]] = field(default_factory=dict)
    heap: list[tuple[float, float]] = field(default_factory=list)

    def clear(self) -> None:
        self.levels.clear()
        self.heap.clear()

    def update_levels(
        self, updates: Iterable[dict[str, Any]] | None, *, snapshot: bool
    ) -> None:
        if updates is None:
            return

        if snapshot:
            self.clear()

        for entry in updates:
            price, size = self._extract(entry)
            price_val = self._to_float(price)
            size_val = self._to_float(size)
            if price_val is None or size_val is None:
                continue

            if size_val <= 0:
                self.levels.pop(price_val, None)
                continue

            self.levels[price_val] = (str(price), str(size))
            priority = price_val if self.is_ask else -price_val
            heappush(self.heap, (priority, price_val))

    def best(self) -> tuple[str, str] | None:
        while self.heap:
            _, price = self.heap[0]
            level = self.levels.get(price)
            if level is not None:
                return level
            heappop(self.heap)
        return None

    @staticmethod
    def _extract(entry: Any) -> tuple[Any, Any]:
        if isinstance(entry, dict):
            price = entry.get("price", entry.get("p"))
            size = entry.get("size", entry.get("q"))
            return price, size
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            return entry[0], entry[1]
        return None, None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

class Price(DataStore):
    _KEYS = ["s"]

    def _on_message(self, msg: dict[str, Any]) -> None:
        payload = msg.get('payload') or {}
        data = payload.get('data') or {}
        symbol = payload.get('symbol')

        if not symbol:
            return
        
        _next = self.get({'s': symbol}) or {}
        _next_price = _next.get('p')
        last_price = None
        
        if data and isinstance(data, list):
            last_price = data[-1].get('value')
        if 'value' in payload:
            last_price = payload.get('value')
        
        if last_price is None:
            return

        record = {'s': symbol, 'p': last_price}
        key = {'s': symbol}
        if self.get(key):
            self._update([record])
        else:
            self._insert([record])


class BBO(DataStore):
    _KEYS = ["s", "S"]

    def _init(self) -> None:
        self._book: dict[str, dict[str, _SideBook]] = {}
        self.id_to_alias: dict[str, str] = {}

    def update_aliases(self, mapping: dict[str, str]) -> None:
        if not mapping:
            return
        self.id_to_alias.update(mapping)

    def _alias(self, asset_id: str | None) -> tuple[str, str | None] | tuple[None, None]:
        if asset_id is None:
            return None, None
        alias = self.id_to_alias.get(asset_id)
        return asset_id, alias

    def _side(self, symbol: str, side: str) -> _SideBook:
        symbol_book = self._book.setdefault(symbol, {})
        side_book = symbol_book.get(side)
        if side_book is None:
            side_book = _SideBook(is_ask=(side == "a"))
            symbol_book[side] = side_book
        return side_book

    def _sync_side(
        self, symbol: str, side: str, best: tuple[str, str] | None, alias: str | None
    ) -> None:
        key = {"s": symbol, "S": side}
        current = self.get(key)

        if best is None:
            if current:
                self._delete([key])
            return

        price, size = best
        payload = {"s": symbol, "S": side, "p": price, "q": size}
        if alias is not None:
            payload["alias"] = alias

        if current:
            cur_price = current.get("p")
            cur_size = current.get("q")
            cur_alias = current.get("alias")

            if cur_price == price:
                # price unchanged -> only update quantities / alias changes
                if cur_size != size or (alias is not None and cur_alias != alias):
                    self._update([payload])
                return

            # price changed -> delete old then insert new level to trigger change watchers
            self._delete([key])

        self._insert([payload])

    def _from_price_changes(self, msg: dict[str, Any]) -> None:
        price_changes = msg.get("price_changes") or []
        touched: dict[str, str | None] = {}
        for change in price_changes:
            asset_id = change.get("asset_id") or change.get("token_id")
            symbol, alias = self._alias(asset_id)
            if symbol is None:
                continue
            side = "b" if str(change.get("side") or "").upper() == "BUY" else "a"
            side_book = self._side(symbol, side)
            side_book.update_levels([change], snapshot=False)
            touched[symbol] = alias

        for symbol, alias in touched.items():
            asks = self._side(symbol, "a")
            bids = self._side(symbol, "b")
            self._sync_side(symbol, "a", asks.best(), alias)
            self._sync_side(symbol, "b", bids.best(), alias)

    def _from_snapshot(self, msg: dict[str, Any]) -> None:
        asset_id = msg.get("asset_id") or msg.get("token_id")
        symbol, alias = self._alias(asset_id)
        if symbol is None:
            return
        asks = self._side(symbol, "a")
        bids = self._side(symbol, "b")
        asks.update_levels(msg.get("asks"), snapshot=True)
        bids.update_levels(msg.get("bids"), snapshot=True)
        self._sync_side(symbol, "a", asks.best(), alias)
        self._sync_side(symbol, "b", bids.best(), alias)

    def _on_message(self, msg: dict[str, Any]) -> None:
        msg_type = (msg.get("event_type") or msg.get("type") or "").lower()
        if msg_type == "book":
            self._from_snapshot(msg)
        elif msg_type == "price_change":
            self._from_price_changes(msg)


class Detail(DataStore):
    """Market metadata keyed by Polymarket token id."""

    _KEYS = ["token_id"]

    @staticmethod
    def _normalize_entry(market: dict[str, Any], token: dict[str, Any]) -> dict[str, Any]:
        slug = market.get("slug")
        outcome = token.get("outcome")
        alias = slug if outcome is None else f"{slug}:{outcome}"

        tick_size = (
            market.get("minimum_tick_size")
            or market.get("orderPriceMinTickSize")
            or market.get("order_price_min_tick_size")
        )
        step_size = (
            market.get("minimum_order_size")
            or market.get("orderMinSize")
            or market.get("order_min_size")
        )

        try:
            tick_size = float(tick_size) if tick_size is not None else None
        except (TypeError, ValueError):
            tick_size = None
        try:
            step_size = float(step_size) if step_size is not None else None
        except (TypeError, ValueError):
            step_size = None

        return {
            "token_id": token.get("token_id") or token.get("id"),
            "asset_id": token.get("token_id") or token.get("id"),
            "alias": alias,
            "question": market.get("question"),
            "outcome": outcome,
            "active": market.get("active"),
            "closed": market.get("closed"),
            "neg_risk": market.get("neg_risk"),
            "tick_size": tick_size if tick_size is not None else 0.01,
            "step_size": step_size if step_size is not None else 1.0,
            "minimum_order_size": step_size if step_size is not None else 1.0,
            "minimum_tick_size": tick_size if tick_size is not None else 0.01,
        }

    def on_response(self, markets: Iterable[dict[str, Any]]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        records: list[dict[str, Any]] = []
        for market in markets or []:
            tokens = market.get("tokens") or []
            if not tokens:
                token_ids = market.get("clobTokenIds") or []
                outcomes = market.get("outcomes") or []

                if isinstance(token_ids, str):
                    try:
                        token_ids = json.loads(token_ids)
                    except json.JSONDecodeError:
                        token_ids = [token_ids]
                if isinstance(outcomes, str):
                    try:
                        outcomes = json.loads(outcomes)
                    except json.JSONDecodeError:
                        outcomes = [outcomes]

                if not isinstance(token_ids, list):
                    token_ids = [token_ids]
                if not isinstance(outcomes, list):
                    outcomes = [outcomes]

                tokens = [
                    {"token_id": tid, "outcome": outcomes[idx] if idx < len(outcomes) else None}
                    for idx, tid in enumerate(token_ids)
                    if tid
                ]

            for token in tokens:
                normalized = self._normalize_entry(market, token)
                slug: str = market.get("slug")
                # 取最后一个'-'之前部分
                base_slug = slug.rsplit("-", 1)[0] if slug else slug
                # Add or update additional fields from market
                normalized.update({
                    "condition_id": market.get("conditionId"),
                    "slug": market.get("slug"),
                    "base_slug": base_slug,
                    "end_date": market.get("endDate"),
                    "start_date": market.get("startDate"),
                    "icon": market.get("icon"),
                    "image": market.get("image"),
                    "liquidity": market.get("liquidityNum") or market.get("liquidity"),
                    "volume": market.get("volumeNum") or market.get("volume"),
                    "accepting_orders": market.get("acceptingOrders"),
                    "spread": market.get("spread"),
                    "best_bid": market.get("bestBid"),
                    "best_ask": market.get("bestAsk"),
                })
                token_id = normalized.get("token_id")
                if not token_id:
                    continue
                records.append(normalized)
                mapping[token_id] = normalized.get("alias") or token_id

        self._update(records)
        return mapping


class PolymarketDataStore(DataStoreCollection):
    """Polymarket-specific DataStore aggregate."""

    def _init(self) -> None:
        self._create("book", datastore_class=Book)
        self._create("bbo", datastore_class=BBO)
        self._create("detail", datastore_class=Detail)
        self._create("position", datastore_class=Position)
        self._create("order", datastore_class=Order)
        self._create("mytrade", datastore_class=MyTrade)
        self._create("fill", datastore_class=Fill)
        self._create("trade", datastore_class=Trade)
        self._create("price", datastore_class=Price)

    @property
    def book(self) -> Book:
        """Order Book DataStore
        _key: k (asset_id), S (side), p (price)

        .. code:: json
            [{
                "k": "asset_id",
                "S": "b" | "a",
                "p": "price",
                "q": "size"
            }]
        """
        return self._get("book")

    @property
    def detail(self) -> Detail:
        """
        Market metadata keyed by token id.

        .. code:: json
            
            [
                {
                    "token_id": "14992165475527298486519422865149275159537493330633013685269145597531945526992",
                    "asset_id": "14992165475527298486519422865149275159537493330633013685269145597531945526992",
                    "alias": "Bitcoin Up or Down - November 12, 12:30AM-12:45AM ET:Down",
                    "question": "Bitcoin Up or Down - November 12, 12:30AM-12:45AM ET",
                    "outcome": "Down",
                    "active": true,
                    "closed": false,
                    "neg_risk": null,
                    "tick_size": 0.01,
                    "step_size": 5.0,
                    "minimum_order_size": 5.0,
                    "minimum_tick_size": 0.01,
                    "condition_id": "0xb64133e5ae9710fab2533cfd3c48cba142347e4bab36822964ca4cca4b7660d2",
                    "slug": "btc-updown-15m-1762925400",
                    "end_date": "2025-11-12T05:45:00Z",
                    "start_date": "2025-11-11T05:32:59.491174Z",
                    "icon": "https://polymarket-upload.s3.us-east-2.amazonaws.com/BTC+fullsize.png",
                    "image": "https://polymarket-upload.s3.us-east-2.amazonaws.com/BTC+fullsize.png",
                    "liquidity": 59948.1793,
                    "volume": 12214.600385,
                    "accepting_orders": true,
                    "spread": 0.01,
                    "best_bid": 0.5,
                    "best_ask": 0.51
                }
            ]
        """

        return self._get("detail")
    
    @property
    def position(self) -> Position:
        """

        .. code:: python
        
            [{
                # 🔑 基础信息
                "proxyWallet": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",  # 代理钱包地址（用于代表用户在链上的交易地址）
                "asset": "<string>",                                          # outcome token 资产地址或 symbol
                "conditionId": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",  # 市场条件 ID（event 的唯一标识）
                
                # 💰 交易与价格信息
                "size": 123,             # 当前持仓数量（仅在未平仓时存在）
                "avgPrice": 123,         # 平均买入价（每个 outcome token 的均价）
                "curPrice": 123,         # 当前市场价格
                "initialValue": 123,     # 初始建仓总价值（avgPrice × size）
                "currentValue": 123,     # 当前持仓市值（curPrice × size）

                # 📊 盈亏指标
                "cashPnl": 123,             # 未实现盈亏（当前浮动盈亏）
                "percentPnl": 123,          # 未实现盈亏百分比
                "realizedPnl": 123,         # 已实现盈亏（平仓后的实际收益）
                "percentRealizedPnl": 123,  # 已实现盈亏百分比（相对成本的收益率）

                # 🧮 累计交易信息
                "totalBought": 123,  # 累计买入数量（含历史）
                
                # ⚙️ 状态标志
                "redeemable": True,   # 是否可赎回（True 表示市场已结算且你是赢家，可提取 USDC）
                "mergeable": True,    # 是否可合并（多笔相同 outcome 可合并为一笔）
                "negativeRisk": True, # 是否为负风险组合（风险对冲导致净敞口为负）
                
                # 🧠 市场元数据
                "title": "<string>",          # 市场标题（如 “Bitcoin up or down 15m”）
                "slug": "<string>",           # outcome 唯一 slug（对应前端页面路径的一部分）
                "eventSlug": "<string>",      # event slug（整个预测事件的唯一路径标识）
                "icon": "<string>",           # 图标 URL（一般为事件关联资产）
                "outcome": "<string>",        # 当前持有的 outcome 名称（例如 “Yes” 或 “No”）
                "outcomeIndex": 123,          # outcome 在该市场中的索引（0 或 1）
                "oppositeOutcome": "<string>",# 对立 outcome 名称
                "oppositeAsset": "<string>",  # 对立 outcome token 地址
                "endDate": "<string>",        # 市场结束时间（UTC ISO 格式字符串）
            }]
        """

        return self._get("position")

    @property
    def orders(self) -> Order:
        """User orders keyed by order id.

        Example row (from REST get_orders):

        .. code:: json
            {
              "id": "0xd4359d…",
              "status": "LIVE",
              "owner": "<api-key>",
              "maker_address": "0x…",
              "market": "0x…",
              "asset_id": "317234…",
              "side": "BUY",
              "original_size": 5.0,
              "size_matched": 0.0,
              "price": 0.02,
              "outcome": "Up",
              "order_type": "GTC",
              "created_at": 1762912331
            }

        """

        return self._get("order")

    @property
    def mytrade(self) -> MyTrade:
        """User trade stream keyed by trade id.

        Columns include Polymarket websocket ``trade`` payloads, e.g.

        .. code:: json
            {
                "event_type": "trade",
                "id": "28c4d2eb-bbea-40e7-a9f0-b2fdb56b2c2e",
                "market": "0xbd31…",
                "asset_id": "521143…",
                "side": "BUY",
                "price": 0.57,
                "size": 10,
                "status": "MATCHED",
                "maker_orders": [ ... ]
            }
        """

        return self._get("trade")
    
    @property
    def price(self) -> Price:
        """Price DataStore
        _key: s 
        """
        return self._get("price")

    @property
    def fill(self) -> Fill:
        """Maker-order fills keyed by ``order_id``.

        A row is created whenever a trade arrives with ``status == 'MATCHED'``.
        ``matched_amount`` and ``price`` are stored as floats for quick PnL math.

        .. code:: json
            {
                "order_id": "0xb46574626be7eb57a8fa643eac5623bdb2ec42104e2dc3441576a6ed8d0cc0ed",
                "owner": "1aa9c6be-02d2-c021-c5fc-0c5b64ba8fd6",
                "maker_address": "0x64A46A989363eb21DAB87CD53d57A4567Ccbc103",
                "matched_amount": "1.35",
                "price": "0.73",
                "fee_rate_bps": "0",
                "asset_id": "60833383978754019365794467018212448484210363665632025956221025028271757152271",
                "outcome": "Up",
                "outcome_index": 0,
                "side": "BUY"
            }
        """

        return self._get("fill")
    
    @property
    def bbo(self) -> BBO:
        """Best Bid and Offer DataStore
        _key: s (asset_id), S (side)

        """
        return self._get("bbo")
    
    @property
    def trade(self) -> Trade:
        """
        _key asset
        MATCHED进行快速捕捉
        .. code:: json
           {
                "asset": "12819879685513143002408869746992985182419696851931617234615358342350852997413",
                "bio": "",
                "conditionId": "0xea609d2c6bc2cb20e328be7c89f258b84b35bbe119b44e0a2cfc5f15e6642b3b",
                "eventSlug": "btc-updown-15m-1763865000",
                "icon": "https://polymarket-upload.s3.us-east-2.amazonaws.com/BTC+fullsize.png",
                "name": "infusion",
                "outcome": "Up",
                "outcomeIndex": 0,
                "price": 0.7,
                "profileImage": "",
                "proxyWallet": "0x2C060830B6F6B43174b1Cf8B4475db07703c1543",
                "pseudonym": "Frizzy-Graduate",
                "side": "BUY",
                "size": 5,
                "slug": "btc-updown-15m-1763865000",
                "timestamp": 1763865085,
                "title": "Bitcoin Up or Down - November 22, 9:30PM-9:45PM ET",
                "hash": "0xddea11d695e811686f83379d9269accf1be581fbcb542809c6c67a3cc3002488"
            }
        """
        return self._get("trade")
    

    def onmessage(self, msg: Any, ws: ClientWebSocketResponse | None = None) -> None:
        # 判定msg是否为list
        lst_msg = msg if isinstance(msg, list) else [msg]
        for m in lst_msg:
            if m == '':
                continue
            topic = m.get("topic") or ""
            if topic in {'crypto_prices_chainlink', 'crypto_prices'}:
                self.price._on_message(m)
                continue
            raw_type = m.get("event_type") or m.get("type")
            if not raw_type:
                continue
            msg_type = str(raw_type).lower()
            if msg_type in {"book", "price_change"}:
                self.book._on_message(m)
            elif msg_type == "order":
                self.orders._on_message(m)
                self.position._on_order(m)

            elif msg_type == "trade":
                self.mytrade._on_message(m)
                # self.fill._on_trade(m)
                # self.position.on_trade(m)
            elif msg_type == 'orders_matched':
                payload = m.get("payload") or {}
                if not payload:
                    continue
                trade_msg = dict(payload)
                if "asset_id" not in trade_msg and "asset" in trade_msg:
                    trade_msg["asset_id"] = trade_msg["asset"]
                self.trade._on_message(trade_msg)
    
    def onmessage_for_bbo(self, msg: Any, ws: ClientWebSocketResponse | None = None) -> None:
        # 判定msg是否为list
        lst_msg = msg if isinstance(msg, list) else [msg]
        for m in lst_msg:
            raw_type = m.get("event_type") or m.get("type")
            if not raw_type:
                continue
            msg_type = str(raw_type).lower()
            if msg_type in {"book", "price_change"}:
                self.bbo._on_message(m)

    def onmessage_for_last_trade(self, msg, ws = None):
        # 判定msg是否为list
        lst_msg = msg if isinstance(msg, list) else [msg]
        for m in lst_msg:
            raw_type = m.get("event_type") or m.get("type")
            if not raw_type:
                continue
            msg_type = str(raw_type).lower()
            if msg_type == "last_trade_price":
                self.trade._on_message(m)