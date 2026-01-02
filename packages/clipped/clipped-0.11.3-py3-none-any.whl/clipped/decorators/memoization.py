from typing import Callable


def memoize(func: Callable):
    """
    Decorator: provide result cache for wrapped func. Results are cached
    for given parameter list.

    See also: http://en.wikipedia.org/wiki/Memoization

    Example:

        @memoize
        def foo(param1, param2):
            return do_calculation(param1, param2)

        a = foo(1, 2)
        b = foo(1, 2)

        The second call is a cache hit and does not lead to a 'do_calculation'
        call.

    HINT: - The current implementation does not allow to clear the cache.
            Therefore, the decorator should only be used in limited scope,
            e.g. to enhance a locally defined methods.
          - The decorator does not work with keyword arguments.
    """

    cache = {}

    def wrapper(*x):
        if x not in cache:
            cache[x] = func(*x)
        return cache[x]

    return wrapper


def memoize_method(func: Callable):
    """
    Provides memoization for methods on a specific instance.
    Results are cached for given parameter list.

    See also: http://en.wikipedia.org/wiki/Memoization

    N.B. The cache object gets added to the instance instead of the global scope.
    Therefore cached results are restricted to that instance.
    The cache dictionary gets a name containing the name of the decorated function to
    avoid clashes.

    Example:

        class MyClass:
            @memoize
            def foo(self, a, b):
                return self._do_calculation(a, b)

    HINT: - The decorator does not work with keyword arguments.
    """

    cache_name = "__CACHED_{}".format(func.__name__)

    def wrapper(self, *args):
        cache = getattr(self, cache_name, None)
        if cache is None:
            cache = {}
            setattr(self, cache_name, cache)
        if args not in cache:
            cache[args] = func(self, *args)
        return cache[args]

    return wrapper
