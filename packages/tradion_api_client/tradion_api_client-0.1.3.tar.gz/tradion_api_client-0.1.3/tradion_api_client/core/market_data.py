"""
Tradion Market Data Client for WebSocket real-time data
Handles WebSocket connection, subscriptions, and heartbeat
"""
import asyncio
import hashlib
import json
import ssl
from typing import Callable, Optional, Dict, Any
import websockets
from tradion_api_client.utils.logger import logger
from tradion_api_client.exceptions import WebSocketError
from tradion_api_client.config import Config

class MarketDataClient:
    """
    Async WebSocket client for real-time market data
    
    Features:
    - Subscribe/unsubscribe to instruments
    - Automatic heartbeat (every 50 seconds)
    - Auto-reconnection on disconnect
    - Tick and depth data support
    """
    
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self._ws = None
        self._listener_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._tick_handler: Optional[Callable] = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._subscriptions = set()
        
        logger.info(f"MarketDataClient initialized for user: {user_id}")
    
    def _hash(self, s: str) -> str:
        """SHA-256 hash helper"""
        return hashlib.sha256(s.encode()).hexdigest()
    
    def _susertoken(self) -> str:
        """Generate WebSocket authentication token"""
        return self._hash(self._hash(self.session_id))
    
    async def connect(self):
        """
        Connect to WebSocket server
        
        Raises:
            WebSocketError: If connection fails
        """
        async with self._lock:
            if self._connected:
                logger.warning("Already connected to WebSocket")
                return
            
            try:
                logger.info("Connecting to WebSocket...")
                
                # Create SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # Connect
                self._ws = await websockets.connect(Config.WS_URL, ssl=ssl_context)
                
                # Send connection payload
                await self._send_connect_payload()
                
                # Wait for connection acknowledgment
                ack = await asyncio.wait_for(self._ws.recv(), timeout=10)
                ack_data = json.loads(ack)
                
                if ack_data.get('t') == 'ck' and ack_data.get('s') == 'OK':
                    self._connected = True
                    logger.info("WebSocket connected successfully")
                    
                    # Start listener and heartbeat tasks
                    self._listener_task = asyncio.create_task(self._listener())
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                else:
                    raise WebSocketError(f"Connection failed: {ack_data}")
            
            except asyncio.TimeoutError:
                logger.error("WebSocket connection timeout")
                raise WebSocketError("Connection timeout")
            
            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                raise WebSocketError(f"Connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        async with self._lock:
            if not self._connected:
                return
            
            logger.info("Disconnecting from WebSocket...")
            
            # Cancel tasks
            if self._listener_task:
                self._listener_task.cancel()
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            
            # Close connection
            if self._ws:
                await self._ws.close()
            
            self._connected = False
            self._subscriptions.clear()
            logger.info("WebSocket disconnected")
    
    async def _send_connect_payload(self):
        """Send initial connection payload"""
        payload = {
            "t": "c",
            "uid": f"{self.user_id}_API",
            "susertoken": self._susertoken(),
            "actid": f"{self.user_id}_API",
            "source": "API"
        }
        
        logger.debug(f"Sending connection payload: {payload}")
        await self._ws.send(json.dumps(payload))
    
    async def _heartbeat_loop(self):
        """Send heartbeat every 50 seconds to keep connection alive"""
        try:
            while self._connected:
                await asyncio.sleep(Config.WS_HEARTBEAT_INTERVAL)
                
                if self._connected and self._ws:
                    try:
                        await self._ws.send(json.dumps({"t": "h", "k": ""}))
                        logger.debug("Heartbeat sent")
                    except Exception as e:
                        logger.error(f"Heartbeat failed: {e}")
                        self._connected = False
                        break
        
        except asyncio.CancelledError:
            logger.debug("Heartbeat task cancelled")
        
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
            self._connected = False

    
    async def subscribe(self, token: str):
        """
        Subscribe to instrument for tick data
        
        Args:
            token: Instrument token in format "EXCHANGE|TOKEN" (e.g., "NSE|1594")
                   For multiple: "NSE|1594#NSE|26000"
        
        Example:
            await market.subscribe("NSE|1594")  # Single instrument
            await market.subscribe("NSE|1594#NSE|26000")  # Multiple
        """
        if not self._connected:
            raise WebSocketError("WebSocket not connected")
        
        try:
            payload = {"t": "t", "k": token}
            await self._ws.send(json.dumps(payload))
            
            # Track subscriptions
            for t in token.split('#'):
                self._subscriptions.add(t)
            
            logger.info(f"Subscribed to: {token}")
        
        except Exception as e:
            logger.error(f"Subscription failed: {e}")
            raise WebSocketError(f"Subscription failed: {e}")
    
    async def unsubscribe(self, token: str):
        """
        Unsubscribe from instrument
        
        Args:
            token: Instrument token (same format as subscribe)
        """
        if not self._connected:
            raise WebSocketError("WebSocket not connected")
        
        try:
            payload = {"t": "u", "k": token}
            await self._ws.send(json.dumps(payload))
            
            # Remove from subscriptions
            for t in token.split('#'):
                self._subscriptions.discard(t)
            
            logger.info(f"Unsubscribed from: {token}")
        
        except Exception as e:
            logger.error(f"Unsubscribe failed: {e}")
            raise WebSocketError(f"Unsubscribe failed: {e}")
    
    async def subscribe_depth(self, token: str):
        """
        Subscribe to market depth data
        
        Args:
            token: Instrument token (same format as subscribe)
        """
        if not self._connected:
            raise WebSocketError("WebSocket not connected")
        
        try:
            payload = {"t": "d", "k": token}
            await self._ws.send(json.dumps(payload))
            logger.info(f"Subscribed to depth: {token}")
        
        except Exception as e:
            logger.error(f"Depth subscription failed: {e}")
            raise WebSocketError(f"Depth subscription failed: {e}")
    
    async def unsubscribe_depth(self, token: str):
        """Unsubscribe from market depth data"""
        if not self._connected:
            raise WebSocketError("WebSocket not connected")
        
        try:
            payload = {"t": "ud", "k": token}
            await self._ws.send(json.dumps(payload))
            logger.info(f"Unsubscribed from depth: {token}")
        
        except Exception as e:
            logger.error(f"Depth unsubscribe failed: {e}")
            raise WebSocketError(f"Depth unsubscribe failed: {e}")
    
    def register_tick_handler(self, handler: Callable):
        """
        Register callback for tick data
        
        Args:
            handler: Async function(symbol, tick) that processes market data
        
        Example:
            async def my_handler(symbol, tick):
                ltp = tick.get('lp')
                print(f"{symbol}: {ltp}")
            
            market.register_tick_handler(my_handler)
        """
        self._tick_handler = handler
        logger.info("Tick handler registered")
    
    async def _listener(self):
        """Listen for incoming WebSocket messages"""
        try:
            logger.info("WebSocket listener started")
            message_count = 0
            async for raw in self._ws:
                message_count += 1
                # Log first 50 messages AND all NSEFO messages
                should_log = message_count <= 50 or 'NSEFO' in raw or message_count % 50 == 0
                if should_log:
                    logger.info(f"Received WS message #{message_count}: {raw[:150]}")
                
                try:
                    msg = json.loads(raw)
                    await self._handle_message(msg)
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {raw[:100]}")
                
                except Exception as e:
                    logger.error(f"Error handling message: {e}", exc_info=True)
            
            # The async for loop ended (WebSocket closed cleanly)
            logger.warning(f"WebSocket stream ended cleanly after {message_count} messages")
            self._connected = False
            # Don't try to reconnect if it's a clean close
        
        except asyncio.CancelledError:
            logger.info("Listener task cancelled (normal shutdown)")
            raise
        
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e.code} - {e.reason}")
            self._connected = False
            # Only reconnect if it's an unexpected close
            if e.code != 1000:  # 1000 is normal close
                await self._reconnect()
        
        except Exception as e:
            logger.error(f"Listener error: {e}", exc_info=True)
            self._connected = False
    
    async def _reconnect(self):
        """Attempt to reconnect WebSocket"""
        logger.info("Attempting to reconnect...")
        
        await asyncio.sleep(Config.WS_RECONNECT_DELAY)
        
        try:
            await self.connect()
            
            # Re-subscribe to all previous subscriptions
            if self._subscriptions:
                logger.info(f"Re-subscribing to {len(self._subscriptions)} instruments")
                for token in self._subscriptions:
                    try:
                        await self.subscribe(token)
                    except Exception as e:
                        logger.error(f"Failed to re-subscribe {token}: {e}")
        
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
    
    async def _handle_message(self, msg: Dict):
        """
        Route incoming messages to tick handler
        
        Message types:
        - 'ck': Connection acknowledgment
        - 'tk': Tick acknowledgment
        - 'tf': Tick feed (price updates)
        - 'dk': Depth acknowledgment
        - 'df': Depth feed (order book)
        """
        msg_type = msg.get('t')
        
        # Log connection status
        if msg_type == 'ck':
            status = msg.get('s')
            if status == 'OK':
                logger.info("Connection acknowledged")
            else:
                logger.error(f"Connection failed: {msg}")
            return
        
        # Log ALL acknowledgments to see option subscriptions
        if msg_type in ['tk', 'dk']:
            exchange = msg.get('e', '')
            token = msg.get('tk', '')
            logger.info(f"[SUBSCRIPTION ACK] {exchange}|{token} - Type: {msg_type}")
        
        # Route to user's handler
        if self._tick_handler and msg_type in ['tf', 'tk', 'df', 'dk']:
            try:
                # Extract symbol/token
                exchange = msg.get('e', '')
                token = msg.get('tk', '')
                symbol = f"{exchange}|{token}" if exchange and token else "UNKNOWN"
                
                # Call user's handler
                await self._tick_handler(symbol, msg)
            
            except Exception as e:
                logger.error(f"Tick handler error: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._connected
