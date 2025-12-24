import asyncio
import pickle
import zlib
from functools import wraps
from urllib.parse import urlparse

import valkey
import valkey.asyncio as valkey_async
from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache
from valkey.asyncio.connection import BlockingConnectionPool
from valkey.asyncio.connection import parse_url as async_parse_url
from valkey.asyncio.sentinel import Sentinel as AsyncSentinel
from valkey.connection import BlockingConnectionPool as SyncBlockingConnectionPool
from valkey.connection import parse_url
from valkey.sentinel import Sentinel

try:
    from valkey.asyncio.cluster import ValkeyCluster as AsyncValkeyCluster
    from valkey.cluster import ValkeyCluster
except ImportError:
    ValkeyCluster = None
    AsyncValkeyCluster = None


try:
    import zstd
except ImportError:
    zstd = None


# Global client registry
_CLIENTS = {}


def ignore_connection_errors(func):
    """
    Decorator that catches connection errors and returns a default value.
    """
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if not self._ignore_exceptions:
                return await func(self, *args, **kwargs)
            try:
                return await func(self, *args, **kwargs)
            except (valkey.exceptions.ConnectionError, valkey.exceptions.TimeoutError):
                if func.__name__ in ["get", "aget"]:
                    return kwargs.get("default") or args[1] if len(args) > 1 else None
                elif func.__name__ in [
                    "set",
                    "aset",
                    "add",
                    "aadd",
                    "delete",
                    "adelete",
                    "touch",
                    "atouch",
                ]:
                    return False
                elif func.__name__ in [
                    "incr",
                    "aincr",
                    "decr",
                    "adecr",
                    "has_key",
                    "ahas_key",
                ]:
                    return 0
                return None

        return async_wrapper
    else:

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            if not self._ignore_exceptions:
                return func(self, *args, **kwargs)
            try:
                return func(self, *args, **kwargs)
            except (valkey.exceptions.ConnectionError, valkey.exceptions.TimeoutError):
                if func.__name__ in ["get", "aget"]:
                    return kwargs.get("default") or args[1] if len(args) > 1 else None
                elif func.__name__ in [
                    "set",
                    "aset",
                    "add",
                    "aadd",
                    "delete",
                    "adelete",
                    "touch",
                    "atouch",
                ]:
                    return False
                elif func.__name__ in [
                    "incr",
                    "aincr",
                    "decr",
                    "adecr",
                    "has_key",
                    "ahas_key",
                ]:
                    return 0
                return None

        return sync_wrapper


