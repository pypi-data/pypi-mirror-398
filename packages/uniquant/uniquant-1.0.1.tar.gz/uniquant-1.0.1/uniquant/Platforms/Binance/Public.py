# ---------------------------------------------------------------
# Import libs and modules 
# ---------------------------------------------------------------
import asyncio
import json
import websockets
import aiohttp
import logging

from socket import gaierror
from uniquant.main import *

# ---------------------------------------------------------------
#  One Symbole Class
# ---------------------------------------------------------------
class OneSymbole(SymbolIndex):
    def __init__(self, symbol: str, errors_queue:QueueStream=None, *args, **kwargs):
        super().__init__(symbol, errors_queue, *args, **kwargs)
        self.platform_name = "Binance"

    # Order-book methods ===============================================

    # Update the order book snapshot from Binance REST API
    async def _update_ob_snapshot(self):
        url = "https://api.binance.com/api/v3/depth"
        params = {"symbol": self.SYMBOL.upper(),"limit": int(self.limit_orderbook)}
        await self._update_ob_snapshot_start()
        try:
            async with self.rest_session.get(url, params=params) as r:

                if r.status == 429:
                    self.error_429(source="_update_ob_snapshot")
                    raise Error429("Get Orderbook Snapshot | Binance REST API")
                if r.status == 418:
                    self.error_418(source="_update_ob_snapshot")
                    raise Error418("Get Orderbook Snapshot | Binance REST API")
                if r.status == 403:
                    self.error_403(source="_update_ob_snapshot")
                    raise Error403("Get Orderbook Snapshot | Binance REST API")
                if r.status != 200:
                    self.queue_error(e_type=f'CONNECTION_{r.status}',source="_update_ob_snapshot",msg=f"Request code error -> {r.status}")
                    raise RequestCodeError(r.status)

                logging.debug("Get Orderbook Snapshot | Binance REST API >> Success")
                
                depth_dict = await r.json()
                await self._update_ob_snapshot_end(depth_dict)
        
        except (aiohttp.ClientConnectionError,gaierror):
            logging.debug("Get Orderbook Snapshot | Binance REST API >> Connection Error")
            self.connection_e(source="_update_ob_snapshot")
            raise ConnectionError("Get Orderbook Snapshot | Binance REST API")
        except Exception as e:
            logging.debug(f"Get Orderbook Snapshot | Binance REST API >> Unknown Error: {e}")
            self.unknown_e(source="_update_ob_snapshot",e=e)
            raise UnknownError(f"Get Orderbook Snapshot | Binance REST API >> {e}")

    # WebSocket connection to receive real-time order book updates
    async def orderbook_stream(self,limit:int=5000):
        self.limit_orderbook = limit
        url = f"wss://stream.binance.com:9443/ws/{self.SYMBOL.lower()}@depth@100ms"
        t = asyncio.create_task(self._update_ob_snapshot())
        #await asyncio.sleep(0)
        self.async_tasks.append(t)
        try:
            async with websockets.connect(url) as ws:
                logging.debug(f"WebSocket Orderbook | Binance WS API >> Connected to {url}")

                while True:
                    resp = await ws.recv()
                    msg = json.loads(resp)
                    data = {
                        "lastUpdateId": int(msg.get("u")),
                        "firstUpdateId": int(msg.get("U")),
                        "bids": msg.get("b"),
                        "asks": msg.get("a")
                    }
                    f = await self.process_ob_message(data)

                    if f:
                        yield {"asks": self.global_asks, "bids": self.global_bids}

        except websockets.exceptions.ConnectionClosedError:
            self.ws_closed_e(source="orderbook_stream")
            raise WebSocketClosedError("WebSocket Orderbook | Binance WS API")
        except (OSError, websockets.exceptions.InvalidStatus, gaierror) as e:
            self.connection_e(source="orderbook_stream")
            raise ConnectionError(f"WebSocket Orderbook | Binance WS API >> {e}")
        except Exception as e:
            self.unknown_e(source="orderbook_stream",e=e)
            raise UnknownError(f"WebSocket Orderbook | Binance WS API >> {e}")
        
    # Auther ws methods ===============================================

    # WebSocket connection to receive real-time trades
    async def trades_stream(self):
        """Fetch real-time trade data from Binance WebSocket API."""
        url = f"wss://stream.binance.com:9443/ws/{self.SYMBOL.lower()}@trade"
        try:
            logging.debug(f"WebSocket Trades | Binance WS API >> Connected to {url}")
            async with websockets.connect(url) as ws:
                while True:
                    resp = await ws.recv()
                    msg = json.loads(resp)
                    yield{
                        "symbol":self.SYMBOL,
                        "price": float(msg.get("p")),
                        "quantity": float(msg.get("q")),
                        "trade_id": int(msg.get("t")),
                        "timestamp": int(msg.get("T")),
                        "side": "buy" if msg.get("m") == False else "sell"
                    }

        except websockets.exceptions.ConnectionClosedError:
            self.ws_closed_e(source="trades_stream")
            raise WebSocketClosedError("WebSocket Trades | Binance WS API")
        except (OSError, websockets.exceptions.InvalidStatus, gaierror) as e:
            self.connection_e(source="trades_stream")
            raise ConnectionError(f"WebSocket Trades | Binance WS API >> {e}")
        except Exception as e:
            self.unknown_e(source="trades_stream",e=e)
            raise UnknownError(f"WebSocket Trades | Binance WS API >> {e}")
        
    async def klines_stream(self, interval:str):
        """Fetch real-time kline/candlestick data from Binance WebSocket API."""

        url = f"wss://stream.binance.com:9443/ws/{self.SYMBOL.lower()}@kline_{fix_interval(interval)[1]}"
        try:
            async with websockets.connect(url) as ws:
                logging.debug(f"WebSocket Klines | Binance WS API >> Connected to {url}")
                while True:
                    resp = await ws.recv()
                    msg = json.loads(resp)
                    kline = msg['k']
                    open_time = int(kline['t'])
                    open_price = float(kline['o'])
                    high_price = float(kline['h'])
                    low_price = float(kline['l'])
                    close_price = float(kline['c'])
                    volume = float(kline['v'])
                    close_time = int(kline['T'])

                    yield {
                        "open_time": open_time,
                        "open": open_price,
                        "high": high_price,
                        "low": low_price,
                        "close": close_price,
                        "volume": volume,
                        "close_time": close_time,
                    }

        except websockets.exceptions.ConnectionClosedError:
            self.ws_closed_e(source="klines_stream")
            raise WebSocketClosedError("WebSocket Klines | Binance WS API")
        except (OSError, websockets.exceptions.InvalidStatus, gaierror) as e:
            self.connection_e(source="klines_stream")
            raise ConnectionError(f"WebSocket Klines | Binance WS API >> {e}")
        except Exception as e:
            self.unknown_e(source="klines_stream",e=e)
            raise UnknownError(f"WebSocket Klines | Binance WS API >> {e}")

    # REST API methods ===============================================

    # Get symbol information from Binance REST API
    async def get_symbol_info(self):
        """Fetch symbol information from Binance REST API."""
        url = "https://api.binance.com/api/v3/exchangeInfo"
        params = {"symbol": self.SYMBOL.upper()}
        try:
            async with self.rest_session.get(url, params=params) as r:

                if r.status == 429:
                    self.error_429(source="get_symbol_info")
                    raise Error429("Get Symbol Info | Binance REST API")
                if r.status == 418:
                    self.error_418(source="get_symbol_info")
                    raise Error418("Get Symbol Info | Binance REST API")
                if r.status == 403:
                    self.error_403(source="get_symbol_info")
                    raise Error403("Get Symbol Info | Binance REST API")
                if r.status != 200:
                    self.queue_error(e_type=f'CONNECTION_{r.status}',source="get_symbol_info",msg=f"Request code error -> {r.status}")
                    raise RequestCodeError(r.status)

                logging.debug("Get Symbol Info | Binance REST API >> Success")
                
                data = await r.json()
                symbols = data.get("symbols", [])
                
                if not symbols:
                    raise ValueError(f"Symbol {self.SYMBOL} not found")
                
                symbol_data = symbols[0]
                
                # Extract precision and filter information
                symbol_info = {
                    "symbol": symbol_data.get("symbol"),
                    "status": symbol_data.get("status"),
                    "baseAsset": symbol_data.get("baseAsset"),
                    "baseAssetPrecision": symbol_data.get("baseAssetPrecision"),
                    "quoteAsset": symbol_data.get("quoteAsset"),
                    "quotePrecision": symbol_data.get("quotePrecision"),
                    "orderTypes": symbol_data.get("orderTypes"),
                    "icebergAllowed": symbol_data.get("icebergAllowed"),
                    "filters": symbol_data.get("filters", [])
                }
                
                return symbol_info
        
        except (aiohttp.ClientConnectionError, gaierror):
            self.connection_e(source="get_symbol_info")
            raise ConnectionError("Get Symbol Info | Binance REST API")
        except Exception as e:
            self.unknown_e(source="get_symbol_info",e=e)
            raise UnknownError(f"Get Symbol Info | Binance REST API >> {e}")

    # Klines/candlesticks data via REST API
    async def klines_rest(self, interval, limit = 1000, start_time = None, end_time = None):
        """Fetch historical kline data from Binance REST API."""
        url = "https://api.binance.com/api/v3/klines"
        logging.debug("Fetching klines from Binance REST API...")
        params = {
            "symbol": self.SYMBOL.upper(),
            "interval": fix_interval(interval)[1],
            "limit": int(limit)
        }
        if start_time: params["startTime"] = start_time
        if end_time: params["endTime"] = end_time
        
        try:
            async with self.rest_session.get(url, params=params) as r:

                if r.status == 429:
                    self.error_429(source="klines_rest")
                    raise Error429("Historical Kilnes | Binance REST API")
                if r.status == 418:
                    self.error_418(source="klines_rest")
                    raise Error418("Historical Kilnes | Binance REST API")
                if r.status == 403:
                    self.error_403(source="klines_rest")
                    raise Error403("Historical Kilnes | Binance REST API")
                if r.status != 200:
                    self.queue_error(e_type=f'CONNECTION_{r.status}',source="klines_rest",msg=f"Request code error -> {r.status}")
                    raise RequestCodeError(r.status)

                logging.debug("Historical Kilnes | Binance REST API >> Success")
                
                data = await r.json()

                klines = []
                for entry in data:
                    kline = {
                        "open_time": int(entry[0]),
                        "open": float(entry[1]),
                        "high": float(entry[2]),
                        "low": float(entry[3]),
                        "close": float(entry[4]),
                        "volume": float(entry[5]),
                        "close_time": int(entry[6]),
                    }
                    klines.append(kline)

                return klines
        
        except (aiohttp.ClientConnectionError,gaierror):
            self.connection_e(source="klines_rest")
            raise ConnectionError("Historical Kilnes | Binance REST API")
        except Exception as e:
            self.unknown_e(source="klines_rest",e=e)
            raise UnknownError(f"Historical Kilnes | Binance REST API >> {e}")
        

