Exception Handling API
====================

The weex-client provides a comprehensive exception hierarchy designed for Python 3.14+ pattern matching and structured error handling.

.. autoclass:: weex_client.exceptions.WEEXError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: weex_client.exceptions.WEEXAuthenticationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: weex_client.exceptions.WEEXRateLimitError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: weex_client.exceptions.WEEXSystemError
   :members:
   :undoc-members:
   :show-inheritance:

Exception Hierarchy
------------------

.. inheritance-diagram:: weex_client.exceptions
   :parts: 1

Base Exceptions
---------------

WEEXError
~~~~~~~~~~

The base exception class for all Weex-related errors:

.. code-block:: python

   from weex_client.exceptions import WEEXError

   try:
       # API call that might fail
       response = await client.place_order(order)
   except WEEXError as e:
       print(f"Error code: {e.code}")
       print(f"Error message: {e.message}")
       print(f"Timestamp: {e.timestamp}")
       print(f"Request ID: {e.request_id}")

WEEXAuthenticationError
~~~~~~~~~~~~~~~~~~~~~~

Raised when API credentials are invalid or missing:

.. code-block:: python

   from weex_client.exceptions import WEEXAuthenticationError

   try:
       response = await client.get_account_balance()
   except WEEXAuthenticationError as e:
       print(f"🔐 Authentication failed: {e.code}")
       print(f"Check your API credentials in .env file")
       if e.code == 40001:
           print("Invalid API key - check WEEX_API_KEY")
       elif e.code == 40002:
           print("Invalid signature - check WEEX_SECRET_KEY")

WEEXRateLimitError
~~~~~~~~~~~~~~~~~~

Raised when API rate limits are exceeded:

.. code-block:: python

   from weex_client.exceptions import WEEXRateLimitError

   try:
       response = await client.get_ticker("BTCUSDT")
   except WEEXRateLimitError as e:
       print(f"⏱️ Rate limited: wait {e.retry_after} seconds")
       print(f"Request count: {e.request_count}")
       print(f"Limit: {e.request_limit}")
       
       # Implement retry logic
       await asyncio.sleep(e.retry_after)

WEEXSystemError
~~~~~~~~~~~~~~~

Raised for system-level errors and maintenance:

.. code-block:: python

   from weex_client.exceptions import WEEXSystemError

   try:
       response = await client.place_order(order)
   except WEEXSystemError as e:
       print(f"⚠️ System error: {e.code}")
       print(f"Service: {e.service}")
       print(f"Retry after: {e.retry_after}")
       
       if e.service == "matching":
           print("🔄 Matching engine issue - retry after delay")
       elif e.service == "market":
           print("📊 Market data issue - check market status")

Error Code Reference
-------------------

Authentication Errors
~~~~~~~~~~~~~~~~~~~~

.. list-table:: Authentication Error Codes
   :header-rows: 1

   * - Code
     - Description
     - Solution
   * - 40001
     - Invalid API key
     - Check ``WEEX_API_KEY`` in .env
   * - 40002
     - Invalid signature
     - Check ``WEEX_SECRET_KEY`` and timestamp
   * - 40003
     - Invalid passphrase
     - Check ``WEEX_PASSPHRASE`` in .env
   * - 40004
     - API key expired
     - Generate new API key
   * - 40005
     - Insufficient permissions
     - Update API key permissions

Rate Limit Errors
~~~~~~~~~~~~~~~~~

.. list-table:: Rate Limit Error Codes
   :header-rows: 1

   * - Code
     - Description
     - Retry Strategy
   * - 40029
     - Too many requests
     - Wait ``retry_after`` seconds
   * - 40030
     - Order rate limit exceeded
     - Reduce order frequency
   * - 40031
     - Connection rate limit
     - Implement connection pooling
   * - 40032
     - WebSocket connection limit
     - Reduce WebSocket connections

System Errors
~~~~~~~~~~~~~~

.. list-table:: System Error Codes
   :header-rows: 1

   * - Code
     - Description
     - Impact
   * - 50001
     - Internal server error
     - Temporary, retry after delay
   * - 50002
     - Database connection error
     - Temporary, system maintenance
   * - 50003
     - Matching engine error
     - May affect order processing
   * - 50004
     - Market data service error
     - Real-time data unavailable

Pattern Matching Examples
------------------------

