"""Cache exception classes"""


class CacheException(Exception):
    pass


class CacheWarning(RuntimeWarning):
    """Issued at runtime."""


class CreationAbortedError(Exception):
    """Deprecated."""


class InvalidCacheBackendError(CacheException, ImportError):
    pass


class MissingCacheParameter(CacheException):
    pass


class LockError(CacheException):
    pass


class InvalidCryptoBackendError(CacheException):
    pass
