"""
Tradion Interactive API Client for REST operations
Handles authentication, orders, portfolio, and funds management
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from tradion_api_client.utils.http_client import HttpClient
from tradion_api_client.utils.logger import logger
from tradion_api_client.exceptions import AuthenticationError, OrderError, TradionAPIError
from tradion_api_client.config import Config


class InteractiveClient:
    """
    Client for Tradion REST API operations
    
    Handles:
    - Authentication (login with password + OTP)
    - Order management (place, modify, cancel)
    - Portfolio (positions, holdings)
    - Funds and profile information
    """
    
    def __init__(self, version: str = Config.VERSION):
        self.version = version
        self.user_id: Optional[str] = None
        self.password: Optional[str] = None
        self.device_id: Optional[str] = None
        self.otp: Optional[str] = None
        self.access_token: Optional[str] = None
        self.http = HttpClient()
        
        logger.info("InteractiveClient initialized")
    
    # -----------------------
    # AUTHENTICATION
    # -----------------------
    
    async def login(self, user_id: str, password: str, otp: str, device_id: str) -> str:
        """
        Login with password and OTP
        
        Args:
            user_id: User ID (e.g., "AAA92")
            password: Trading password
            otp: OTP code
            device_id: Device identifier
            
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If login fails
        """
        self.user_id = user_id
        self.password = password
        self.otp = otp
        self.device_id = device_id
        
        logger.info(f"Attempting login for user: {user_id}...")
        
        try:
            # Step 1: Password validation
            pwd_payload = {
                "userId": self.user_id,
                "password": self.password,
                "deviceId": self.device_id,
                "versionNo": self.version,
                "appName": Config.APP_NAME,
                "osName": Config.OS_NAME,
                "source": Config.SOURCE
            }
            
            pwd_res = await self.http.request(
                "POST",
                f"{Config.AUTH_BASE}/pwd/validate",
                json=pwd_payload
            )
            
            temp_token = pwd_res["result"]["token"]
            logger.debug("Password validation successful")
            
            # Step 2: OTP validation
            otp_payload = {
                "userId": self.user_id,
                "receivedOtp": self.otp,
                "deviceId": self.device_id,
                "appName": Config.APP_NAME,
                "osName": Config.OS_NAME,
                "source": Config.SOURCE
            }
            
            headers = {"Authorization": f"Bearer {temp_token}"}
            otp_res = await self.http.request(
                "POST",
                f"{Config.AUTH_BASE}/otp/validate",
                json=otp_payload,
                headers=headers
            )
            
            self.access_token = otp_res["result"]["accessToken"]
            logger.info("Login successful")
            
            return self.access_token
        
        except TradionAPIError as e:
            logger.error(f"Login failed: {e}")
            raise AuthenticationError(f"Login failed: {e.message}")
        
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise AuthenticationError(f"Login failed: {e}")
    
    def _auth_header(self) -> Dict[str, str]:
        """Get authorization header for authenticated requests"""
        if not self.access_token:
            raise AuthenticationError("Not logged in. Call login() first.")
        return {"Authorization": f"Bearer {self.access_token}"}

    
    # -----------------------
    # ORDER PAYLOAD
    # -----------------------
    
    @dataclass
    class OrderPayload:
        """Order payload for place_order API"""
        exchange: str
        instrumentId: str
        transactionType: str
        quantity: int
        product: str
        orderComplexity: str
        orderType: str
        price: str
        validity: str
        slTriggerPrice: str = ""
        disclosedQuantity: str = ""
        marketProtectionPercent: str = ""
        targetLegPrice: str = ""
        slLegPrice: str = ""
        trailingSlAmount: str = ""
        apiOrderSource: str = ""
        algoId: str = ""
        orderTag: str = ""
    
    # -----------------------
    # ORDER MANAGEMENT
    # -----------------------
    
    async def place_order(self, orders: List[OrderPayload]) -> List[Dict[str, Any]]:
        """
        Place one or more orders
        
        Args:
            orders: List of OrderPayload objects
        
        Returns:
            List of order responses with brokerOrderId
        
        Raises:
            OrderError: If order placement fails
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/placeorder"
            payload = [o.__dict__ for o in orders]
            
            logger.info(f"Placing {len(orders)} order(s)")
            logger.info(f"Order payload contains {len(payload)} items: {[f'{p.get('transactionType')} {p.get('quantity')} x {p.get('instrumentId')}' for p in payload]}")
            logger.debug(f"Full order payload: {payload}")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            logger.info(f"Raw API response type: {type(response)}, keys: {response.keys() if isinstance(response, dict) else 'N/A'}")
            result = response.get('result', [])
            logger.info(f"Orders placed successfully")
            
            # Handle different result formats
            # If result is a dict (single order), wrap it in a list
            if isinstance(result, dict):
                order_id = result.get('brokerOrderId', 'UNKNOWN')
                request_time = result.get('requestTime', 'N/A')
                logger.info(f"Order placed - ID: {order_id}, Time: {request_time}")
                return [result]
            
            # If result is a list of dicts, return as is
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                for order in result:
                    order_id = order.get('brokerOrderId', 'UNKNOWN')
                    request_time = order.get('requestTime', 'N/A')
                    logger.info(f"Order placed - ID: {order_id}, Time: {request_time}")
                return result
            
            # Default: return result as is
            return [result] if result else []
        
        except TradionAPIError as e:
            logger.error(f"Order placement failed: {e}")
            raise OrderError(e.error_code, e.message)
        
        except Exception as e:
            logger.error(f"Unexpected error placing order: {e}")
            raise OrderError("UNKNOWN", str(e))
    
    async def modify_order(self, broker_order_id: str, **kwargs) -> Dict[str, Any]:
        """
        Modify an existing order
        
        Args:
            broker_order_id: Order ID to modify
            **kwargs: Fields to modify (quantity, price, orderType, etc.)
        
        Returns:
            Modified order response
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/modify"
            payload = {"brokerOrderId": broker_order_id, **kwargs}
            
            logger.info(f"Modifying order: {broker_order_id}")
            logger.debug(f"Modify payload: {payload}")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            logger.info(f"Order modified successfully: {broker_order_id}")
            return response.get('result', [{}])[0]
        
        except TradionAPIError as e:
            logger.error(f"Order modification failed: {e}")
            raise OrderError(e.error_code, e.message)
    
    async def cancel_order(self, broker_order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order
        
        Args:
            broker_order_id: Order ID to cancel
        
        Returns:
            Cancellation response
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/cancel"
            payload = {"brokerOrderId": broker_order_id}
            
            logger.info(f"Cancelling order: {broker_order_id}")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            logger.info(f"Order cancelled successfully: {broker_order_id}")
            return response.get('result', [{}])[0]
        
        except TradionAPIError as e:
            logger.error(f"Order cancellation failed: {e}")
            raise OrderError(e.error_code, e.message)
    
    async def order_book(self) -> List[Dict[str, Any]]:
        """
        Get all orders for the day
        
        Returns:
            List of orders with status, quantity, price, etc.
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/book"
            
            logger.debug("Fetching order book")
            
            response = await self.http.request(
                "GET",
                url,
                json={},
                headers=self._auth_header()
            )
            
            orders = response.get('result', [])
            logger.info(f"Fetched {len(orders)} orders from order book")
            
            return orders
        
        except Exception as e:
            logger.error(f"Failed to fetch order book: {e}")
            raise
    
    async def order_history(self, broker_order_id: str) -> List[Dict[str, Any]]:
        """
        Get history of a specific order
        
        Args:
            broker_order_id: Order ID
        
        Returns:
            Order history with all state changes
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/history"
            payload = {"brokerOrderId": broker_order_id}
            
            logger.debug(f"Fetching order history: {broker_order_id}")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            return response.get('result', [])
        
        except Exception as e:
            logger.error(f"Failed to fetch order history: {e}")
            raise
    
    async def tradebook(self) -> List[Dict[str, Any]]:
        """
        Get all executed trades for the day
        
        Returns:
            List of executed trades
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/trades"
            
            logger.debug("Fetching trade book")
            
            response = await self.http.request(
                "GET",
                url,
                json={},
                headers=self._auth_header()
            )
            
            trades = response.get('result', [])
            logger.info(f"Fetched {len(trades)} trades from trade book")
            
            return trades
        
        except Exception as e:
            logger.error(f"Failed to fetch trade book: {e}")
            raise
    
    async def check_margin(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check margin required for an order before placing
        
        Args:
            order_payload: Order details
        
        Returns:
            Margin details (totalCashAvailable, currentOrderMargin, etc.)
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/checkMargin"
            
            logger.debug("Checking margin requirement")
            
            response = await self.http.request(
                "POST",
                url,
                json=order_payload,
                headers=self._auth_header()
            )
            
            return response.get('result', [{}])[0]
        
        except Exception as e:
            logger.error(f"Failed to check margin: {e}")
            raise
        
    async def exit_bracket_order(self, broker_order_id: str, order_complexity: str) -> Dict[str, Any]:
        """
        Exit a bracket order
        
        Args:
            broker_order_id: Order ID to exit (also called orderNo)
            order_complexity: Complexity of the order (e.g., "BO" for Bracket Order)
        
        Returns:
            Exit response with brokerOrderId and requestTime
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/exit/sno"
            # API expects array format with orderNo field
            payload = {
                    "orderNo": broker_order_id,
                    "orderComplexity": order_complexity
                }
            
            
            logger.info(f"Exiting bracket order: {broker_order_id}")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            logger.info(f"Bracket order exited successfully: {broker_order_id}")
            return response.get('result', [{}])[0]
        
        except TradionAPIError as e:
            logger.error(f"Exit bracket order failed: {e}")
            raise OrderError(e.error_code, e.message)

    
    # -----------------------
    # PORTFOLIO & FUNDS
    # -----------------------
    
    async def get_holdings(self) -> List[Dict[str, Any]]:
        """
        Get long-term holdings (DEMAT account)
        
        Returns:
            List of holdings with quantity, average price, etc.
        """
        try:
            url = f"{Config.ORDER_BASE}/holdings/productType"
            
            logger.debug("Fetching holdings")
            
            response = await self.http.request(
                "GET",
                url,
                json={},
                headers=self._auth_header()
            )
            
            holdings = response.get('result', [])
            logger.info(f"Fetched {len(holdings)} holdings")
            
            return holdings
        
        except Exception as e:
            logger.error(f"Failed to fetch holdings: {e}")
            raise
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current day positions (open positions)
        
        Returns:
            List of positions with P&L, quantity, etc.
        """
        try:
            url = f"{Config.ORDER_BASE}/positions"
            
            logger.debug("Fetching positions")
            
            response = await self.http.request(
                "GET",
                url,
                json={},
                headers=self._auth_header()
            )
            
            logger.debug(f"Positions API response: {response}")
            
            result = response.get('result')
            
            # Handle None or empty result
            if result is None:
                logger.warning("Positions API returned None result")
                return []
            
            # If result is not a list, try to handle it
            if not isinstance(result, list):
                logger.warning(f"Positions API returned non-list result: {type(result)}")
                return []
            
            logger.info(f"Fetched {len(result)} positions")
            return result
        
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}", exc_info=True)
            return []  # Return empty list instead of raising
    
    async def square_off_position(self, square_off_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Square off (close) open positions
        
        Args:
            square_off_payload: List of positions to close with order details
        
        Returns:
            Square off response
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/positions/sqroff"
            
            logger.info(f"Squaring off {len(square_off_payload)} position(s)")
            
            response = await self.http.request(
                "POST",
                url,
                json=square_off_payload,
                headers=self._auth_header()
            )
            
            logger.info("Positions squared off successfully")
            return response.get('result', [])
        
        except Exception as e:
            logger.error(f"Failed to square off positions: {e}")
            raise
        
    # -----------------------
    # GTT ORDER
    # -----------------------
    
    async def place_gtt_order(
        self,
        trading_symbol: str,
        exchange: str,
        transaction_type: str,
        order_type: str,
        product: str,
        validity: str,
        quantity: int,
        price: float,
        order_complexity: str,
        instrument_id: str,
        gtt_type: str,
        gtt_value: float
    ) -> Dict[str, Any]:
        """
        Place a GTT (Good Till Triggered) order
        
        Args:
            trading_symbol: Trading symbol (e.g., "SILVER25SEP25C100000")
            exchange: Exchange code (e.g., "NSE", "BSE", "MCX")
            transaction_type: "BUY" or "SELL"
            order_type: Order type - "LIMIT", "MARKET", "SL", "SLM"
            product: Product type - "INTRADAY", "LONGTERM", "MTF"
            validity: Validity period - "DAY", "IOC"
            quantity: Quantity as string
            price: Order price
            order_complexity: Complexity - "REGULAR", "AMO"
            instrument_id: Unique instrument ID
            gtt_type: GTT type (e.g., "LTP_A_O")
            gtt_value: Trigger price value as string
        
        Returns:
            GTT order response with orderNo and requestTime
        
        Raises:
            OrderError: If GTT order placement fails
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/gtt/execute"
            payload = {
                "tradingSymbol": trading_symbol,
                "exchange": exchange,
                "transactionType": transaction_type,
                "orderType": order_type,
                "product": product,
                "validity": validity,
                "quantity": quantity,
                "price": price,
                "orderComplexity": order_complexity,
                "instrumentId": instrument_id,
                "gttType": gtt_type,
                "gttValue": gtt_value
            }
            
            logger.info(f"Placing GTT order: {transaction_type} {quantity} x {trading_symbol} @ {price}, trigger: {gtt_value}")
            logger.debug(f"GTT order payload: {payload}")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            result = response.get('result', [{}])[0]
            order_no = result.get('orderNo', 'UNKNOWN')
            request_time = result.get('requestTime', 'N/A')
            
            logger.info(f"GTT order placed - Order No: {order_no}, Time: {request_time}")
            return result
        
        except TradionAPIError as e:
            logger.error(f"GTT order placement failed: {e}")
            raise OrderError(e.error_code, e.message)
        
        except Exception as e:
            logger.error(f"Unexpected error placing GTT order: {e}")
            raise OrderError("UNKNOWN", str(e))
    
    async def get_gtt_orderbook(self) -> List[Dict[str, Any]]:
        """
        Get all GTT orders (active, triggered, cancelled)
        
        Returns:
            List of GTT orders with details like orderNo, tradingSymbol, 
            gttType, gttValue, status, etc.
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/gtt/orderbook"
            
            logger.debug("Fetching GTT order book")
            
            response = await self.http.request(
                "GET",
                url,
                json={},
                headers=self._auth_header()
            )
            
            gtt_orders = response.get('result', [])
            logger.info(f"Fetched {len(gtt_orders)} GTT orders")
            
            return gtt_orders
        
        except Exception as e:
            logger.error(f"Failed to fetch GTT order book: {e}")
            raise
    
    async def modify_gtt_order(
        self,
        broker_order_id: str,
        trading_symbol: str,
        exchange: str,
        order_type: str,
        product: str,
        validity: str,
        quantity: str,
        price: str,
        order_complexity: str,
        instrument_id: str,
        gtt_type: str,
        gtt_value: str
    ) -> Dict[str, Any]:
        """
        Modify an existing GTT order
        
        Args:
            broker_order_id: Order ID to modify
            trading_symbol: Trading symbol
            exchange: Exchange code
            order_type: Order type - "LIMIT", "MARKET", "SL", "SLM"
            product: Product type - "INTRADAY", "LONGTERM", "MTF"
            validity: Validity period - "DAY", "IOC"
            quantity: Quantity as string
            price: Order price as string
            order_complexity: Complexity - "REGULAR", "AMO"
            instrument_id: Unique instrument ID
            gtt_type: GTT type (e.g., "LTP_A_O")
            gtt_value: New trigger price value as string
        
        Returns:
            Modified GTT order response
        
        Raises:
            OrderError: If modification fails
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/gtt/modify"
            payload = {
                "tradingSymbol": trading_symbol,
                "exchange": exchange,
                "orderType": order_type,
                "product": product,
                "validity": validity,
                "quantity": quantity,
                "price": price,
                "orderComplexity": order_complexity,
                "instrumentId": instrument_id,
                "gttType": gtt_type,
                "gttValue": gtt_value,
                "brokerOrderId": broker_order_id
            }
            
            logger.info(f"Modifying GTT order: {broker_order_id}")
            logger.debug(f"GTT modify payload: {payload}")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            result = response.get('result', [{}])[0]
            logger.info(f"GTT order modified successfully: {broker_order_id}")
            return result
        
        except TradionAPIError as e:
            logger.error(f"GTT order modification failed: {e}")
            raise OrderError(e.error_code, e.message)
        
        except Exception as e:
            logger.error(f"Unexpected error modifying GTT order: {e}")
            raise OrderError("UNKNOWN", str(e))
    
    async def cancel_gtt_order(self, broker_order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing GTT order
        
        Args:
            broker_order_id: GTT Order ID to cancel
        
        Returns:
            Cancellation response with orderNo and requestTime
        
        Raises:
            OrderError: If cancellation fails
        """
        try:
            url = f"{Config.ORDER_BASE}/orders/gtt/cancel"
            payload = {"brokerOrderId": broker_order_id}
            
            logger.info(f"Cancelling GTT order: {broker_order_id}")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            result = response.get('result', [{}])[0]
            logger.info(f"GTT order cancelled successfully: {broker_order_id}")
            return result
        
        except TradionAPIError as e:
            logger.error(f"GTT order cancellation failed: {e}")
            raise OrderError(e.error_code, e.message)
        
        except Exception as e:
            logger.error(f"Unexpected error cancelling GTT order: {e}")
            raise OrderError("UNKNOWN", str(e))
    
    # -----------------------
    # FUNDS
    # -----------------------
    
    async def get_funds(self) -> Dict[str, Any]:
        """
        Get available funds and margin details
        
        Returns:
            Funds details with available balance, utilized margin, etc.
        """
        try:
            url = f"{Config.ORDER_BASE}/limits/"
            
            logger.debug("Fetching funds")
            
            response = await self.http.request(
                "GET",
                url,
                json={},
                headers=self._auth_header()
            )
            
            funds = response.get('result', [{}])[0]
            logger.info(f"Available balance: Rs.{funds.get('openingCashLimit', 0)}")
            
            return response
        
        except Exception as e:
            logger.error(f"Failed to fetch funds: {e}")
            raise
    
    # -----------------------
    # PROFILE
    # -----------------------
    
    async def get_profile(self) -> Dict[str, Any]:
        """
        Get user profile information
        
        Returns:
            Profile with clientId, name, exchanges, products, etc.
        """
        try:
            url = f"{Config.ORDER_BASE}/profile"
            
            logger.debug("Fetching profile")
            
            response = await self.http.request(
                "GET",
                url,
                json={},
                headers=self._auth_header()
            )
            
            profile = response.get('result', [{}])[0]
            logger.info(f"Profile: {profile.get('clientName')} ({profile.get('clientId')})")
            
            return response
        
        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}")
            raise
    
    # -----------------------
    # WEBSOCKET SESSION
    # -----------------------
    
    async def create_ws_session(self) -> str:
        """
        Create WebSocket session for market data
        
        Returns:
            Session token for WebSocket connection
        """
        try:
            url = f"{Config.ORDER_BASE}/profile/createWsSess"
            payload = {
                "source": "API",
                "userId": self.user_id,
                "token": self.access_token
            }
            
            logger.debug("Creating WebSocket session")
            
            response = await self.http.request(
                "POST",
                url,
                json=payload,
                headers=self._auth_header()
            )
            
            logger.info("WebSocket session created successfully")
            return self.access_token
        
        except Exception as e:
            logger.error(f"Failed to create WebSocket session: {e}")
            raise
    
    async def close(self):
        """Close HTTP session"""
        await self.http.close()
        logger.info("InteractiveClient closed")
