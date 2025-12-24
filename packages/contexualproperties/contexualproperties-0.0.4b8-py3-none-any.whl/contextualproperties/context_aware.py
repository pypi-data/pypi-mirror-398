from contextualproperties.context_manager import ObjectContextManager
from contextualproperties.context_cached import ContextCacheObject

class ContextAwareObject(ContextCacheObject):
    """
    Base object that provides tools for making an object aware of the context
    in which it is being used.

    Provides a ``__context_mgr__`` attribute that provides a context manager as
    well as the ability to use the ``<<`` operator to apply a context,
    the ``~`` operator to remove a context

    Also provides context manager (``with`` statement) support that reverts
    to the original context when the statement exits
    """

    def __init__(self):
        ContextCacheObject.__init__(self)
        self.__context_mgr__ = ObjectContextManager()

    def __lshift__(self, obj):
        self.__context_mgr__.push(obj)
        return self

    def __invert__(self):
        self.__context_mgr__.pop()
        return self

    def __enter__(self):
        return self.__context_mgr__.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__context_mgr__.__exit__(exc_type, exc_val, exc_tb)