Python 3.14 Pattern Matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from weex_client.exceptions import *
   from weex_client import WeexAsyncClient, WeexConfig

   async def advanced_error_handling():
       """Comprehensive error handling with pattern matching"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           try:
               balance = await client.get_account_balance()
               return balance
               
           except WEEXError as e:
               match e:
                   # Authentication errors
                   case WEEXAuthenticationError(code=40001):
                       print("🔐 Invalid API key - check .env file")
                       await handle_invalid_api_key()
                   
                   case WEEXAuthenticationError(code=40002):
                       print("🔐 Invalid signature - check secret key")
                       await handle_invalid_signature()
                   
                   case WEEXAuthenticationError(code=40003):
                       print("🔐 Invalid passphrase - check .env file")
                       await handle_invalid_passphrase()
                   
                   # Rate limit errors
                   case WEEXRateLimitError(retry_after=delay, request_count=count):
                       print(f"⏱️ Rate limited: {count} requests, wait {delay}s")
                       await asyncio.sleep(delay)
                       return await retry_operation()
                   
                   # System errors
                   case WEEXSystemError(service="matching", retry_after=delay):
                       print(f"🔄 Matching engine issue: retry in {delay}s")
                       await asyncio.sleep(delay)
                       return await retry_operation()
                   
                   case WEEXSystemError(service="market"):
                       print("📊 Market data service unavailable")
                       await handle_market_data_outage()
                   
                   # Generic errors with structured handling
                   case WEEXError(code=code, message=msg) if 400 <= code < 500:
                       print(f"❌ Client error {code}: {msg}")
                       await handle_client_error(code, msg)
                   
                   case WEEXError(code=code, message=msg) if 500 <= code < 600:
                       print(f"⚠️ Server error {code}: {msg}")
                       await handle_server_error(code, msg)
                   
                   # Fallback for unknown errors
                   case WEEXError() as unknown_error:
                       print(f"❓ Unknown Weex error: {unknown_error}")
                       await handle_unknown_error(unknown_error)

   async def handle_invalid_api_key():
       """Handle invalid API key scenario"""
       print("🔧 Steps to fix invalid API key:")
       print("1. Check your .env file exists")
       print("2. Verify WEEX_API_KEY is correct")
       print("3. Ensure API key is enabled")
       print("4. Check IP whitelist settings")

   async def retry_operation():
       """Retry logic after handling error"""
       # Implementation of retry logic
       pass

Nested Pattern Matching
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def nested_error_handling():
       """Complex error handling with nested patterns"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           try:
               # Multiple operations that might fail
               balance_task = asyncio.create_task(client.get_account_balance())
               ticker_task = asyncio.create_task(client.get_ticker("BTCUSDT"))
               order_task = asyncio.create_task(client.place_order(order))
               
               results = await asyncio.gather(
                   balance_task, ticker_task, order_task,
                   return_exceptions=True
               )
               
               # Handle results with nested pattern matching
               for i, result in enumerate(results):
                   operation = ["balance", "ticker", "order"][i]
                   
                   match result:
                       case WEEXError() as error:
                           match error:
                               case WEEXRateLimitError(retry_after=delay):
                                   print(f"⏱️ {operation} rate limited: wait {delay}s")
                               
                               case WEEXAuthenticationError():
                                   print(f"🔐 {operation} authentication failed")
                               
                               case WEEXSystemError(service=svc):
                                   print(f"⚠️ {operation} system error in {svc}")
                               
                               case _:
                                   print(f"❌ {operation} error: {error}")
                       
                       case Exception() as other_error:
                           print(f"💥 {operation} unexpected error: {other_error}")
                       
                       case _:
                           print(f"✅ {operation} successful: {result}")

Error Recovery Strategies
------------------------

Retry Logic
~~~~~~~~~~~

.. code-block:: python

   from tenacity import retry, stop_after_attempt, wait_exponential
   from weex_client.exceptions import WEEXRateLimitError, WEEXSystemError

   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=4, max=10),
       retry=retry_if_exception_type((WEEXRateLimitError, WEEXSystemError))
   )
   async def resilient_api_call(api_func, *args, **kwargs):
       """Resilient API call with automatic retry"""
       try:
           return await api_func(*args, **kwargs)
       except WEEXRateLimitError as e:
           print(f"🔄 Retrying after rate limit: wait {e.retry_after}s")
           raise
       except WEEXSystemError as e:
           print(f"🔄 Retrying after system error: {e.service}")
           raise

   # Usage
   try:
       balance = await resilient_api_call(client.get_account_balance)
   except WEEXRateLimitError:
       print("❌ Max retries exceeded due to rate limiting")
   except WEEXSystemError:
       print("❌ Max retries exceeded due to system errors")

