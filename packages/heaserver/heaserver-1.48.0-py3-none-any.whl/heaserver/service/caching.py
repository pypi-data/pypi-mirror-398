import datetime
import functools
from .util import now as datetime_now


DEFAULT_TTL = datetime.timedelta(hours=1)


def ttl_cache(func=None, *, ttl: datetime.timedelta = DEFAULT_TTL):
    """
    Decorator for caching the results of a function for a given maximum timedelta. Use this decorator if the function
    will not change its value for the given amount of time. After that period of time, calling the function will
    actually call the function.

    :param ttl: the maximum amount of time before which the decorated function will be actually called (i.e. the time
    to live). Defaults to 1 hour.

    Example:
    >>> import time
    >>> from datetime import timedelta
    >>> count = 0
    >>>
    >>> @ttl_cache(ttl=timedelta(minutes=1))  # Although a ttl is specified here, not specifying it will default to 1 hour
    ... def my_function() -> int:
    ...     global count
    ...     count += 1
    ...     return count
    ...
    >>> my_function()
    1
    >>> my_function()
    1
    >>> time.sleep(61)  # 1 minute, 1 second (just in case)
    >>> my_function()
    2
    """
    if func is None:
        return functools.partial(ttl_cache, ttl=ttl)

    time, value = None, None

    @functools.wraps(func)
    def wrapper(*args, **kw):
        nonlocal time
        nonlocal value
        now = datetime_now()
        if not time or now - time > ttl:
            value = func(*args, **kw)
            time = now
        return value
    return wrapper