class ValkeyCacheBase(BaseCache):
    def __init__(self, alias, params):
        super().__init__(params)
        self._location = params.get("LOCATION", "valkey://valkey:6379/1")
        self._options = params.get("OPTIONS", {})
        self._ignore_exceptions = self._options.get("IGNORE_EXCEPTIONS", False)
        self._compress_min_len = self._options.get("COMPRESS_MIN_LEN", 1024)
        self._cluster_mode = self._options.get("CLUSTER_MODE", False)

        if self._cluster_mode and ValkeyCluster is None:
            raise ImportError("valkey-py cluster support is not installed.")

        if zstd:
            self._compressor = "zstd"
            self._compress = zstd.compress
            self._decompress = zstd.decompress
            self._magic_byte = b"z"
        else:
            self._compressor = "zlib"
            self._compress = zlib.compress
            self._decompress = zlib.decompress
            self._magic_byte = b"\x8f"

    def _parse_sentinel_url(self, url):
        parts = urlparse(url)
        sentinels = []
        for sentinel_host in parts.netloc.split(","):
            host, port = sentinel_host.split(":")
            sentinels.append((host, int(port)))

        path_parts = parts.path.strip("/").split("/")
        service_name = path_parts[0]
        db = path_parts[1] if len(path_parts) > 1 else 0
        return sentinels, service_name, int(db)

    def _get_client(self, async_client=False):
        key = (self._location, self._cluster_mode, async_client)
        if key in _CLIENTS:
            return _CLIENTS[key]

        if self._location.startswith("sentinel://"):
            sentinels, service_name, db = self._parse_sentinel_url(self._location)

            kwargs = self._options.copy()
            kwargs.pop("IGNORE_EXCEPTIONS", None)
            kwargs.pop("COMPRESS_MIN_LEN", None)
            kwargs.pop("CLUSTER_MODE", None)

            if "connection_pool_timeout" in kwargs:
                kwargs["timeout"] = kwargs.pop("connection_pool_timeout")

            pool_class = None
            if "max_connections" in kwargs and "timeout" in kwargs:
                pool_class = (
                    BlockingConnectionPool
                    if async_client
                    else SyncBlockingConnectionPool
                )
            else:
                pool_class = (
                    valkey_async.ConnectionPool
                    if async_client
                    else valkey.ConnectionPool
                )

            sentinel_kwargs = {}  # Let valkey-py handle sentinel connection options

            if async_client:
                sentinel = AsyncSentinel(sentinels, **sentinel_kwargs)
                _CLIENTS[key] = sentinel.master_for(
                    service_name, db=db, connection_pool_class=pool_class, **kwargs
                )
            else:
                sentinel = Sentinel(sentinels, **sentinel_kwargs)
                _CLIENTS[key] = sentinel.master_for(
                    service_name, db=db, connection_pool_class=pool_class, **kwargs
                )
            return _CLIENTS[key]

        if self._cluster_mode:
            # Cluster mode uses from_url.
            connection_kwargs = self._options.copy()
            connection_kwargs.pop("IGNORE_EXCEPTIONS", None)
            connection_kwargs.pop("COMPRESS_MIN_LEN", None)
            connection_kwargs.pop("CLUSTER_MODE", None)
            if async_client:
                _CLIENTS[key] = AsyncValkeyCluster.from_url(
                    self._location, **connection_kwargs
                )
            else:
                _CLIENTS[key] = ValkeyCluster.from_url(
                    self._location, **connection_kwargs
                )
            return _CLIENTS[key]

        # For non-cluster mode, we'll create the connection pool manually
        # to ensure options are handled correctly, as requested by the user.
        url_options = (
            async_parse_url(self._location)
            if async_client
            else parse_url(self._location)
        )

        # Options from Django settings have precedence over URL options.
        # This combined_options dictionary will hold all arguments temporarily.
        combined_options = {**url_options, **self._options}

        # Pop django-vcache internal options.
        combined_options.pop("IGNORE_EXCEPTIONS", None)
        combined_options.pop("COMPRESS_MIN_LEN", None)
        combined_options.pop("CLUSTER_MODE", None)

        # Extract pool-specific options into pool_kwargs.
        pool_kwargs = {}
        if "max_connections" in combined_options:
            pool_kwargs["max_connections"] = int(
                combined_options.pop("max_connections")
            )
        if "connection_pool_timeout" in combined_options:
            pool_kwargs["timeout"] = float(
                combined_options.pop("connection_pool_timeout")
            )
        elif "timeout" in combined_options:  # URL-parsed timeout is also for the pool
            pool_kwargs["timeout"] = float(combined_options.pop("timeout"))

        # The remaining options in combined_options are connection-specific arguments.
        conn_kwargs = combined_options

        # Determine which ConnectionPool class to use.
        pool_class = (
            valkey_async.ConnectionPool if async_client else valkey.ConnectionPool
        )
        if (
            pool_kwargs.get("max_connections") is not None
            and pool_kwargs.get("timeout") is not None
        ):
            if async_client:
                pool_class = BlockingConnectionPool
            else:
                pool_class = SyncBlockingConnectionPool
        elif (
            pool_kwargs.get("max_connections") is None
            and pool_kwargs.get("timeout") is not None
        ):
            # If only timeout is specified without max_connections, use default pool
            # with timeout applied, as max_connections is usually required for Blocking.
            # This handles cases where timeout is from URL and max_connections is not
            # explicit. But, as per Valkey docs, if max_connections is not specified,
            # it will be unlimited. So, only use BlockingConnectionPool if
            # max_connections is also specified.
            pass  # Keep default pool_class

        # Create the connection pool.
        pool = pool_class(**pool_kwargs, **conn_kwargs)

        # Create the Valkey client with the connection pool.
        if async_client:
            _CLIENTS[key] = valkey_async.Valkey(connection_pool=pool)
        else:
            _CLIENTS[key] = valkey.Valkey(connection_pool=pool)

        return _CLIENTS[key]

    @property
    def client(self):
        return self._get_client(async_client=False)

    @property
    def async_client(self):
        return self._get_client(async_client=True)

    def get_raw_client(self, async_client=False):
        """
        Returns the underlying valkey connection object.
        """
        return self._get_client(async_client=async_client)

    def _get_expiration_time(self, timeout):
        if timeout is DEFAULT_TIMEOUT:
            timeout = self.default_timeout
        if timeout is None:
            return None  # No expiration
        if timeout == 0:
            return 0  # Expire immediately
        return int(timeout)

    def _encode(self, value):
        pickled_value = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        if self._compress_min_len and len(pickled_value) > self._compress_min_len:
            return self._magic_byte + self._compress(pickled_value)
        return pickled_value

    def _decode(self, value):
        if value.startswith(b"z"):
            if zstd:
                return pickle.loads(zstd.decompress(value[1:]))
            return None
        if value.startswith(b"\x8f"):
            return pickle.loads(zlib.decompress(value[1:]))
        return pickle.loads(value)

    # Sync methods
    @ignore_connection_errors
    def get(self, key, default=None, version=None):
        _key = self.make_key(key, version=version)
        value = self.client.get(_key)
        if value is None:
            return default
        return self._decode(value)

    @ignore_connection_errors
    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        _key = self.make_key(key, version=version)
        encoded_value = self._encode(value)
        ttl = self._get_expiration_time(timeout)
        if ttl == 0:
            self.client.delete(_key)
            return True
        elif ttl is None:
            return self.client.set(_key, encoded_value)
        else:
            return self.client.set(_key, encoded_value, ex=ttl)

    @ignore_connection_errors
    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        _key = self.make_key(key, version=version)
        encoded_value = self._encode(value)
        ttl = self._get_expiration_time(timeout)
        if ttl == 0:
            return False  # if timeout is 0, treat as not adding.
        elif ttl is None:
            return self.client.set(_key, encoded_value, nx=True)
        else:
            return self.client.set(_key, encoded_value, ex=ttl, nx=True)

    @ignore_connection_errors
    def delete(self, key, version=None):
        _key = self.make_key(key, version=version)
        return self.client.delete(_key) > 0

    def close(self, **kwargs):
        # Clients are shared globally, so we don't close them here.
        pass

    @ignore_connection_errors
    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        _key = self.make_key(key, version=version)
        ttl = self._get_expiration_time(timeout)
        if ttl == 0:
            return self.client.delete(_key) > 0
        elif ttl is None:
            return self.client.persist(_key)
        else:
            return self.client.expire(_key, ttl)

    @ignore_connection_errors
    def incr(self, key, delta=1, version=None):
        value = self.get(key, version=version)
        if value is None:
            if self._ignore_exceptions:
                return 0
            raise ValueError("Key '%s' does not exist." % key)
        if not isinstance(value, int):
            raise ValueError("Key '%s' contains a non-integer value." % key)
        new_value = value + delta
        self.set(key, new_value, version=version)
        return new_value

    @ignore_connection_errors
    def decr(self, key, delta=1, version=None):
        value = self.get(key, version=version)
        if value is None:
            if self._ignore_exceptions:
                return 0
            raise ValueError("Key '%s' does not exist." % key)
        if not isinstance(value, int):
            raise ValueError("Key '%s' contains a non-integer value." % key)
        new_value = value - delta
        self.set(key, new_value, version=version)
        return new_value

    def lock(
        self,
        key,
        version=None,
        timeout=None,
        sleep=0.1,
        blocking=True,
        blocking_timeout=None,
        thread_local=True,
    ):
        if self._cluster_mode:
            raise NotImplementedError("Locking is not supported in cluster mode.")
        _key = self.make_key(key, version=version)
        return self.client.lock(
            _key,
            timeout=timeout,
            sleep=sleep,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
            thread_local=thread_local,
        )

    @ignore_connection_errors
    def has_key(self, key, version=None):
        _key = self.make_key(key, version=version)
        return self.client.exists(_key)


