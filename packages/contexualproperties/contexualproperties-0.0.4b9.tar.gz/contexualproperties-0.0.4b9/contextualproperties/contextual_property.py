from copy import copy
from typing import Hashable, Tuple, List

from contextualproperties.context_manager import ObjectContextManager
from contextualproperties.context_cached import ContextualPropertyCache
from contextualproperties.property_aware import PropertyAwareObject
from contextualproperties.context_aware import ContextAwareObject
from contextualproperties.exceptions import MissingContextError


class ContextualObject(PropertyAwareObject, ContextAwareObject):
    """
    Base class that combines the tools of the propert- and context-aware
    base classes. Classes that use ``@contextualproperty`` properties should
    inherit this base class for full functionality
    """
    def __init__(self):
        PropertyAwareObject.__init__(self)
        ContextAwareObject.__init__(self)


class ContextualProperty(property):
    """
    Expanded version of the property class that allows objects to get, set, and
    delete properties based on the context of the object that has contextual
    properties
    """

    def __NO_GETTER(self, obj, *args, **kwargs):
        raise MissingContextError(context=obj.__context__.context,
                                  name=self.__name,
                                  type='getter')

    def __NO_SETTER(self, obj, val, *args, **kwargs):
        raise MissingContextError(context=obj.__context__.context,
                                  name=self.__name,
                                  type='setter')

    def __NO_DELETER(self, obj, *args, **kwargs):
        raise MissingContextError(context=obj.__context__.context,
                                  name=self.__name,
                                  type='deleter')

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name=None,
                 cache=False):
        self.__name = name
        self.__fget_contexts = {None: fget or self.__NO_GETTER}
        self.__fset_contexts = {None: fset or self.__NO_SETTER}
        self.__fdel_contexts = {None: fdel or self.__NO_DELETER}
        self.__doc__ = doc

        # caches initial getter if specified
        self.__cached = [None] if cache else []
        # mapping of setter/deleter functions to contexts they invalidate
        self.__invalidators = {}

        # replaces functions with wrappers that determine what actually gets
        # called based on the owning object's __context__
        super().__init__(
            fget=self.__fget,
            fset=self.__fset,
            fdel=self.__fdel,
            doc=doc
        )

    @staticmethod
    def get_cache_context(obj) ->  Tuple[Hashable, ContextualPropertyCache]:
        """Gets the cache and context; returns empty defaults if unavailable"""
        context = getattr(obj, '__context_mgr__', ObjectContextManager()).context
        cache = getattr(obj, '__context_cache__', ContextualPropertyCache())
        return context, cache

    def __fget(self, obj):
        """
        Grabs the correct getter function based on object context and returns
        the result of the getter
        :param obj: the object to retrieve data from
        :return: the context-dependent data
        """
        # if the context is not recognized, use None (default function)
        context, cache = self.get_cache_context(obj)
        fn = self.__fget_contexts.get(
            (getter_ctx := context if context in self.__fget_contexts.keys() else None))
        if getter_ctx in self.__cached:
            return cache.cache_execute(self.__name, getter_ctx, fn, obj)
        return fn(obj)

    def __fset(self, obj, val):
        """
        Sets the value of the given object to the given value using the
        appropriate function under the given context
        :param obj: object to modify
        :param val: incoming value to set
        """
        context, cache = self.get_cache_context(obj)
        fn = self.__fset_contexts.get(
            context if context in self.__fset_contexts.keys() else None)
        contexts = self.__invalidators[fn]
        return cache.invalidate_execute(self.__name, contexts, fn, obj, val)

    def __fdel(self, obj):
        """
        Deletes the property using the function appropriate under the given
        object's context
        :param obj: object to delete the property from
        """
        context, cache = self.get_cache_context(obj)
        fn = self.__fdel_contexts.get(
            context if context in self.__fdel_contexts.keys() else None)
        contexts = self.__invalidators[fn]
        return cache.invalidate_execute(self.__name, contexts, fn, obj)

    def setter(self, fset=None, invalidate: Tuple | List = None):
        """
        Changes the default setter function for the property. Should be used
        as a decorator
        :param fset: new default setter function
        :return:
        """
        def kwarg_fset(_fset):
            self.__fset_contexts[None] = _fset
            self.__invalidators[fset] = invalidate if invalidate else self.__cached
            return self

        if fset:
            self.__fset_contexts[None] = fset
            self.__invalidators[fset] = self.__cached
            return self
        return kwarg_fset

    def getter(self, fget, cache=False):
        """
        Changes the default getter function for the property. Should be used
        as a decorator
        :param fget: new default getter function
        :return:
        """

        def kwarg_fget(_fget):
            self.__fget_contexts[None] = _fget
            self.__cached += [None] if cache else []
            return self

        if fget:
            self.__fget_contexts[None] = fget
            return self
        return kwarg_fget

    def deleter(self, fdel, invalidate: Tuple | List = None):
        """
        Changes the default deleter function for the property. Should be used
        as a decorator
        :param fdel: new default deleter function
        :return:
        """
        def kwarg_fdel(_fdel):
            self.__fdel_contexts[None] = _fdel
            self.__invalidators[_fdel] = invalidate if invalidate else self.__cached
            return self

        if fdel:
            self.__fdel_contexts[None] = fdel
            self.__invalidators[fdel] = self.__cached
            return self
        return kwarg_fdel

    def setter_context(self, context, invalidate: Tuple | List = None):
        """
        Decorator for adding a context-dependent setter to the property. The
        function will be used when the __context__ attribute of the property
        matches the identifying value of the contextual function
        :param context: identifier for the contextual function
        """
        def decorator(fn):
            self.__fset_contexts[context] = fn
            self.__invalidators[fn] = invalidate if invalidate is not None else self.__cached
            return self
        return decorator

    def getter_context(self, context, cache=False):
        """
        Decorator for adding a context-dependent getter to the property. The
        function will be used when the __context__ attribute of the property
        matches the identifying value of the contextual function
        :param context: identifier for the contextual function
        """
        def decorator(fn):
            self.__fget_contexts[context] = fn
            self.__cached += [context] if cache else []
            return self
        return decorator

    def deleter_context(self, context, invalidate: Tuple | List = None):
        """
        Decorator for adding a context-dependent deleter to the property. The
        function will be used when the __context__ attribute of the property
        matches the identifying value of the contextual function
        :param context: identifier for the contextual function
        """
        def decorator(fn):
            self.__fdel_contexts[context] = fn
            self.__invalidators[fn] = invalidate if invalidate else self.__cached
            return self
        return decorator

    def __copy__(self):
        new_prop = ContextualProperty(doc=self.__doc__)
        new_prop.__fget_contexts = self.__fget_contexts.copy()
        new_prop.__fset_contexts = self.__fset_contexts.copy()
        new_prop.__fdel_contexts = self.__fdel_contexts.copy()
        new_prop.__invalidators = self.__invalidators.copy()
        new_prop.__cached = self.__cached.copy()
        return new_prop

    def __call__(self, *args, **kwargs):
        """"""
        print('test')


def contextualproperty(fn=None, cache=False) -> ContextualProperty:
    """
    Wrapper function that allows for @contextualproperty decorators
    without needlessly complex code in the actual object. The doc property will
    be derived from the docstring of the getter function.
    :param fn: getter function that serves as a starting point for the property
    :return: ContextualProperty with a getter and documentation, if provided
    """
    # there are ways to make this part of the class but I'm not doing it. I
    # have spent way too much time making this thing work and I am not about to
    # drive myself insane over this one design choice.

    def with_kwargs(next_fn):
        """"""
        return ContextualProperty(fget=next_fn, name=next_fn.__name__,
                                  doc=next_fn.__doc__, cache=cache)

    def without_kwargs():
        """"""
        return ContextualProperty(fget=fn, name=fn.__name__, doc=fn.__doc__)

    return with_kwargs if fn is None else without_kwargs()
