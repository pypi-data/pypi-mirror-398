# ---------------------------------------------------------------
# Import libs and modules 
# ---------------------------------------------------------------
import asyncio
import aiohttp

from .__exceptions__ import *

# ---------------------------------------------------------------
#  Main Class
# ---------------------------------------------------------------
class SymbolIndex:
    def __init__(self, symbol: str, errors_queue=None, *args, **kwargs):
        # Base attributes
        self.platform_name = "Platform"
        self.SYMBOL = symbol
        self.async_tasks = []
        self.rest_session = None
        self.errors_queue = errors_queue

        # Order-book attributes
        self.snapshot_update_status = 0
        self.snapshot_update = None
        self.updates = {}
        self.bests_ob = {}
        self.global_bids = {}
        self.global_asks = {}
        self.lastUpdateInOB = 0
        self.limit_orderbook = 5000

    # Errors queue =====================================================

    # Main of queue 
    def queue_error(self,e_type:str,source:str,msg:str):
        if self.errors_queue:
            asyncio.create_task(self.errors_queue.put({
                'type':e_type,
                'source':f"onesymbol.{self.SYMBOL}.{source}",
                'msg':msg
            }))

    # When ther is not any connection
    def connection_e(self,source:str):
        self.queue_error(
            e_type='CONNECTION_0', # 'CONNECTION_'/'CRITICAL'/'UNKNOWN',
            source=source,
            msg="❌ No Internet Connection, Please Try to connect and retry"
        )

    # The critical connnection errors
    def error_429(self,source:str):
        self.queue_error(e_type='CONNECTION_429',source=source,msg="⚠️ Too many requests (429). Please wait just 1 minute to retry, if you dont wait, you IP ADress will blocked")
    def error_418(self,source:str):
        self.queue_error(e_type='CONNECTION_418',source=source,msg="🚫 IP is banned temporarily (418). Please wait 1 hour to retry, if you dont wait, you IP ADress will blocked")
    def error_403(self,source:str):
        self.queue_error(e_type='CONNECTION_403',source=source,msg="❌ Forbidden (403). Your IP might be blocked. Please Try to use VPN or Proxy server")

    # Unknown error
    def unknown_e(self,source:str,e:str):
        self.queue_error(e_type='UNKNOWN',source=source,msg=e)

    # When websocket closed
    def ws_closed_e(self,source:str):
        self.queue_error(e_type='CONNECTION_WS',source=source,msg="❌ WebSocket connection closed, Please try reconnecting")


    # Order-book methods ===============================================

    # Set order-book updates
    async def process_ob_message(self,msg:dict):
        """Set order-book upates"""
        try:
            lastUpdateId = msg.get("lastUpdateId")
            firstUpdateId = msg.get("firstUpdateId")
            if self.snapshot_update_status == 0: 
                self.updates[lastUpdateId] = msg
                return False
            elif self.snapshot_update_status == -1:
                if not self.lastUpdateInOB+1 == firstUpdateId:
                    t = asyncio.create_task(self._update_ob_snapshot());t
                    self.async_tasks.append(t)
                    return False
                asks_ = msg.get("asks")
                bids_ = msg.get("bids")
                self._update_ob(asks_,bids_)
                self.lastUpdateInOB = lastUpdateId
            else:
                last_updates_key = list(self.updates.keys())[-1] if len(list(self.updates.keys())) > 0 else lastUpdateId
                self.snapshot_update_status = -1
                if last_updates_key == self.snapshot_update:
                    asks_ = msg.get("asks")
                    bids_ = msg.get("bids")
                    self._update_ob(asks_,bids_)
                    self.lastUpdateInOB = lastUpdateId
                else:
                    udpdates_keys = list(self.updates.keys())
                    if self.snapshot_update in udpdates_keys:
                        idx = udpdates_keys.index(self.snapshot_update)
                        vals = {k:self.updates[k] for k in udpdates_keys[idx+1:]}
                        for l,value in vals.items():
                            vals_asks = value.get("asks")
                            vals_bids = value.get("bids")
                            self._update_ob(vals_asks,vals_bids)
                            self.updates.clear()
                        asks_ = msg.get("asks")
                        bids_ = msg.get("bids")
                        self._update_ob(asks_,bids_)
                        self.lastUpdateInOB = lastUpdateId
                    else:
                        t = asyncio.create_task(self._update_ob_snapshot());t
                        self.async_tasks.append(t)
                        return False
            if len(self.global_asks) > 0 and len(self.global_bids) > 0:
                self.bests_ob = {
                    "min":{
                        "asks":min(self.global_asks.keys()),
                        "bids":min(self.global_bids.keys())
                    },
                    "max":{
                        "asks":max(self.global_asks.keys()),
                        "bids":max(self.global_bids.keys())
                }}

            return True
        except Exception as e:
            raise UnknownError(f"Process Orderbook Message | {self.platform_name} >> {e}")
        
    # Update order-book levels
    def _update_ob(self,asks_,bids_):
        for p,q in bids_:
            q = float(q)
            p = float(p)
            self.global_bids[p] = q
            if self.global_bids[p] == 0: 
                del self.global_bids[p]
        for p,q in asks_:
            q = float(q)
            p = float(p)
            self.global_asks[p] = q
            if self.global_asks[p] == 0: 
                del self.global_asks[p]
        # Limit order-book levels
        if len(self.global_asks) > self.limit_orderbook:
            sorted_asks = dict(sorted(self.global_asks.items()))
            self.global_asks = dict(list(sorted_asks.items())[:self.limit_orderbook])
        if len(self.global_bids) > self.limit_orderbook:
            sorted_bids = dict(sorted(self.global_bids.items(), reverse=True))
            self.global_bids = dict(list(sorted_bids.items())[:self.limit_orderbook])

    # upate order-book snapshot start operation
    async def _update_ob_snapshot_start(self):
        self.snapshot_update_status = 0

    # update order-book snapshot end operation
    async def _update_ob_snapshot_end(self,data:dict):
        self.snapshot_update = data.get("lastUpdateId")
        self.snapshot_update_status = 10
        self.global_asks = {float(p):float(q) for p,q in data.get("asks")}
        self.global_bids = {float(p):float(q) for p,q in data.get("bids")}
        self.bests_ob = {
            "min":{
                "asks":min(self.global_asks.keys()),
                "bids":min(self.global_bids.keys())
            },
            "max":{
                "asks":max(self.global_asks.keys()),
                "bids":max(self.global_bids.keys())
            }}

    # Update order-book snapshot
    async def _update_ob_snapshot(self):
        raise NotImplementedError("The method `_update_ob_snapshot` should be implemented in the subclass.")

    # Main methods ==================================================
        
    # Start async sessions
    async def start(self,session:aiohttp.ClientSession=None):
        if self.rest_session is None and session is None:
            self.rest_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(20))
        elif session is not None:
            self.rest_session = session
        return self.rest_session
    
    # Restart async sessions
    async def restart(self,session:aiohttp.ClientSession=None):
        """Restart async sessions"""
        try:
            await self.close()
            await self.start(session=session)
        except Exception as e:
            raise UnknownError(f"Restart Sessions | {self.platform_name} >> {e}")
        
    # Close async sessions and tasks
    async def close(self):
        """Close all async sessions and tasks"""
        try:   
            for task in self.async_tasks:
                task.cancel()
            await self.rest_session.close()
            self.rest_session = None
        except Exception as e:
            raise UnknownError(f"Close Sessions and Tasks | {self.platform_name} >> {e}")
        

