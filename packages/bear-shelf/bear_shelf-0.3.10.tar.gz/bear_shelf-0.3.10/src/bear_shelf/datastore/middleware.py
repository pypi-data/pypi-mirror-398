"""Contains the base Middleware class and a CachingMiddleware implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from collections.abc import Mapping

    from bear_shelf.datastore.storage._common import Storage

# TODO: Improve the typing here, too many things are any


class Middleware:
    """The base class for all Middlewares.

    Middlewares hook into the read/write process, allowing you to
    extend the behaviour by adding caching, logging, ...

    Your middleware's ``__init__`` method has to call the parent class
    constructor so the middleware chain can be configured properly.
    """

    def __init__(self, storage_cls: type[Storage]) -> None:
        """Initialize the Middleware with the underlying storage class."""
        self._storage_cls: type[Storage] = storage_cls
        self.storage: Storage | None = None

    def __call__(self, *args, **kwargs) -> Self:
        """Create the storage instance and store it as self.storage.

        Usually a user creates a new instance like this::

            BearDB(storage=StorageClass)

        The storage keyword argument is used by BearDB this way::

            self.storage = storage(*args, **kwargs)

        As we can see, ``storage(...)`` runs the constructor and returns the
        new storage instance.

        So, when running ``self.storage = storage(*args, **kwargs)`` Python
        now will call ``__call__`` and BearDB will expect the return value to
        be the storage (or Middleware) instance. Returning the instance is
        simple, but we also got the underlying (*real*) StorageClass as an
        __init__ argument that still is not an instance.
        So, we initialize it in __call__ forwarding any arguments we receive
        from BearDB (``BearDB(arg1, kwarg1=value, storage=...)``).

        In case of nested Middlewares, calling the instance as if it was a
        class results in calling ``__call__`` what initializes the next
        nested Middleware that itself will initialize the next Middleware and
        so on.
        """
        self.storage = self._storage_cls(*args, **kwargs)
        return self

    def __getattr__(self, name: str) -> Any:
        """Forward all unknown attribute calls to the underlying storage, so we remain as transparent as possible."""
        return getattr(self.__dict__["storage"], name)


class CachingMiddleware(Middleware):
    """Add some caching to BearDB.

    This Middleware aims to improve performance by writing only
    the last DB state every :attr:`WRITE_CACHE_SIZE` time and reading always
    from cache.
    """

    WRITE_CACHE_SIZE = 1000
    """Number of write operations to cache before writing to disk."""

    def __init__(self, storage_cls: type[Storage]) -> None:  # TODO: Fix the Any
        """Initialize the CachingMiddleware with the underlying storage class."""
        super().__init__(storage_cls)  # Initialize the parent constructor
        self.cache = None
        self._cache_modified_count = 0

    def read(self) -> Any | Mapping[Any, Any]:  # TODO: Fix the Any
        """Read data from cache or storage."""
        if self.cache is None:
            if self.storage is None:
                raise RuntimeError("Middleware not initialized properly.")
            self.cache = self.storage.read()  # Empty cache: read from the storage
        return self.cache

    def write(self, data: Any) -> None:  # TODO: Fix the Any
        """Write data to cache and flush if necessary."""
        self.cache = data  # Store data in cache # TODO: Fix the Any
        self._cache_modified_count += 1

        # Check if we need to flush the cache
        if self._cache_modified_count >= self.WRITE_CACHE_SIZE:
            self.flush()

    def flush(self) -> None:
        """Flush all unwritten data to disk."""
        if self._cache_modified_count > 0:
            if self.storage is None:
                raise RuntimeError("Middleware not initialized properly.")
            if self.cache is None:
                raise RuntimeError("No data in cache to flush.")
            self.storage.write(self.cache)  # Force-flush the cache by writing the data to the storage
            self._cache_modified_count = 0

    def close(self) -> None:
        """Close the storage, flushing any unwritten data first."""
        self.flush()  # Flush potentially unwritten data
        if self.storage is not None:
            self.storage.close()  # Let the storage clean up too