Circuit Breaker Pattern
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class CircuitBreaker:
       def __init__(self, failure_threshold=5, timeout=60):
           self.failure_threshold = failure_threshold
           self.timeout = timeout
           self.failure_count = 0
           self.last_failure_time = None
           self.state = "closed"  # closed, open, half-open
       
       async def call(self, func, *args, **kwargs):
           """Execute function with circuit breaker protection"""
           if self.state == "open":
               if time.time() - self.last_failure_time > self.timeout:
                   self.state = "half-open"
               else:
                   raise WEEXSystemError("Circuit breaker is open")
           
           try:
               result = await func(*args, **kwargs)
               if self.state == "half-open":
                   self.reset()
               return result
           except WEEXError as e:
               self.record_failure()
               raise
       
       def record_failure(self):
           """Record a failure"""
           self.failure_count += 1
           self.last_failure_time = time.time()
           
           if self.failure_count >= self.failure_threshold:
               self.state = "open"
               print("🚨 Circuit breaker opened")
       
       def reset(self):
           """Reset circuit breaker"""
           self.failure_count = 0
           self.state = "closed"
           print("✅ Circuit breaker reset")

   # Usage
   circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

   async def safe_trading_operation():
       try:
           balance = await circuit_breaker.call(client.get_account_balance)
           return balance
       except WEEXSystemError as e:
           if "Circuit breaker" in str(e):
               print("🚨 Service temporarily unavailable")
               return None
           raise

Context-Aware Error Handling
---------------------------

Trading Context
~~~~~~~~~~~~~~

.. code-block:: python

   async def context_aware_trading():
       """Error handling adapted to trading context"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           try:
               # Critical operation: place order
               order_result = await client.place_order(order)
               
               # Less critical: get additional data
               ticker_data = await client.get_ticker("BTCUSDT")
               balance_data = await client.get_account_balance()
               
               return {
                   "order": order_result,
                   "ticker": ticker_data,
                   "balance": balance_data
               }
               
           except WEEXError as e:
               match e:
                   # Handle differently based on trading context
                   case WEEXRateLimitError():
                       print("⏱️ Rate limit during trading -暂停操作")
                       await trading_emergency_stop()
                   
                   case WEEXAuthenticationError():
                       print("🔐 Authentication failed - check credentials")
                       await emergency_security_check()
                   
                   case WEEXSystemError(service="matching"):
                       print("🔄 Matching engine issue - cancel pending orders")
                       await cancel_all_pending_orders()
                   
                   case WEEXSystemError(service="market"):
                       print("📊 Market data issue - use cached data")
                       return await use_cached_market_data()

Production Error Handling
-------------------------

Logging and Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import structlog

   logger = structlog.get_logger()

   async def production_error_handling():
       """Error handling for production environment"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           try:
               result = await client.get_account_balance()
               logger.info("API call successful", operation="get_balance")
               return result
               
           except WEEXError as e:
               # Structured logging with error context
               error_context = {
                   "error_code": e.code,
                   "error_message": e.message,
                   "timestamp": e.timestamp,
                   "request_id": e.request_id,
                   "operation": "get_balance"
               }
               
               match e:
                   case WEEXRateLimitError(retry_after=delay):
                       logger.warning(
                           "Rate limit exceeded",
                           retry_after=delay,
                           **error_context
                       )
                       await asyncio.sleep(delay)
                       # Retry logic here
                   
                   case WEEXAuthenticationError():
                       logger.error(
                           "Authentication failed",
                           severity="critical",
                           **error_context
                       )
                       # Alert operations team
                       await alert_security_team(e)
                   
                   case WEEXSystemError():
                       logger.error(
                           "System error occurred",
                           severity="high",
                           **error_context
                       )
                       # Check system status
                       await check_system_health()
                   
                   case _:
                       logger.error(
                           "Unknown error occurred",
                           severity="medium",
                           **error_context
                       )

   async def alert_security_team(error):
       """Send alert to security team"""
       # Implementation of alert system
       pass

   async def check_system_health():
       """Check overall system health"""
       # Implementation of health check
       pass

Custom Exception Extensions
-------------------------

Business-Specific Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client.exceptions import WEEXError

   class TradingStrategyError(WEEXError):
       """Custom exception for trading strategy errors"""
       def __init__(self, message: str, strategy_name: str, **kwargs):
           super().__init__(
               message=message,
               code=60001,
               strategy_name=strategy_name,
               **kwargs
           )

   class RiskManagementError(WEEXError):
       """Custom exception for risk management violations"""
       def __init__(self, message: str, risk_type: str, **kwargs):
           super().__init__(
               message=message,
               code=60002,
               risk_type=risk_type,
               **kwargs
           )

   class PortfolioError(WEEXError):
       """Custom exception for portfolio management errors"""
       def __init__(self, message: str, portfolio_value: float, **kwargs):
           super().__init__(
               message=message,
               code=60003,
               portfolio_value=portfolio_value,
               **kwargs
           )

   # Usage with pattern matching
   async def trading_operation():
       try:
           # Trading logic here
           pass
       except WEEXError as e:
           match e:
               case TradingStrategyError(strategy_name=name):
                   print(f"📈 Strategy {name} failed: {e.message}")
               
               case RiskManagementError(risk_type=risk):
                   print(f"🛡️ Risk management violation ({risk}): {e.message}")
               
               case PortfolioError(portfolio_value=value):
                   print(f"💼 Portfolio error (${value}): {e.message}")

