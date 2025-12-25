import asyncio
from typing import Literal, Optional
import pybotters
from .models.ourbit import OurbitSwapDataStore, OurbitSpotDataStore
from decimal import Decimal, ROUND_HALF_UP


class OurbitSwap:

    def __init__(self, client: pybotters.Client):
        """
        ✅ 完成:
            下单, 撤单, 查询资金, 查询持有订单, 查询历史订单

        """
        self.client = client
        self.store = OurbitSwapDataStore()
        self.api_url = "https://futures.ourbit.com"
        self.ws_url = "wss://futures.ourbit.com/edge"

    async def __aenter__(self) -> "OurbitSwap":
        client = self.client
        await self.store.initialize(
            client.get(f"{self.api_url}/api/v1/contract/detailV2?client=web")
        )
        return self

    async def update(
        self,
        update_type: Literal["position", "orders", "balance", "ticker", "all"] = "all",
    ):
        """由于交易所很多不支持ws推送，这里使用Rest"""
        all_urls = [
            f"{self.api_url}/api/v1/private/position/open_positions",
            f"{self.api_url}/api/v1/private/order/list/open_orders?page_size=200",
            f"{self.api_url}/api/v1/private/account/assets",
            f"{self.api_url}/api/v1/contract/ticker",
            f"{self.api_url}/api/platform/spot/market/v2/symbols",
        ]

        url_map = {
            "position": [all_urls[0]],
            "orders": [all_urls[1]],
            "balance": [all_urls[2]],
            "ticker": [all_urls[3]],
            "all": all_urls,
        }

        try:
            urls = url_map[update_type]
        except KeyError:
            raise ValueError(f"update_type err: {update_type}")

        # 直接传协程进去，initialize 会自己 await
        await self.store.initialize(*(self.client.get(url) for url in urls))

    async def sub_tickers(self):
        self.client.ws_connect(
            self.ws_url,
            send_json={"method": "sub.tickers", "param": {"timezone": "UTC+8"}},
            hdlr_json=self.store.onmessage,
        )

    async def sub_orderbook(self, symbols: str | list[str]):
        if isinstance(symbols, str):
            symbols = [symbols]

        send_jsons = []
        # send_json={"method":"sub.depth.step","param":{"symbol":"BTC_USDT","step":"0.1"}},

        for symbol in symbols:
            step = self.store.detail.find({"symbol": symbol})[0].get("tick_size")
            step_str = str(Decimal(str(step)).normalize())

            send_jsons.append(
                {
                    "method": "sub.depth.step",
                    "param": {
                        "symbol": symbol,
                        "step": step_str,
                    },
                }
            )

        await self.client.ws_connect(
            self.ws_url, send_json=send_jsons, hdlr_json=self.store.onmessage
        )

    async def sub_personal(self):
        wsapp = self.client.ws_connect(
            self.ws_url,
            send_json={"method": "sub.personal.user.preference"},
            hdlr_json=self.store.onmessage,
        )
        await wsapp._event.wait()

    def ret_content(self, res: pybotters.FetchResult):
        match res.data:
            case {"success": True}:
                return res.data["data"]
            case _:
                raise Exception(f"Failed api {res.response.url}: {res.data}")

    def fmt_price(self, symbol, price: float) -> float:
        tick = self.store.detail.find({"symbol": symbol})[0].get("tick_size")
        tick_dec = Decimal(str(tick))
        price_dec = Decimal(str(price))
        return float(
            (price_dec / tick_dec).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            * tick_dec
        )

    async def place_order(
        self,
        symbol: str,
        side: Literal["buy", "sell", "close_buy", "close_sell"],
        size: float = None,
        price: float = None,
        order_type: Literal["market", "limit_GTC", "limit_IOC"] = "market",
        usdt_amount: Optional[float] = None,
        leverage: Optional[int] = 20,
        position_id: Optional[int] = None,
        quantity: float = None,  # 兼容参数，不使用
    ):
        """
        size为合约张数, openType 1 为逐仓, 2为全仓

        .. code ::
        {
            "orderId": "219602019841167810",
            "ts": 1756395601543
        }

        """
        if (size is None) == (usdt_amount is None):
            raise ValueError("params err")

        max_lev = self.store.detail.find({"symbol": symbol})[0].get("max_lev")

        if usdt_amount is not None:
            cs = self.store.detail.find({"symbol": symbol})[0].get("contract_sz")
            size = max(int(usdt_amount / cs / price), 1)

        if price is not None:
            price = self.fmt_price(symbol, price)

        leverage = min(max_lev, leverage)

        data = {
            "symbol": symbol,
            "side": 1 if side == "buy" else 3,
            "openType": 2,
            "type": "5",
            "vol": size,
            "leverage": leverage,
            "marketCeiling": False,
            "priceProtect": "0",
        }

        if order_type == "limit_IOC":
            data["type"] = 3
            data["price"] = str(price)
        if order_type == "limit_GTC":
            data["type"] = "1"
            data["price"] = str(price)

        if "close" in side:
            if side == "close_buy":
                data["side"] = 2
            elif side == "close_sell":
                data["side"] = 4

            if position_id is None:
                raise ValueError("position_id is required for closing position")
            data["positionId"] = position_id

        res = await self.client.fetch(
            "POST", f"{self.api_url}/api/v1/private/order/create", data=data
        )
        # 'orderId' =
        # '226474723700166962'
        # 'ts' =
        # 1758034181833
        ret_c = self.ret_content(res)
        # 只返回 orderId
        return ret_c["orderId"]

    async def place_tpsl(
        self,
        position_id: int,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
    ):
        """
        position_id 持仓ID

        .. code:: json

            {
                "success": true,
                "code": 0,
                "data": 2280508
            }
        """
        if (take_profit is None) and (stop_loss is None):
            raise ValueError("params err")

        data = {
            "positionId": position_id,
            "profitTrend": "1",
            "lossTrend": "1",
            "profitLossVolType": "SAME",
            "volType": 2,
            "takeProfitReverse": 2,
            "stopLossReverse": 2,
            "priceProtect": "0",
        }

        if take_profit is not None:
            data["takeProfitPrice"] = take_profit
        if stop_loss is not None:
            data["stopLossPrice"] = stop_loss

        res = await self.client.fetch(
            "POST", f"{self.api_url}/api/v1/private/stoporder/place", data=data
        )

        return self.ret_content(res)

    async def cancel_orders(self, order_ids: list[str]):
        res = await self.client.fetch(
            "POST",
            f"{self.api_url}/api/v1/private/order/cancel",
            data=order_ids,
        )
        return self.ret_content(res)

    async def query_orders(
        self,
        symbol: str,
        states: list[Literal["filled", "canceled"]],  # filled:已成交, canceled:已撤销
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page_size: int = 200,
        page_num: int = 1,
    ):
        """查询历史订单

        Args:
            symbol: 交易对
            states: 订单状态列表 ["filled":已成交, "canceled":已撤销]
            start_time: 开始时间戳(毫秒), 可选
            end_time: 结束时间戳(毫秒), 可选
            page_size: 每页数量, 默认200
            page_num: 页码, 默认1
        """
        state_map = {"filled": 3, "canceled": 4}

        params = {
            "symbol": symbol,
            "states": ",".join(str(state_map[state]) for state in states),
            "page_size": page_size,
            "page_num": page_num,
            "category": 1,
        }

        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        res = await self.client.fetch(
            "GET",
            f"{self.api_url}/api/v1/private/order/list/history_orders",
            params=params,
        )

        return self.ret_content(res)

    async def query_order(self, order_id: str):
        """查询单个订单的详细信息

        Args:
            order_id: 订单ID

        Returns:
            ..code:python

            订单详情数据，例如:
            [
                    {
                        "id": "38600506",          # 成交ID
                        "symbol": "SOL_USDT",      # 交易对
                        "side": 4,                 # 方向(1:买入, 3:卖出, 4:平仓)
                        "vol": 1,                  # 成交数量
                        "price": 204.11,          # 成交价格
                        "fee": 0.00081644,        # 手续费
                        "feeCurrency": "USDT",    # 手续费币种
                        "profit": -0.0034,        # 盈亏
                        "category": 1,            # 品类
                        "orderId": "219079365441409152",  # 订单ID
                        "timestamp": 1756270991000,       # 时间戳
                        "positionMode": 1,        # 持仓模式
                        "voucher": false,         # 是否使用代金券
                        "taker": true            # 是否是taker
                    }
            ]
        """
        res = await self.client.fetch(
            "GET",
            f"{self.api_url}/api/v1/private/order/deal_details/{order_id}",
        )
        return self.ret_content(res)


