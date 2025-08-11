import asyncio
import json
import hmac
import base64
import hashlib
from typing import Callable, List, Tuple

from utils.time_utils import is_weekend_utc3, ms_to_dt_utc

Bar = Tuple[int, float, float, float, float]

class FXOpenWS:
    """
    Универсальный клиент: логин, история, подписки на тики и бары.
    Вызывает колбэки: on_history(bars), on_tick(ts_ms, bid), on_server_bar(bar_tuple).
    """
    def __init__(self, feed_url: str, api_id: str, api_key: str, api_secret: str):
        self.feed_url = feed_url
        self.api_id = api_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws = None

        # callbacks
        self.on_history: Callable[[List[Bar]], None] = lambda bars: None
        self.on_tick:    Callable[[int, float], None] = lambda ts, price: None
        self.on_bar:     Callable[[Bar], None] = lambda bar: None

    def _sign(self, ts_ms: int) -> str:
        msg = f"{ts_ms}{self.api_id}{self.api_key}".encode("utf-8")
        dig = hmac.new(self.api_secret.encode("utf-8"), msg, hashlib.sha256).digest()
        return base64.b64encode(dig).decode("utf-8")

    async def _send(self, obj):
        await self.ws.send(json.dumps(obj))

    async def login(self):
        ts = int(ms_to_dt_utc(0).timestamp()*1000)  # заглушка, ниже исправим на текущее
        import time as _time
        ts = int(_time.time() * 1000)
        payload = {
            "Id": "login",
            "Request": "Login",
            "Params": {
                "AuthType": "HMAC",
                "WebApiId": self.api_id,
                "WebApiKey": self.api_key,
                "Timestamp": ts,
                "Signature": self._sign(ts),
                "DeviceId": "PyClient",
                "AppSessionId": "QuotesSession"
            }
        }
        await self._send(payload)
        resp = json.loads(await self.ws.recv())
        if resp.get("Response") == "Error":
            raise RuntimeError(f"Login error: {resp.get('Error')}")
        # ok

    async def get_history(self, symbol: str, periodicity: str, count: int) -> List[Bar]:
        import time as _time
        req = {
            "Id": "history",
            "Request": "QuoteHistoryBars",
            "Params": {
                "Symbol": symbol,
                "Periodicity": periodicity,  # "M1"
                "PriceType": "bid",
                "Timestamp": int(_time.time()*1000),
                "Count": -abs(count)
            }
        }
        await self._send(req)
        resp = json.loads(await self.ws.recv())
        if resp.get("Response") == "Error":
            raise RuntimeError(f"QuoteHistoryBars error: {resp.get('Error')}")
        result = resp.get("Result", {}) or {}
        raw = None
        for key in ("Bars","Items","History","Data","Quotes"):
            arr = result.get(key)
            if isinstance(arr, list):
                raw = arr; break
        if raw is None and isinstance(result, list):
            raw = result
        bars: List[Bar] = []
        if raw:
            for b in raw:
                t = b.get("Time") or b.get("Timestamp") or b.get("T")
                if t is None: continue
                ts = int(t)
                if is_weekend_utc3(ts):  # фильтруем сразу
                    continue
                o = float(b.get("Open", b.get("O")))
                h = float(b.get("High", b.get("H")))
                l = float(b.get("Low",  b.get("L")))
                c = float(b.get("Close", b.get("C")))
                bars.append((ts, o, h, l, c))
        bars.sort(key=lambda x: x[0])
        return bars

    async def subscribe_ticks(self, symbol: str):
        payload = {
            "Id": "sub_ticks",
            "Request": "FeedSubscribe",
            "Params": { "Subscribe": [{ "Symbol": symbol, "BookDepth": 1 }] }
        }
        await self._send(payload)
        _ = json.loads(await self.ws.recv())  # ok

    async def subscribe_bars(self, symbol: str, periodicity: str):
        payload = {
            "Id": "sub_bars",
            "Request": "BarFeedSubscribe",
            "Params": {
                "Subscribe": [{
                    "Symbol": symbol,
                    "BarParams": [{ "Periodicity": periodicity, "PriceType": "Bid" }]
                }]
            }
        }
        await self._send(payload)
        _ = json.loads(await self.ws.recv())  # ok

    async def run(self, symbol: str, periodicity: str, count: int):
        import websockets
        async with websockets.connect(self.feed_url, ping_interval=20, ping_timeout=20) as ws:
            self.ws = ws
            await self.login()
            bars = await self.get_history(symbol, periodicity, count)
            self.on_history(bars)
            await self.subscribe_ticks(symbol)
            await self.subscribe_bars(symbol, periodicity)

            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except:
                    continue

                # Tick
                if msg.get("Response") == "FeedTick":
                    r = msg.get("Result", {}) or {}
                    ts = r.get("Timestamp")
                    bb = r.get("BestBid") or {}
                    price = bb.get("Price")
                    if ts is None or price is None:
                        continue
                    ts = int(ts); price = float(price)
                    if is_weekend_utc3(ts):  # лишняя защита
                        continue
                    self.on_tick(ts, price)
                    continue

                # Server bar update
                if msg.get("Response") == "FeedBarUpdate":
                    r = msg.get("Result", {}) or {}
                    updates = r.get("Updates") or []
                    if not updates: continue
                    u = updates[-1]
                    try:
                        t = int(u.get("Time"))
                        if is_weekend_utc3(t): continue
                        o = float(u.get("Open")); h = float(u.get("High"))
                        l = float(u.get("Low"));  c = float(u.get("Close"))
                        self.on_bar((t,o,h,l,c))
                    except:
                        pass
