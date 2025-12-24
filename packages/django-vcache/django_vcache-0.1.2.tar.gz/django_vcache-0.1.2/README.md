# django-vcache

A very fast Django cache backend for Valkey (and Redis). This async + sync backend is designed to be resource-efficient.

It powers the [GlitchTip](https://glitchtip.com) open-source error tracking platform.

Why django-vcache?

- Zero "Sync-to-Async" Overhead: Native implementations for both Sync (get) and Async (aget) methods. No thread-switching wrappers.
- Connection Efficiency: Maintains at most two client instances (one Sync, one Async) per configured backend.
- Lazy Loading: Connections are established only when a command is issued, keeping startup time instant and memory usage low.
- Raw Access: Easily borrow the underlying valkey-py client for advanced operations (locking, pipelines, custom data structures) without spinning up new connections. Use the existing client with [django-vtask](https://gitlab.com/glitchtip/django-vtask).
- Opinionated and Fast - We use libvalkey and focus on simplicity and speed over every possible use case. Stop thinking about which parser class to use and write your fast application.

## Installation

```bash
pip install django-vcache
```

## Usage

Update your `settings.py` to configure the cache backend:

```python
CACHES = {
    "default": {
        "BACKEND": "django_vcache.backend.ValkeyCache",
        "LOCATION": "valkey://your-valkey-host:6379/1",
        "OPTIONS": {
            "max_connections": 200,  # Example: limit the number of connections in the pool
            "connection_pool_timeout": 5, # Example: time to wait for a connection before raising an error
            "socket_connect_timeout": 5,  # Example: set a connection timeout
            "retry_on_timeout": True,     # Example: enable retry on timeout
        }
    },
}
```

The `max_connections` and `connection_pool_timeout` options enable sensible blocking behavior. When `max_connections` is reached, subsequent requests for a connection will wait for up to `connection_pool_timeout` seconds for a connection to become available before raising an error. It is recommended to set values for these options to prevent connection exhaustion.

You can then use Django's cache framework as usual:

```python
from django.core.cache import cache

cache.set('my_key', 'my_value', 30)
value = cache.get('my_key')
```

To access the underlying raw `valkey-py` client instance, you can use the `get_raw_client` method:

```python
# Get the synchronous client
sync_client = cache.get_raw_client()

# Get the asynchronous client
async_client = cache.get_raw_client(async_client=True)
```

## Async usage

You must use an ASGI server to run the asynchronous client. For example, you can use `granian` or `uvicorn`. This is due to limitations in the `valkey-py` library. aget will not run reliably on a WSGI server.

Example equivalent of Django runserver:
`granian --interface asgi --host 0.0.0.0 --port 8000 sample.asgi:application --reload`

## WSGI Compatibility

The primary `ValkeyCache` backend is designed for modern ASGI applications and provides native async support. However, for legacy systems running in a synchronous WSGI environment (like Gunicorn or uWSGI with default workers), calling async cache methods can be problematic.

For these specific cases, a WSGI-compatible backend is available. It ensures that async cache methods are safely wrapped, preventing errors related to event loop management in a synchronous context.

To use it, update your `settings.py`:

```python
CACHES = {
    "default": {
        "BACKEND": "django_vcache.wsgi.ValkeyWSGICache",
        "LOCATION": "valkey://your-valkey-host:6379/1",
        # ... other options
    },
}
```

> **Note:** `django-vcache` is optimized for ASGI. If your project is primarily WSGI-based, you may find that other cache backends like `django-redis` better suit your needs. The `ValkeyWSGICache` is provided as a compatibility layer, not a performance-focused feature.

## Contributing

### Development Environment

This project uses Docker for development. To get started:

1.  Clone the repository.
2.  Build and start the services:

    ```bash
    docker compose up -d --build
    ```

This will start a Valkey container and an `app` container with the Django sample project running on `http://localhost:8000`. The development server uses `granian` with auto-reload, so changes you make to the code will be reflected automatically.

#### Using Valkey Sentinel

To run the development environment with Valkey Sentinel enabled, use the override compose file:

```bash
docker compose -f compose.yml -f compose.sentinel.yml up -d --build
```

You will also need to configure your `sample/settings.py` to use the Sentinel URL. The recommended way is to set the `VALKEY_URL` environment variable before starting the services:

```bash
export VALKEY_URL="sentinel://localhost:26379/mymaster/1"
```

The application will then be available at `http://localhost:8000`.

### Using Valkey Cluster

To use `django-vcache` with a Valkey Cluster, set the `CLUSTER_MODE` option to `True` in your cache configuration. The `LOCATION` should point to one of the cluster's nodes; `valkey-py` will automatically discover the rest of the cluster nodes.

```python
CACHES = {
    "default": {
        "BACKEND": "django_vcache.backend.ValkeyCache",
        "LOCATION": "valkey://your-cluster-node-1:6379/1",
        "OPTIONS": {
            "CLUSTER_MODE": True,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
        }
    },
}
```

Note that distributed locking (via `cache.lock()` and `cache.alock()`) is not supported when `CLUSTER_MODE` is enabled, as this functionality is not provided by the underlying `valkey-py` library in cluster environments. Attempting to use these methods will raise a `NotImplementedError`.

To run the development environment with Valkey Cluster enabled, use the override compose file and environment variables:

```bash
docker compose -f compose.yml -f compose.cluster.yml up -d --build \
    -e VALKEY_URL='valkey://valkey-1:6379/1' \
    -e VALKEY_CLUSTER_MODE='true'
```

The application will then be available at `http://localhost:8000`.

### Running Tests

To run the test suite, execute the following command:

```bash
docker compose run --rm app bash -c "python sample/manage.py test"
```

## Credits

Inspired by the excellent work of django-valkey and django-redis, but re-architected for strict resource efficiency and modern async/sync hybrid stacks.
