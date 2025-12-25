from __future__ import annotations

import asyncio
from decimal import Decimal
import hashlib
import math
import random
import re
import time
from typing import Any, Iterable, Literal

import pybotters

from .models.edgex import EdgexDataStore
from .lib.edgex_sign import LimitOrderMessage, LimitOrderSigner
from .lib.util import fmt_value

def gen_client_id():
    # 1. 生成 [0,1) 的浮点数
    r = random.random()
    # 2. 转成字符串
    s = str(r)  # e.g. "0.123456789"
    # 3. 去掉 "0."
    digits = s[2:]
    # 4. 去掉前导 0
    digits = re.sub(r"^0+", "", digits)
    return digits


def calc_nonce(client_order_id: str) -> int:
    digest = hashlib.sha256(client_order_id.encode()).hexdigest()
    return int(digest[:8], 16)

def bignumber_to_string(x: Decimal) -> str:
    # normalize 去掉尾随零，然后用 f 格式避免科学计数法
    s = format(x.normalize(), "f")
    # 去掉小数点后多余的 0
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s

class Edgex:
    """
    Edgex 公共 API (HTTP/WS) 封装。

    说明
    - 当前仅包含公共行情数据（不包含私有接口）。
    - 订单簿频道命名规则：``depth.{contractId}.{level}``。
      成功订阅后，服务器会先推送一次完整快照（depthType=SNAPSHOT），之后持续推送增量（depthType=CHANGED）。
      解析后的结果存入 ``EdgexDataStore.book``。

    参数
    - client: ``pybotters.Client`` 实例
    - api_url: REST 基地址；默认使用 Edgex 官方 testnet 站点
    - ws_url: WebSocket 基地址；如不提供，则默认使用官方文档地址。
    """

    def __init__(
        self,
        client: pybotters.Client,
        *,
        api_url: str | None = None,
    ) -> None:
        self.client = client
        self.store = EdgexDataStore()
        # 公共端点可能因环境/地区不同而变化，允许外部覆盖。
        self.api_url = api_url or "https://pro.edgex.exchange"
        self.ws_url = "wss://quote.edgex.exchange"
        self.userid = None
        self.eth_address = None
        self.l2key = None

        api = self.client._session.__dict__['_apis'].get("edgex")  # type: ignore
        if api:
            self.l2key = api[2].split("-")[1]

    async def __aenter__(self) -> "Edgex":
        # 初始化基础合约元数据，便于后续使用 tickSize 等字段。
        await self.update_detail()
        await self.sync_user()
        return self
    
    async def sync_user(self) -> dict[str, Any]:
        # https://pro.edgex.exchange/api/v1/private/user/getUserInfo
        # https://pro.edgex.exchange/api/v1/private/account/getAccountPage?size=100
        # url = self._resolve_api_path("/api/v1/private/user/getUserInfo")
        # url = self._resolve_api_path("/api/v1/private/account/getAccountPage")
   
        res = await self.client.get(f'{self.api_url}/api/v1/private/account/getAccountPage?size=100')
        
        data = await res.json()
      
        # 重新取 userId ethAddress accountId
        data = data.get("data", {})
        accounts = data.get("dataList", [])
        if accounts:
            account = accounts[0]
            self.userid = account.get("userId")
            self.eth_address = account.get("ethAddress")
            self.accountid = account.get("id")
        else:
            raise ValueError("No account data found in response")
    
    async def sub_personal(self) -> None:
        """订阅用户相关的私有频道（需要登录）。"""
        await self.client.ws_connect(
            f"{self.ws_url}/api/v1/private/ws?accountId={self.accountid}&timestamp=" + str(int(time.time() * 1000)),
            hdlr_json=self.store.onmessage,
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: BaseException | None,
    ) -> None:
        # Edgex 当前没有需要关闭的资源；保持接口与 Ourbit 等类一致。
        return None

    async def update_detail(self) -> dict[str, Any]:
        """Fetch and cache contract metadata via the public REST endpoint."""

        await self.store.initialize(
            self.client.get(f'{self.api_url}/api/v1/public/meta/getMetaData'),
        )

    async def update(
        self,
        update_type: Literal["balance", "position", "orders", "ticker", "all"] = "all",
        *,
        contract_id: str | None = None,
    ) -> None:
        """使用 REST 刷新本地缓存的账户资产、持仓、活动订单与 24h 行情。"""

        requires_account = {"balance", "position", "orders", "all"}
        if update_type in requires_account and not getattr(self, "accountid", None):
            raise ValueError("accountid not set; call sync_user() before update().")

        account_asset_url = None
        active_orders_url = None
        if update_type in requires_account:
            account_asset_url = (
                f"{self.api_url}/api/v1/private/account/getAccountAsset"
                f"?accountId={self.accountid}"
            )
            active_orders_url = (
                f"{self.api_url}/api/v1/private/order/getActiveOrderPage"
                f"?accountId={self.accountid}&size=200"
            )

        ticker_url = f"{self.api_url}/api/v1/public/quote/getTicker"
        if contract_id:
            ticker_url = f"{ticker_url}?contractId={contract_id}"

        url_map: dict[str, list[str]] = {
            "balance": [account_asset_url] if account_asset_url else [],
            "position": [account_asset_url] if account_asset_url else [],
            "orders": [active_orders_url] if active_orders_url else [],
            "ticker": [ticker_url],
            "all": [
                *(url for url in (account_asset_url, active_orders_url) if url),
                ticker_url,
            ],
        }

        try:
            urls = url_map[update_type]
        except KeyError:
            raise ValueError(f"update_type err: {update_type}")

        # 直接传协程进去，initialize 会自己 await
        await self.store.initialize(*(self.client.get(url) for url in urls))



    async def sub_orderbook(
        self,
        contract_ids: str | Iterable[str] | None = None,
        *,
        symbols: str | Iterable[str] | None = None,
        level: int = 15,
        ws_url: str | None = None,
    ) -> None:
        """订阅指定合约 ID 或交易对名的订单簿（遵循 Edgex 协议）。

        规范
        - 默认 WS 端点：wss://quote.edgex.exchange（可通过参数/实例覆盖）
        - 每个频道的订阅报文：
          {"type": "subscribe", "channel": "depth.{contractId}.{level}"}
        - 服务端在订阅成功后，会先推送一次快照，再持续推送增量。
        """

        ids: list[str] = []
        if contract_ids is not None:
            if isinstance(contract_ids, str):
                ids.extend([contract_ids])
            else:
                ids.extend(contract_ids)

        if symbols is not None:
            if isinstance(symbols, str):
                lookup_symbols = [symbols]
            else:
                lookup_symbols = list(symbols)

            for symbol in lookup_symbols:
                matches = self.store.detail.find({"contractName": symbol})
                if not matches:
                    raise ValueError(f"Unknown Edgex symbol: {symbol}")
                ids.append(str(matches[0]["contractId"]))

        if not ids:
            raise ValueError("contract_ids or symbols must be provided")

        channels = [f"depth.{cid}.{level}" for cid in ids]

        # 优先使用参数 ws_url，其次使用实例的 ws_url，最后使用默认地址。
        url =  f"{self.ws_url}/api/v1/public/ws?timestamp=" + str(int(time.time() * 1000))

        # 根据文档：每个频道一条订阅指令，允许一次发送多个订阅对象。
        payload = [{"type": "subscribe", "channel": ch} for ch in channels]

        wsapp = self.client.ws_connect(url, send_json=payload, hdlr_json=self.store.onmessage)
        # 等待 WS 完成握手再返回，确保订阅报文成功发送。
        await wsapp._event.wait()

    async def sub_ticker(
        self,
        contract_ids: str | Iterable[str] | None = None,
        *,
        symbols: str | Iterable[str] | None = None,
        all_contracts: bool = False,
        periodic: bool = False,
        ws_url: str | None = None,
    ) -> None:
        """订阅 24 小时行情推送。

        参数
        - contract_ids / symbols: 指定单个或多个合约；二者至少提供一个。
        - all_contracts: 订阅 ``ticker.all``（或 ``ticker.all.1s``）。
        - periodic: 与 ``all_contracts`` 配合，true 则订阅 ``ticker.all.1s``。
        """

        channels: list[str] = []

        if all_contracts:
            channel = "ticker.all.1s" if periodic else "ticker.all"
            channels.append(channel)
        else:
            ids: list[str] = []
            if contract_ids is not None:
                if isinstance(contract_ids, str):
                    ids.append(contract_ids)
                else:
                    ids.extend(contract_ids)

            if symbols is not None:
                if isinstance(symbols, str):
                    lookup_symbols = [symbols]
                else:
                    lookup_symbols = list(symbols)

                for symbol in lookup_symbols:
                    matches = self.store.detail.find({"contractName": symbol})
                    if not matches:
                        raise ValueError(f"Unknown Edgex symbol: {symbol}")
                    ids.append(str(matches[0]["contractId"]))

            if not ids:
                raise ValueError("Provide contract_ids/symbols or set all_contracts=True")

            channels.extend(f"ticker.{cid}" for cid in ids)

        url = ws_url or f"{self.ws_url}/api/v1/public/ws?timestamp=" + str(int(time.time() * 1000))
        payload = [{"type": "subscribe", "channel": ch} for ch in channels]
        print(payload)
        wsapp = self.client.ws_connect(url, send_json=payload, hdlr_json=self.store.onmessage)
        await wsapp._event.wait()

    def _fmt_price(self, symbol: str, price: float) -> str:
        o = self.store.detail.get({"contractName": symbol})
        if not o:
            raise ValueError(f"Unknown Edgex symbol: {symbol}")
        tick = float(o.get("tickSize"))
        return fmt_value(price, float(tick))
    
    def _fmt_size(self, symbol: str, size: float) -> str:
        o = self.store.detail.get({"contractName": symbol})
        if not o:
            raise ValueError(f"Unknown Edgex symbol: {symbol}")
        step = float(o.get("stepSize"))
        return fmt_value(size, float(step))
    

    async def place_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        price: float = None,
        quantity: float = None,
        order_type: Literal["market", "limit_ioc", "limit_gtc"] = "limit_ioc",
        usdt_amount: float = None,
    ):  
        """下单接口（私有 REST）。
        返回值order_id: str
        """
        
        # 前端请求模板
        args = {
            "price": "210.00",
            "size": "1.0",
            "type": "LIMIT",
            "timeInForce": "GOOD_TIL_CANCEL",
            "reduceOnly": False,
            "isPositionTpsl": False,
            "isSetOpenTp": False,
            "isSetOpenSl": False,
            "accountId": "663528067938910372",
            "contractId": "10000003",
            "side": "BUY",
            "triggerPrice": "",
            "triggerPriceType": "LAST_PRICE",
            "clientOrderId": "39299826149407513",
            "expireTime": "1760352231536",
            "l2Nonce": "1872301",
            "l2Value": "210",
            "l2Size": "1.0",
            "l2LimitFee": "1",
            "l2ExpireTime": "1761129831536",
            "l2Signature": "03c4d84c30586b12ab9fec939a875201e58dac9a0391f15eb6118ab2fb50464804ce38b19cc5e07c973fc66b449bec0274058ea2d012c1c7a580f805d2c7a1d3",
            "extraType": "",
            "extraDataJson": "",
            "symbol": "SOLUSD",
            "showEqualValInput": False,
            "maxSellQTY": 1, # 不需要特别计算, 服务器不校验
            "maxBuyQTY": 1 # 不需要特别计算, 服务器不校验
        }

        try:
            size = Decimal(self._fmt_size(symbol, quantity))
            price = Decimal(self._fmt_price(symbol, price))
        except (ValueError, TypeError):
            raise ValueError("failed to parse size or price")
        
        if 'gtc' in order_type:
            args['timeInForce'] = "GOOD_TIL_CANCEL"
        if 'ioc' in order_type:
            args['timeInForce'] = "IMMEDIATE_OR_CANCEL"
        if 'limit' in order_type:
            args['type'] = "LIMIT"
        if 'market' in order_type:
            args['type'] = "MARKET"
  
            if side == 'buy':
                price = price * 10
            else:
                tick_size = self.store.detail.get({'contractName': symbol}).get("tickSize")
                price = Decimal(tick_size)

        if not self.l2key or not self.userid:
            raise ValueError("L2 key or userId is not set. Ensure API keys are correctly configured.")


        collateral_coin = self.store.app.get({'appName': 'edgeX'})

        c = self.store.detail.get({'contractName': symbol})
        if not c:
            raise ValueError(f"Unknown Edgex symbol: {symbol}")
        hex_resolution = c.get("starkExResolution", "0x0")
        hex_resolution = hex_resolution.replace("0x", "")

        try:
            resolution_int = int(hex_resolution, 16)
            resolution = Decimal(resolution_int)
        except (ValueError, TypeError):
            raise ValueError("failed to parse hex resolution")
        
        client_order_id = gen_client_id()

        # Calculate values
        value_dm:Decimal = price * size
        
        amount_synthetic = int(size * resolution)
        amount_collateral = int(value_dm * Decimal("1000000"))  # Shift 6 decimal places
        
        
        # Calculate fee based on order type (maker/taker)
        try:
            fee_rate = Decimal(c.get("defaultTakerFeeRate", "0"))
        except (ValueError, TypeError):
            raise ValueError("failed to parse fee rate")

        # Calculate fee amount in decimal with ceiling to integer
        amount_fee_dm = Decimal(str(math.ceil(float(value_dm * fee_rate))))
        amount_fee_str = str(amount_fee_dm)

        # Convert to the required integer format for the protocol
        amount_fee = int(amount_fee_dm * Decimal("1000000"))  # Shift 6 decimal places

        nonce = calc_nonce(client_order_id)
        now = int(time.time() * 1000)
        l2_expire_time = int(now + 2592e6)  # 30 天后
        expireTime = int(l2_expire_time - 7776e5)  # 提前 9 天


        # Calculate signature using asset IDs from metadata
        expire_time_unix = int(l2_expire_time // (60 * 60 * 1000))

        asset_id_synthetic = c.get("starkExSyntheticAssetId")

        act_id = self.accountid

        message = LimitOrderMessage(
            asset_id_synthetic=asset_id_synthetic, # SOLUSD
            asset_id_collateral=collateral_coin.get("starkExCollateralStarkExAssetId"), # USDT
            asset_id_fee=collateral_coin.get("starkExCollateralStarkExAssetId"),
            is_buy= side=='buy',  # isBuyingSynthetic
            amount_synthetic=amount_synthetic,      # quantumsAmountSynthetic
            amount_collateral=amount_collateral,     # quantumsAmountCollateral
            amount_fee=amount_fee,              # quantumsAmountFee
            nonce=int(nonce),                # nonce
            position_id=int(act_id),  # positionId
            expiration_epoch_hours=int(expire_time_unix),   # 此处也比较重要 # TODO: 计算
        )

        # 取 L2 私钥


        signer = LimitOrderSigner(self.l2key)
        hash_hex, signature_hex = signer.sign(message)
        value_str = bignumber_to_string(value_dm)
        
        price_str = str(price) if 'limit' in order_type else "0"

        args.update({
            'price': price_str,
            'size': str(float(size)),
            'side': side.upper(),
            'accountId': str(act_id),
            'contractId': str(c.get("contractId")),
            'clientOrderId': client_order_id,
            'expireTime': str(expireTime),
            'l2ExpireTime': str(l2_expire_time),
            'l2Nonce': str(nonce),
            'l2Value': value_str,
            'l2Size': str(float(size)),
            'l2LimitFee': amount_fee_str,
            'l2Signature': signature_hex,
            'symbol': symbol
        })



        res = await self.client.post(
            f'{self.api_url}/api/v1/private/order/createOrder',
            data=args
        )

        data:dict = await res.json()
        if data.get("code") != "SUCCESS":  # pragma: no cover - defensive guard
            raise RuntimeError(f"Failed to place Edgex order: {data}")

        latency = int(data.get("responseTime",0)) - int(data.get("requestTime",0))
        print(latency)
        order_id = data.get("data", {}).get("orderId")
        return order_id
    
    async def cancel_orders(self, order_ids: list[str]) -> dict[str, Any]:
        """
        批量撤单接口（私有 REST）。
        
        .. code:: json
            {
                "665186247567737508": "SUCCESS"
            }
        """

        args = {
            "orderIdList": order_ids,
            "accountId": str(self.accountid),
        }
        res = await self.client.post(
            f'{self.api_url}/api/v1/private/order/cancelOrderById',
            data=args
        )
        data: dict = await res.json()
        print(data)
        if data.get("code") != "SUCCESS":  # pragma: no cover - defensive guard
            raise RuntimeError(f"Failed to cancel Edgex orders: {data}")
        return data.get("data", {}).get("cancelResultMap", {})


    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: BaseException | None,
    ) -> None:
        # Edgex 当前没有需要关闭的资源；保持接口与 Ourbit 等类一致。
        return None