class ValkeyCache(ValkeyCacheBase):
    # Async methods
    @ignore_connection_errors
    async def aget(self, key, default=None, version=None):
        _key = self.make_key(key, version=version)
        value = await self.async_client.get(_key)
        if value is None:
            return default
        return self._decode(value)

    @ignore_connection_errors
    async def aset(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        _key = self.make_key(key, version=version)
        encoded_value = self._encode(value)
        ttl = self._get_expiration_time(timeout)
        if ttl == 0:
            await self.async_client.delete(_key)
            return True
        elif ttl is None:
            return await self.async_client.set(_key, encoded_value)
        else:
            return await self.async_client.set(_key, encoded_value, ex=ttl)

    @ignore_connection_errors
    async def aadd(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        _key = self.make_key(key, version=version)
        encoded_value = self._encode(value)
        ttl = self._get_expiration_time(timeout)
        if ttl == 0:
            return False
        elif ttl is None:
            return await self.async_client.set(_key, encoded_value, nx=True)
        else:
            return await self.async_client.set(_key, encoded_value, ex=ttl, nx=True)

    @ignore_connection_errors
    async def adelete(self, key, version=None):
        _key = self.make_key(key, version=version)
        return await self.async_client.delete(_key) > 0

    async def aclose(self, **kwargs):
        # Clients are shared globally, so we don't close them here.
        pass

    @ignore_connection_errors
    async def atouch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        _key = self.make_key(key, version=version)
        ttl = self._get_expiration_time(timeout)
        if ttl == 0:
            return await self.async_client.delete(_key) > 0
        elif ttl is None:
            return await self.async_client.persist(_key)
        else:
            return await self.async_client.expire(_key, ttl)

    @ignore_connection_errors
    async def aincr(self, key, delta=1, version=None):
        value = await self.aget(key, version=version)
        if value is None:
            if self._ignore_exceptions:
                return 0
            raise ValueError("Key '%s' does not exist." % key)
        if not isinstance(value, int):
            raise ValueError("Key '%s' contains a non-integer value." % key)
        new_value = value + delta
        await self.aset(key, new_value, version=version)
        return new_value

    @ignore_connection_errors
    async def adecr(self, key, delta=1, version=None):
        value = await self.aget(key, version=version)
        if value is None:
            if self._ignore_exceptions:
                return 0
            raise ValueError("Key '%s' does not exist." % key)
        if not isinstance(value, int):
            raise ValueError("Key '%s' contains a non-integer value." % key)
        new_value = value - delta
        await self.aset(key, new_value, version=version)
        return new_value

    def alock(
        self,
        key,
        version=None,
        timeout=None,
        sleep=0.1,
        blocking=True,
        blocking_timeout=None,
        thread_local=True,
    ):
        if self._cluster_mode:
            raise NotImplementedError("Locking is not supported in cluster mode.")
        _key = self.make_key(key, version=version)
        return self.async_client.lock(
            _key,
            timeout=timeout,
            sleep=sleep,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
            thread_local=thread_local,
        )

    @ignore_connection_errors
    async def ahas_key(self, key, version=None):
        _key = self.make_key(key, version=version)
        return await self.async_client.exists(_key)