# ---------------------------------------------------------------
#  All Symbols Class
# ---------------------------------------------------------------

class AllSymbolsIndex:
    def __init__(self, errors_queue=None, *args, **kwargs):
        # Base attributes
        self.platform_name = "Platform"
        self.rest_session = None
        self.errors_queue = errors_queue

    # Errors queue =====================================================

    # Main of queue 
    def queue_error(self,e_type:str,source:str,msg:str):
        if self.errors_queue:
            asyncio.create_task(self.errors_queue.put({
                'type':e_type,
                'source':f"publicsymbols.{source}",
                'msg':msg
            }))

    # When ther is not any connection
    def connection_e(self,source:str):
        self.queue_error(
            e_type='CONNECTION_0', # 'CONNECTION_'/'CRITICAL'/'UNKNOWN',
            source=source,
            msg="❌ No Internet Connection, Please Try to connect and retry"
        )

    # The critical connnection errors
    def error_429(self,source:str):
        self.queue_error(e_type='CONNECTION_429',source=source,msg="⚠️ Too many requests (429). Please wait just 1 minute to retry, if you dont wait, you IP ADress will blocked")
    def error_418(self,source:str):
        self.queue_error(e_type='CONNECTION_418',source=source,msg="🚫 IP is banned temporarily (418). Please wait 1 hour to retry, if you dont wait, you IP ADress will blocked")
    def error_403(self,source:str):
        self.queue_error(e_type='CONNECTION_403',source=source,msg="❌ Forbidden (403). Your IP might be blocked. Please Try to use VPN or Proxy server")

    # Unknown error
    def unknown_e(self,source:str,e:str):
        self.queue_error(e_type='UNKNOWN',source=source,msg=e)

    # When websocket closed
    def ws_closed_e(self,source:str):
        self.queue_error(e_type='CONNECTION_WS',source=source,msg="❌ WebSocket connection closed, Please try reconnecting")

    # Main methods ==================================================
        
    # Start async sessions
    async def start(self,session:aiohttp.ClientSession=None):
        if self.rest_session is None and session is None:
            self.rest_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(20))
        elif session is not None:
            self.rest_session = session
        return self.rest_session
    
    # Restart async sessions
    async def restart(self,session:aiohttp.ClientSession=None):
        """Restart async sessions"""
        try:
            await self.close()
            await self.start(session=session)
        except Exception as e:
            raise UnknownError(f"Restart Sessions | {self.platform_name} >> {e}")
        
    # Close async sessions
    async def close(self):
        """Close all async sessions"""
        try:   
            await self.rest_session.close()
            self.rest_session = None
        except Exception as e:
            raise UnknownError(f"Close Sessions | {self.platform_name} >> {e}")