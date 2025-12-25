from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Any

import pybotters
from pybotters.store import DataStore
from pybotters.ws import ClientWebSocketResponse


@dataclass
class _SideBook:
    is_ask: bool
    levels: dict[float, tuple[str, str]] = field(default_factory=dict)
    heap: list[tuple[float, float]] = field(default_factory=list)

    def clear(self) -> None:
        self.levels.clear()
        self.heap.clear()

    def update_levels(self, updates: list[list[Any]] | None, snapshot: bool) -> None:
        if updates is None:
            return

        if snapshot:
            self.clear()

        for entry in updates:
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                continue
            price, size = entry[0], entry[1]
            price_val = self._float(price)
            size_val = self._float(size)
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
    def _float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class Book(DataStore):
    """只维护卖一/买一价的轻量级（book1）深度数据。"""

    _KEYS = ["s", "S"]

    def _init(self) -> None:
        self._book: dict[str, dict[str, _SideBook]] = {}

    def _side(self, symbol: str, side: str) -> _SideBook:
        symbol_book = self._book.setdefault(symbol, {})
        side_book = symbol_book.get(side)
        if side_book is None:
            side_book = _SideBook(is_ask=(side == "a"))
            symbol_book[side] = side_book
        return side_book

    def _sync_side(self, symbol: str, side: str, best: tuple[str, str] | None) -> None:
        key = {"s": symbol, "S": side}
        current = self.get(key)

        if best is None:
            if current:
                self._delete([key])
            return

        price, size = best
        if current and current.get("p") == price and current.get("q") == size:
            return

        payload = {"s": symbol, "S": side, "p": price, "q": size}
        if current:
            self._update([payload])
        else:
            self._insert([payload])

    def _on_message(self, msg: dict[str, Any]) -> None:
        b_type = msg.get("type")
        if b_type not in {"snapshot", "delta"}:
            return

        data = msg.get("data") or {}
        if not data:
            return

        symbol = data.get("s")
        if not symbol:
            return

        asks = self._side(symbol, "a")
        bids = self._side(symbol, "b")

        is_snapshot = b_type == "snapshot"
        asks.update_levels(data.get("a"), snapshot=is_snapshot)
        bids.update_levels(data.get("b"), snapshot=is_snapshot)

        best_ask = asks.best()
        best_bid = bids.best()

        self._sync_side(symbol, "a", best_ask)
        self._sync_side(symbol, "b", best_bid)


store = Book()

def callback(msg, ws: ClientWebSocketResponse = None):
    topic = msg.get('topic')
    if not topic:
        return
    if 'orderBook' in topic:
        store._on_message(msg)
        

async def main():
    async with pybotters.Client() as client:
        # webData2
        client.ws_connect(
            "wss://quote.omni.apex.exchange/realtime_public",
            send_json={"op":"subscribe","args":["orderBook25.H.BTCUSDT"]},
            hdlr_json=callback
        )

        while True:
            await asyncio.sleep(1)
            print(store.find())

if __name__ == "__main__":
    asyncio.run(main())
