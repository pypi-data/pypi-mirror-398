Configuration API
==================

The WeexClient uses a comprehensive configuration system designed for flexibility and security.

.. autoclass:: weex_client.config.WeexConfig
   :members:
   :undoc-members:
   :show-inheritance:

Connection Configuration
------------------------

.. autoclass:: weex_client.config.ConnectionConfig
   :members:
   :undoc-members:

Retry Configuration
-------------------

.. autoclass:: weex_client.config.RetryConfig
   :members:
   :undoc-members:

Rate Limit Configuration
------------------------

.. autoclass:: weex_client.config.RateLimitConfig
   :members:
   :undoc-members:

Logging Configuration
---------------------

.. autoclass:: weex_client.config.LoggingConfig
   :members:
   :undoc-members:

Environment Variables
---------------------

The configuration system supports loading from environment variables:

.. envvar:: WEEX_API_KEY

   Your Weex API key. Starts with "weex_".

.. envvar:: WEEX_SECRET_KEY

   Your Weex secret key for HMAC signature.

.. envvar:: WEEX_PASSPHRASE

   Your API passphrase.

.. envvar:: WEEX_ENVIRONMENT

   Target environment: ``development``, ``staging``, or ``production``.
   Default: ``development``

.. envvar:: WEEX_TIMEOUT

   Request timeout in seconds. Default: ``30``

.. envvar:: WEEX_MAX_RETRIES

   Maximum number of retry attempts. Default: ``3``

.. envvar:: WEEX_LOG_LEVEL

   Logging level: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``.
   Default: ``INFO``

Configuration Examples
-----------------------

Basic Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client.config import WeexConfig

   config = WeexConfig(
       api_key="your_api_key",
       secret_key="your_secret_key",
       passphrase="your_passphrase",
       environment="development"
   )

From Environment
~~~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client.config import WeexConfig

   # Load from environment variables
   config = WeexConfig.from_env()

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client.config import WeexConfig, ConnectionConfig, RetryConfig

   config = WeexConfig(
       api_key="your_api_key",
       secret_key="your_secret_key", 
       passphrase="your_passphrase",
       connection=ConnectionConfig(
           timeout=60,
           max_connections=20
       ),
       retry=RetryConfig(
           max_attempts=5,
           backoff_factor=2.0
       ),
       environment="staging"
   )

Trading Safety Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from weex_client.config import WeexConfig

   # For paper trading and testing
   config = WeexConfig(
       api_key="paper_trading_key",
       secret_key="paper_trading_secret",
       passphrase="paper_trading_pass",
       environment="development"  # Always use development for testing
   )

URL Resolution
--------------

The configuration automatically resolves API endpoints based on environment:

.. list-table:: Environment URLs
   :header-rows: 1

   * - Environment
     - Base URL
     - WebSocket URL
   * - development
     - https://development-api.weex.com
     - wss://development-ws.weex.com
   * - staging
     - https://staging-api.weex.com
     - wss://staging-ws.weex.com
   * - production
     - https://api.weex.com
     - wss://ws.weex.com

Configuration Validation
------------------------

The configuration system includes built-in validation:

.. code-block:: python

   try:
       config = WeexConfig.from_env()
       print(f"✅ Configuration valid for {config.environment}")
   except ValueError as e:
       print(f"❌ Configuration error: {e}")

Best Practices
--------------

Trading Safety
~~~~~~~~~~~~~~~

1. **Always use development environment** for testing and paper trading
2. **Never commit API credentials** to version control
3. **Use separate API keys** for development and production
4. **Enable IP whitelisting** when possible

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Use environment variables** for sensitive data
2. **Store non-sensitive defaults** in code
3. **Validate configuration** before API calls
4. **Log configuration status** (without secrets)

.. code-block:: python

   # Safe configuration logging
   config = WeexConfig.from_env()
   logger.info(f"Config loaded: environment={config.environment}, timeout={config.connection.timeout}")
   # Never log API keys or secrets!