# ---------------------------------------------------------------
#  All Symbols Class
# ---------------------------------------------------------------
class PublicSymbols(AllSymbolsIndex):
    def __init__(self, errors_queue=None, *args, **kwargs):
        super().__init__(errors_queue,*args, **kwargs)
        self.platform_name = "Binance"

    # Get all spot symbols from Binance REST API
    async def get_all_spot_symbols(self,_type_:str="short"):
        """Fetch all spot trading symbols from Binance REST API."""
        url = "https://api.binance.com/api/v3/exchangeInfo"
        try:
            async with self.rest_session.get(url) as r:

                if r.status == 429:  raise Error429("Get All Spot Symbols | Binance REST API")
                if r.status == 418:  raise Error418("Get All Spot Symbols | Binance REST API")
                if r.status == 403:  raise Error403("Get All Spot Symbols | Binance REST API")
                if r.status != 200:  raise RequestCodeError(r.status)

                if r.status == 429:
                    self.error_429(source="get_all_spot_symbols")
                    raise Error429("Get All Spot Symbols | Binance REST API")
                if r.status == 418:
                    self.error_418(source="get_all_spot_symbols")
                    raise Error418("Get All Spot Symbols | Binance REST API")
                if r.status == 403:
                    self.error_403(source="get_all_spot_symbols")
                    raise Error403("Get All Spot Symbols | Binance REST API")
                if r.status != 200:
                    self.queue_error(e_type=f'CONNECTION_{r.status}',source="get_all_spot_symbols",msg=f"Request code error -> {r.status}")
                    raise RequestCodeError(r.status)

                logging.debug("Get All Spot Symbols | Binance REST API >> Success")
                
                data = await r.json()
                symbols = set()
                
                for symbol in data.get("symbols", []):
                    if symbol.get("status") == "TRADING":
                        symbols.add(symbol.get("symbol"))
                
                if _type_ == "short":
                    return symbols
                elif _type_ == "full":  
                    return data.get("symbols", [])
        
        except (aiohttp.ClientConnectionError, gaierror):
            self.connection_e(source="get_all_spot_symbols")
            raise ConnectionError("Get All Spot Symbols | Binance REST API")
        except Exception as e:
            self.unknown_e(source="get_all_spot_symbols",e=e)
            raise UnknownError(f"Get All Spot Symbols | Binance REST API >> {e}")