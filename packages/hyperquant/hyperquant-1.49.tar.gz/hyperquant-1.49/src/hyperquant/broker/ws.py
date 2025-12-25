import asyncio
import time
from typing import Any

import pybotters
from aiohttp import WSMsgType
from pybotters.ws import ClientWebSocketResponse, logger


class Heartbeat:
    @staticmethod
    async def ourbit(ws: pybotters.ws.ClientWebSocketResponse):
        while not ws.closed:
            await ws.send_str('{"method":"ping"}')
            await asyncio.sleep(10.0)
    
    async def ourbit_spot(ws: pybotters.ws.ClientWebSocketResponse):
        while not ws.closed:
            await ws.send_str('{"method":"ping"}')
            await asyncio.sleep(10.0)

    @staticmethod
    async def edgex(ws: pybotters.ws.ClientWebSocketResponse):
        while not ws.closed:
            now = str(int(time.time() * 1000))
            await ws.send_json({"type": "ping", "time": now})
            await asyncio.sleep(20.0)

    @staticmethod
    async def lbank(ws: ClientWebSocketResponse):
        while not ws.closed:
            await ws.send_str('ping')
            await asyncio.sleep(6)
    
    @staticmethod
    async def coinw(ws: ClientWebSocketResponse):
        while not ws.closed:
            await ws.send_json({"event": "ping"})
            await asyncio.sleep(3.0)

    @staticmethod
    async def deepcoin(ws: ClientWebSocketResponse):
        while not ws.closed:
            await ws.send_str("ping")
            await asyncio.sleep(30)

    @staticmethod   
    async def lighter(ws: ClientWebSocketResponse):
        while not ws.closed:
            await ws.send_json({"type":"ping"})
            await asyncio.sleep(3)



pybotters.ws.HeartbeatHosts.items['futures.ourbit.com'] = Heartbeat.ourbit
pybotters.ws.HeartbeatHosts.items['www.ourbit.com'] = Heartbeat.ourbit_spot
pybotters.ws.HeartbeatHosts.items['quote.edgex.exchange'] = Heartbeat.edgex
pybotters.ws.HeartbeatHosts.items['uuws.rerrkvifj.com'] = Heartbeat.lbank
pybotters.ws.HeartbeatHosts.items['ws.futurescw.com'] = Heartbeat.coinw
pybotters.ws.HeartbeatHosts.items['stream.deepcoin.com'] = Heartbeat.deepcoin
pybotters.ws.HeartbeatHosts.items['mainnet.zklighter.elliot.ai'] = Heartbeat.lighter
# pybotters.ws.HeartbeatHosts.items['ws-subscriptions-clob.polymarket.com'] = Heartbeat.polymarket

class WssAuth:
    @staticmethod
    async def ourbit(ws: ClientWebSocketResponse):
        key: str = ws._response._session.__dict__["_apis"][
            pybotters.ws.AuthHosts.items[ws._response.url.host].name
        ][0]
        await ws.send_json(
            {
                "method": "login",
                "param": {
                    "token": key
                }
            }
        )
        async for msg in ws:
            # {"channel":"rs.login","data":"success","ts":1756470267848}
            data = msg.json()
            if data.get("channel") == "rs.login":
                if data.get("data") == "success":
                    break
                else:
                    logger.warning(f"WebSocket login failed: {data}")
    
    @staticmethod
    async def coinw(ws: ClientWebSocketResponse):
        creds = ws._response._session.__dict__["_apis"].get(
            pybotters.ws.AuthHosts.items[ws._response.url.host].name
        )
        if not creds:
            raise RuntimeError("CoinW credentials are required for websocket login.")
        if isinstance(creds, dict):
            raise RuntimeError("CoinW credentials must be a sequence, not a dict.")
        if len(creds) < 1:
            raise RuntimeError("CoinW credentials are incomplete.")

        api_key = creds[0]
        secret = creds[1] if len(creds) > 1 else ""

        await ws.send_json(
            {
                "event": "login",
                "params": {
                    "api_key": api_key,
                    "passphrase": secret.decode(),
                },
            }
        )

        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            try:
                data:dict = msg.json()
            except Exception:  # pragma: no cover - defensive
                continue

            channel = data.get("channel")
            event_type = data.get("type")
            if channel == "login" or event_type == "login":
                result = data.get("data", {}).get("result")
                if result is not True:
                    raise RuntimeError(f"CoinW WebSocket login failed: {data}")
                break
            if data.get("event") == "pong":
                # ignore heartbeat responses while waiting
                continue

pybotters.ws.AuthHosts.items['futures.ourbit.com'] = pybotters.auth.Item("ourbit", WssAuth.ourbit)
pybotters.ws.AuthHosts.items['ws.futurescw.com'] = pybotters.auth.Item("coinw", WssAuth.coinw)
