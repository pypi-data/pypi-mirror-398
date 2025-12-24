from itertools import chain


class PropertyAwareObject:
    """
    Base object that provides tools for working with object properties.
    Provides a __get_properties__ method to produce a tuple for classes and a
    __properties__ variable to instances of inheriting classes
    """

    def __init__(self):
        self.__properties__ = self.__get_properties__()

    def __iter__(self):
        for prop in self.__properties__:
            yield prop, getattr(self, prop)

    def __getitem__(self, keys):
        keys = [keys] if isinstance(keys, str) else keys
        if any(key not in self.__properties__ for key in keys):
            bad_keys = [key for key in keys if key not in self.__properties__]
            raise KeyError(f'''Key{'s' if len(bad_keys) > 1 else ''} ''' +
                           f'''('{"', '".join(bad_keys)}') ''' +
                           f'''not in type '{self.__class__.__name__}\'''')
        return {key: getattr(self, key) for key in keys}

    @classmethod
    def __get_properties__(cls, refresh=False):
        """
        Creates a list of all @property objects defined and inherited in
        this class
        """
        if not hasattr(cls, '__properties__') or refresh:
            # we cache a copy
            cls.__properties__ = tuple(set(chain(key for kls in cls.mro()
                                             for key, value in
                                             kls.__dict__.items()
                                             if isinstance(value, property))))
        return cls.__properties__

    def switch_context(self, context):
        self.__context_mgr__(context)
        return self.__context__