class OurbitSpot:

    def __init__(self, client: pybotters.Client, personal_msg_cb: callable=None):
        """
        ✅ 完成:
            下单, 撤单, 查询资金, 查询持有订单, 查询历史订单

        """
        self.client = client
        self.store = OurbitSpotDataStore()
        self.api_url = "https://www.ourbit.com"
        self.ws_url = "wss://www.ourbit.com/ws"
        self.personal_msg_cb = personal_msg_cb

    async def __aenter__(self) -> "OurbitSpot":
        client = self.client
        await self.store.initialize(
            client.get(f"{self.api_url}/api/platform/spot/market/v2/symbols")
        )
        return self

    async def update(
        self, update_type: Literal["orders", "balance", "ticker", "book", "all"] = "all"
    ):

        all_urls = [
            f"{self.api_url}/api/platform/spot/order/current/orders/v2?orderTypes=1%2C2%2C3%2C4%2C5%2C100&pageNum=1&pageSize=100&states=0%2C1%2C3",
            f"{self.api_url}/api/assetbussiness/asset/spot/statistic",
            f"{self.api_url}/api/platform/spot/market/v2/tickers",
        ]

        # orderTypes=1%2C2%2C3%2C4%2C5%2C100&pageNum=1&pageSize=100&states=0%2C1%2C3

        url_map = {
            "orders": [all_urls[0]],
            "balance": [all_urls[1]],
            "ticker": [all_urls[2]],
            "all": all_urls,
        }

        try:
            urls = url_map[update_type]
        except KeyError:
            raise ValueError(f"Unknown update type: {update_type}")

        # 直接传协程进去，initialize 会自己 await
        await self.store.initialize(*(self.client.get(url) for url in urls))

    async def sub_personal(self):
        """订阅个人频道"""
        # https://www.ourbit.com/ucenter/api/ws_token
        res = await self.client.fetch("GET", f"{self.api_url}/ucenter/api/ws_token")

        token = res.data["data"].get("wsToken")

        app = self.client.ws_connect(
            f"{self.ws_url}?wsToken={token}&platform=web",
            send_json={
                "method": "SUBSCRIPTION",
                "params": [
                    "spot@private.orders",
                    "spot@private.trigger.orders",
                    "spot@private.balances",
                ],
                "id": 1,
            },
            hdlr_json=(
                self.store.onmessage
                if self.personal_msg_cb is None
                else [self.store.onmessage, self.personal_msg_cb]
            ),
        )

        await app._event.wait()

    async def sub_orderbook(self, symbols: str | list[str]):
        """订阅订单簿深度数据

        Args:
            symbols: 交易对符号，可以是单个字符串或字符串列表
        """
        import logging

        logger = logging.getLogger("OurbitSpot")

        if isinstance(symbols, str):
            symbols = [symbols]

        # 构建订阅参数
        subscription_params = []
        for symbol in symbols:
            subscription_params.append(f"spot@public.increase.aggre.depth@{symbol}")

        # 一次sub20个，超过需要分开订阅
        for i in range(0, len(subscription_params), 20):
            wsapp = self.client.ws_connect(
                "wss://www.ourbit.com/ws?platform=web",
                send_json={
                    "method": "SUBSCRIPTION",
                    "params": subscription_params[i : i + 20],
                    "id": 2,
                },
                hdlr_json=self.store.onmessage,
            )
            await wsapp._event.wait()

        # await asyncio.sleep(1)  # 等待ws连接稳定

        # 并发获取每个交易对的初始深度数据
        tasks = [
            self.client.fetch(
                "GET", f"{self.api_url}/api/platform/spot/market/depth?symbol={symbol}"
            )
            for symbol in symbols
        ]

        # 等待所有请求完成
        responses = await asyncio.gather(*tasks)

        # 处理响应数据
        for idx, response in enumerate(responses):
            symbol = symbols[idx]
            self.store.book._onresponse(response.data)

        async def check_loss():
            await asyncio.sleep(1)
            while True:
                loss = self.store.book.loss
                for symbol, is_loss in loss.items():
                    if is_loss:
                        resp = await self.client.fetch(
                            "GET",
                            f"{self.api_url}/api/platform/spot/market/depth?symbol={symbol}",
                        )
                        self.store.book._onresponse(resp.data)
                await asyncio.sleep(1)

        asyncio.create_task(check_loss())

    async def place_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        price: float = None,
        quantity: float = None,
        order_type: Literal["market", "limit"] = "limit",
        usdt_amount: float = None,
    ):
        """现货下单

        Args:
            symbol: 交易对，如 "SOL_USDT"
            side: 买卖方向 "buy" 或 "sell"
            price: 价格，市价单可为None
            quantity: 数量
            order_type: 订单类型 "market" 或 "limit"
            usdt_amount: USDT金额，如果指定则根据价格计算数量

        Returns:
            订单响应数据
        """
        # 参数检查
        if order_type == "limit" and price is None:
            raise ValueError("Limit orders require a price")
        if quantity is None and usdt_amount is None:
            raise ValueError("Either quantity or usdt_amount must be specified")

        # 解析交易对
        parts = symbol.split("_")
        if len(parts) != 2:
            raise ValueError(f"Invalid symbol format: {symbol}")

        currency, market = parts

        # 获取交易对详情
        detail = self.store.detail.get({"name": currency})
        if not detail:
            raise ValueError(f"Unknown currency: {currency}")

        price_scale = detail.get("price_scale")
        quantity_scale = detail.get("quantity_scale")

        # 构建请求数据
        data = {"currency": currency, "market": market, "tradeType": side.upper()}

        # 处理市价单和限价单的不同参数
        if order_type == "limit":
            data["orderType"] = "LIMIT_ORDER"
            data["price"] = str(
                round(price, price_scale) if price_scale is not None else price
            )

            # 计算并设置数量
            if quantity is None and usdt_amount is not None and price:
                quantity = usdt_amount / price

            if quantity_scale is not None:
                quantity = round(quantity, quantity_scale)
            data["quantity"] = str(quantity)

        elif order_type == "market":
            data["orderType"] = "MARKET_ORDER"

            # 市价单可以使用数量或金额，但不能同时使用
            if usdt_amount is not None:
                data["amount"] = str(usdt_amount)
            else:
                if quantity_scale is not None:
                    quantity = round(quantity, quantity_scale)
                data["quantity"] = str(quantity)

            if price:
                data["price"] = str(price)

        # 确定API端点
        url = f'{self.api_url}/api/platform/spot/{"v4/order/place" if order_type == "market" else "order/place"}'
        # print(f"Placing  {symbol}: {data}")
        # 发送请求
        res = await self.client.fetch("POST", url, json=data)

        # 处理响应
        if res.data.get("msg") == "success":
            return res.data["data"]
        raise Exception(f"Failed to place order: {res.data}")

    async def cancel_orders(self, order_ids: list[str]):

        for order_id in order_ids:
            url = f"{self.api_url}/api/platform/spot/order/cancel/v2?orderId={order_id}"
            await self.client.fetch("DELETE", url)

    async def cancel_order(self, order_id: str):

        url = f"{self.api_url}/api/platform/spot/order/cancel/v2?orderId={order_id}"
        res = await self.client.fetch("DELETE", url)
