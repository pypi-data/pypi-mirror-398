from asgiref.sync import sync_to_async

from .backend import ValkeyCacheBase


class ValkeyWSGICache(ValkeyCacheBase):
    """
    Valkey cache backend for WSGI environments.

    This backend relies on Django's default async-to-sync wrappers for most
    async methods. It only implements custom wrappers for methods not present
    in Django's BaseCache or ones that need to preserve specific behavior
    from the synchronous implementation.
    """

    async def aincr(self, key, delta=1, version=None):
        return await sync_to_async(self.incr)(key, delta=delta, version=version)

    async def adecr(self, key, delta=1, version=None):
        return await sync_to_async(self.decr)(key, delta=delta, version=version)

    async def ahas_key(self, key, version=None):
        return await sync_to_async(self.has_key)(key, version=version)

    async def alock(
        self,
        key,
        version=None,
        timeout=None,
        sleep=0.1,
        blocking=True,
        blocking_timeout=None,
        thread_local=True,
    ):
        return await sync_to_async(self.lock)(
            key,
            version=version,
            timeout=timeout,
            sleep=sleep,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
            thread_local=thread_local,
        )
