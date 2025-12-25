class _CachedAccessor:
    """from xarray: Custom property-like object (descriptor) for caching accessors."""

    def __init__(self, name, accessor):
        self._name = name
        self._accessor = accessor

    def __get__(self, obj, cls):
        if obj is None:
            # we're accessing the attribute of the class, i.e., Dataset.geo
            return self._accessor

        # Use the same dict as @pandas.util.cache_readonly.
        # It must be explicitly declared in obj.__slots__.
        try:
            cache = obj._cache
        except AttributeError:
            cache = obj._cache = {}

        try:
            return cache[self._name]
        except KeyError:
            pass

        try:
            accessor_obj = self._accessor(obj)
        except AttributeError as err:
            # __getattr__ on data object will swallow any AttributeErrors
            # raised when initializing the accessor, so we need to raise as
            # something else (GH933):
            msg = f"error initializing {self._name!r} accessor."
            raise RuntimeError(msg) from err

        cache[self._name] = accessor_obj
        return accessor_obj


def register_accessor(cls, accessor, name):
    """
    Register an accessor for a class.

    Args:
        cls: The class to register the accessor to.
        accessor: The accessor class.
        name: The attribute name the accessor will be available under.


    """

    setattr(cls, name, _CachedAccessor(name, accessor))



