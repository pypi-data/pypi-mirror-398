class ContextualPropertyCache:
    """
    Cache manager for objects that use contextual properties. Provides an api
    for storing and invalidating values as well as passthrough functions for
    easier use
    """
    # TODO: add ability to put expiration timestamps on values that causes them
    #  to return None
    # TODO: add counter and `invalidate_after` option to invalidate a cached
    #  value after a certain number of uses

    @property
    def cache_map(self):
        """
        A mapping of getter functions to their cached values
        """
        if not getattr(self, '__context_cache_map', None):
            setattr(self, '__context_cache_map', {})
        return getattr(self, '__context_cache_map')

    def cache(self, prop, context, value):
        """
        Maps a getter function to a cached value
        :param prop: the name of the property
        :param context: the context of the object
        :param value: stored value
        :return: value provided (passthrough)
        """
        self.cache_map[prop] = self.cache_map.get(prop, {})
        self.cache_map[prop][context] = value
        return value

    def get(self, prop, context):
        """
        Returns the cached value for the prop based on context
        :param prop: the name of the property
        :param context: the context of the object
        """
        return self.cache_map.get(prop, {}).get(context, None)

    def invalidate(self, prop, context):
        """
        Invalidates cached values for the provided property and context
        :param prop: the name of the property
        :param context: the context of the object
        """
        self.cache_map.get(prop, {}).pop(context, None)

    def cache_execute(self, prop, context, fn, obj, expires: int = None,
                      interval: int = None, max_uses: int = None):
        """
        Passthrough that either returns a cached value for the property and
        context or stores the value after executing the function.
        :param prop: name of the property
        :param context: context of the object
        :param fn: getter function
        :param obj: object operated on
        :param expires: expiration timestamp for reevaluation
        :param interval: time interval before needing to reevaluate
        :param max_uses: maximum number of times to return a cached value
         before rerunning the function
        :return:
        """
        if context in self.cache_map.get(prop, {}).keys():
            return self.get(prop, context)
        return self.cache(prop, context, fn(obj))

    def invalidate_execute(self, prop, context, fn, obj, val=None):
        """
        Passthrough that performs the invalidation and executes the function
        :param fn: setter/deleter function to execute
        :param obj: object operated on
        :param val: value provided to the object (setter only)
        :return:
        """
        if isinstance(context, (list, tuple, set)):
            for ctx in context:
                self.invalidate(prop, ctx)
        else:
            self.invalidate(prop, context)
        if val:
            return fn(obj, val)
        return fn(obj)

class ContextCacheObject:
    """
    Base object that provides tools for providing an object with a cache for
    contextual properties

    Provides a ``__context_cache__`` attribute that provides a cache manager
    """

    def __init__(self):
        self.__context_cache__ = ContextualPropertyCache()