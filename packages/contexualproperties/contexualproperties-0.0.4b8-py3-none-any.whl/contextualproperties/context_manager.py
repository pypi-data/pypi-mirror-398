from copy import copy
from typing import Hashable, List, Tuple


class JsonContextAwareManager:
    """
    Class for managing the context in which a @property is being modified or
    retrieved
    """

    def __init__(self):
        self._stack = list()
        self.context = None
        self.active = False

    def __call__(self, context=None, *args, **kwargs):
        self._stack.append(self.context)
        self.context = context
        return self

    def __enter__(self):
        self.active = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context = None if not self._stack else self._stack.pop()
        self.active = len(self._stack) > 0


GLOBAL_CONTEXT_MANAGER: 'ObjectContextManager' = None


class ObjectContextManager:
    @property
    def context(self) -> Hashable:
        return None if not self.active else self.context_stack[-1]

    @property
    def context_stack(self) -> Tuple[Hashable]:
        if not getattr(self, '__ContextManager_stack', None):
            setattr(self, '__ContextManager_stack', tuple())
        return getattr(self, '__ContextManager_stack')

    @property
    def active(self) -> bool:
        return len(self.context_stack) > 0

    def __call__(self, context=None):
        """
        Returns the current context, adding a new one if provided
        :param context: new context to provide
        :return: current context
        """
        if context:
            self.push(context)
        return self.context

    def push(self, context: Hashable) -> Hashable:
        setattr(self, '__ContextManager_stack', self.context_stack + (context,))
        return self.context

    def pop(self) -> Hashable:
        previous_context = self.context
        if self.active:
            setattr(self, '__ContextManager_stack', self.context_stack[:-1])
        return previous_context

    def __add__(self, new_context: Hashable) -> 'ObjectContextManager':
        self.push(new_context)
        return self

    def __iadd__(self, new_context: Hashable) -> 'ObjectContextManager':
        self.push(new_context)
        return self

    def __invert__(self):
        self.pop()
        return self

    def __enter__(self) -> 'ObjectContextManager':
        setattr(self, '__starting_context_stack', copy(self.context_stack))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        setattr(self, '__ContextManager_stack',
                getattr(self, '__starting_context_stack', []))
        delattr(self, '__starting_context_stack')


GLOBAL_CONTEXT_MANAGER = ObjectContextManager()