Error Analytics
--------------

Error Tracking
~~~~~~~~~~~~~~

.. code-block:: python

   class ErrorTracker:
       def __init__(self):
           self.error_counts = {}
           self.error_timeline = []
           self.error_patterns = {}
       
       def record_error(self, error: WEEXError):
           """Record error for analytics"""
           error_type = type(error).__name__
           
           # Count errors by type
           self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
           
           # Record timeline
           self.error_timeline.append({
               "timestamp": datetime.now(),
               "type": error_type,
               "code": error.code,
               "message": error.message
           })
           
           # Analyze patterns
           self.analyze_patterns(error)
       
       def analyze_patterns(self, error: WEEXError):
           """Analyze error patterns"""
           # Group by error code
           code_key = f"{error.__class__.__name__}_{error.code}"
           self.error_patterns[code_key] = self.error_patterns.get(code_key, 0) + 1
       
       def get_error_summary(self) -> dict:
           """Get error summary report"""
           return {
               "total_errors": sum(self.error_counts.values()),
               "error_types": self.error_counts,
               "common_patterns": sorted(
                   self.error_patterns.items(),
                   key=lambda x: x[1],
                   reverse=True
               )[:5],
               "recent_errors": self.error_timeline[-10:]
           }

   # Usage
   error_tracker = ErrorTracker()

   async def tracked_trading():
       try:
           # Trading operations
           pass
       except WEEXError as e:
           error_tracker.record_error(e)
           raise
       
       # Generate periodic reports
       if should_generate_report():
           summary = error_tracker.get_error_summary()
           logger.info("Error summary", **summary)

Performance Considerations
------------------------

Error Handling Overhead
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def optimized_error_handling():
       """Optimized error handling for high-frequency operations"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           # Use dictionary lookup for faster error handling
           error_handlers = {
               WEEXAuthenticationError: handle_auth_error,
               WEEXRateLimitError: handle_rate_limit,
               WEEXSystemError: handle_system_error,
           }
           
           try:
               result = await client.get_account_balance()
               return result
           except WEEXError as e:
               handler = error_handlers.get(type(e))
               if handler:
                   return await handler(e)
               else:
                   return await handle_generic_error(e)

   async def handle_auth_error(error):
       """Optimized auth error handler"""
       # Fast, specific handling
       pass

   async def handle_rate_limit(error):
       """Optimized rate limit handler"""
       # Fast, specific handling
       pass

Error Handling Best Practices
---------------------------

1. **Use pattern matching** for Python 3.14+ instead of if/elif chains
2. **Log structured error data** for debugging and analytics
3. **Implement retry logic** with exponential backoff
4. **Use circuit breakers** for fault tolerance
5. **Customize error handling** based on business context
6. **Track error patterns** for system optimization
7. **Provide clear user feedback** for actionable errors
8. **Separate critical from non-critical errors** in recovery strategies

.. code-block:: python

   async def best_practice_example():
       """Demonstrating error handling best practices"""
       config = WeexConfig.from_env()
       
       async with WeexAsyncClient(config) as client:
           while True:  # Main trading loop
               try:
                   # Trading operation
                   result = await trading_operation(client)
                   logger.info("Operation successful", result=result)
                   await asyncio.sleep(1)  # Rate limiting
               
               except WEEXRateLimitError as e:
                   # Specific rate limit handling
                   logger.warning("Rate limited", retry_after=e.retry_after)
                   await asyncio.sleep(e.retry_after)
                   continue  # Retry the operation
               
               except WEEXAuthenticationError as e:
                   # Critical authentication issue
                   logger.error("Authentication failed", code=e.code)
                   await notify_admins("Authentication failure")
                   break  # Exit loop - requires manual intervention
               
               except WEEXSystemError as e:
                   # System error with recovery
                   logger.error("System error", service=e.service)
                   await implement_fallback_strategy()
                   continue  # Try with fallback
               
               except WEEXError as e:
                   # Generic Weex error
                   logger.error("Generic Weex error", code=e.code, message=e.message)
                   await safe_stop()
                   break
               
               except Exception as e:
                   # Unexpected error
                   logger.critical("Unexpected error", error=str(e))
                   await emergency_shutdown()
                   break