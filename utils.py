"""
Utility functions for Blue Bird to be shared with the services.
"""
import logging
from datetime import datetime

def cache(cacheTime, removeFunc=lambda key, time, val: None):
    """A decorator for caching the results of a function for a fixed amount of time

    All arguments and returned values of cached functions must be
    hashable, otherwise you will get errors. Written to be generic
    enough to interact with R and delete those variables if necessary
    by accepting a function that is called when an object is removed
    from the cache.

    The function is called with the arguments passed to the function,
    the time the cache instance was created and the result of the
    function that was cached.

    Usage:
    @cache(datetime.timedelta(days=1))
    @cache(datetime.timedelta(days=1), f)
    """
    cache = {}
    def dec(f):
        def call(*args, **kwargs):
            # Clean the cache of old entries
            now = datetime.now()
            # logging.info("%s: Cleaning cache at time %s", f.__name__, now)
            for key, (time, val) in cache.items():
                # logging.info("Checking cache of %s, the cache is %s old",
                #              key, now-time)
                if (now - time) > cacheTime:
                    # logging.info("%s: Removing %s %s", f.__name__,key, (time, val))
                    removeFunc(key, time, val)
                    del cache[key]

            # See if there is a cached result to return
            key = (args, tuple(kwargs.items()))
            if key in cache.keys(): return cache[key][1]
            else:
                cache[key] = (datetime.now(), f(*args, **kwargs))
                return cache[key][1]
        call.__name__ = f.__name__
        call.__doc__ = f.__doc__
        return call
    return dec
