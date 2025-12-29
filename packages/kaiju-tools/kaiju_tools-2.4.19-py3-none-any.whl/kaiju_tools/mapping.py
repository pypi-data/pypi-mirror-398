from collections.abc import Collection, Iterable
from inspect import isclass
from itertools import zip_longest
from time import time
from types import GenericAlias
from typing import Any, TypeVar

from msgspec import Struct, defstruct


__all__ = [
    "get_field",
    "set_field",
    "recursive_update",
    "strip_fields",
    "filter_fields",
    "flatten",
    "unflatten",
    "struct_to_dict",
    "struct_to_tuple",
    "convert_struct_type",
    "DictCache",
]

_DictLike = TypeVar("_DictLike", tuple[dict], list[dict], dict)
_Struct = TypeVar("_Struct", bound=Struct)


class DictCache(dict):
    """Simple dict cache implementation.

    You can either set the default key ttl value in seconds using :py:attr:`~DictCache.default_ttl` property
    or set explicitly for each key by :py:meth:`~DictCache.set` method.

    You may set :py:attr:`~DictCache.max_keys` property to limit the max number of stored keys. When the cache key
    count reaches this number, it would randomly remove already stored keys while adding new ones.

    You may also set :py:attr:`~DictCache.eviction_threshold` to evict all expired keys periodically when any key
    is accessed. Basically it counts number of get and getitem operations and, once it reaches `eviction_threshold`
    limit, the :py:meth:`~DictCache.evict_expired` is triggered.

    >>> cache = DictCache()
    >>> cache['key'] = 'value'
    >>> 'key' in cache
    True
    >>> cache['key']
    'value'
    >>> list(cache)
    ['key']
    >>> list(cache.items())
    [('key', 'value')]
    >>> del cache['key']
    >>> list(cache)
    []
    >>> cache.set('key', 'value', ttl=10)
    >>> list(cache.values())
    ['value']
    >>> cache.get('key')
    'value'
    >>> cache.set('key', 'value', ttl=-10)
    >>> 'key' in cache
    False

    Using `eviction_threshold` to automatically trigger all expired eviction on certain number of key accesses:

    >>> cache.eviction_threshold = 1
    >>> cache.set('key1', 'value')
    >>> cache.set('key2', 'expired', ttl=-10)
    >>> cache.set('key3', 'value')
    >>> cache['key1']
    'value'
    >>> cache.get('key4')
    >>> repr(cache)
    "{'key1': ('value', None), 'key3': ('value', None)}"

    Using `max_keys` to limit the number of keys in the cache:

    >>> cache.max_keys = 1
    >>> cache['key1'] = 'value1'
    >>> cache['key2'] = 'value2'
    >>> list(cache.keys())
    ['key2']

    """

    __slots__ = ("_max_keys", "_default_ttl", "_eviction_count", "_eviction_threshold")

    def __init__(self, *args, **kws) -> None:
        super().__init__(*args, **kws)
        self._max_keys = None
        self._default_ttl = None
        self._eviction_count = None
        self._eviction_threshold = None

    def __setitem__(self, key, value, /) -> None:
        exp = int(time()) + self._default_ttl if self._default_ttl else None
        if self._max_keys and super().__len__() >= self._max_keys:
            super().popitem()
        super().__setitem__(key, (value, exp))

    def __getitem__(self, key, /):
        if self._eviction_threshold:
            if self._eviction_count >= self._eviction_threshold:
                self._eviction_count = 0
                self.evict_expired()
                return super().__getitem__(key)[0]
            else:
                self._eviction_count += 1
        value, exp = super().__getitem__(key)
        if exp and time() > exp:
            super().__delitem__(key)
            raise KeyError(key)
        return value

    def get(self, key, /, default=None):
        if self._eviction_threshold:
            if self._eviction_count >= self._eviction_threshold:
                self._eviction_count = 0
                self.evict_expired()
                _value = super().get(key)
                if not _value:
                    return default
                return _value[0]
            else:
                self._eviction_count += 1
        _value = super().get(key)
        if not _value:
            return default
        value, exp = _value
        if exp and time() > exp:
            super().__delitem__(key)
            return default
        return value

    def __contains__(self, key, /):
        _value = super().get(key)
        if not _value:
            return False
        value, exp = _value
        if exp and time() > exp:
            super().__delitem__(key)
            return False
        return True

    def items(self, /):
        t = int(time())
        return ((k, v) for k, (v, exp) in super().items() if not exp or exp > t)

    def values(self, /):
        t = int(time())
        return (v for (v, exp) in super().values() if not exp or exp > t)

    def set(self, key, value, /, ttl: int = None) -> None:
        if not ttl:
            ttl = self._default_ttl
        exp = int(time()) + ttl if ttl else None
        if self._max_keys and super().__len__() >= self._max_keys:
            super().popitem()
        super().__setitem__(key, (value, exp))

    def evict_expired(self):
        t = int(time())
        _to_remove = []
        for k, (v, exp) in super().items():
            if exp and t > exp:
                _to_remove.append(k)
        for k in _to_remove:
            super().__delitem__(k)

    @property
    def max_keys(self) -> int | None:
        return self._max_keys

    @max_keys.setter
    def max_keys(self, max_keys: int, /) -> None:
        self._max_keys = max_keys

    @property
    def default_ttl(self) -> int | None:
        return self._default_ttl

    @default_ttl.setter
    def default_ttl(self, default_ttl: int | None, /) -> None:
        self._default_ttl = default_ttl

    @property
    def eviction_threshold(self) -> int | None:
        return self._eviction_threshold

    @eviction_threshold.setter
    def eviction_threshold(self, eviction_threshold: int | None, /) -> None:
        self._eviction_threshold = eviction_threshold
        self._eviction_count = 0


def strip_fields(__obj: _DictLike, *, prefix: str = "_") -> _DictLike:
    """Strip fields starting with `prefix` from a dict or from a list of dicts.

    >>> strip_fields({'_meta': 123, 'name': 'bob'}, prefix='_')
    {'name': 'bob'}

    >>> strip_fields([{'a': 1, '.b': 2}, {'c': [{'.d': 4, 'e': 5}], '.b': 4}], prefix='.')
    [{'a': 1}, {'c': [{'e': 5}]}]

    """
    if isinstance(__obj, dict):
        new = {}
        for key, value in __obj.items():
            if not key.startswith(prefix):
                new[key] = strip_fields(value, prefix=prefix)
        return new
    elif isinstance(__obj, (list, tuple)):
        return type(__obj)(strip_fields(sub, prefix=prefix) for sub in __obj)
    else:
        return __obj


def flatten(__obj: _DictLike, *, delimiter: str = ".") -> _DictLike:
    """Flatten a nested dict or a list of nested dicts.

    >>> flatten({'a': {'b': {'c': 1, 'd': 2}}})
    {'a.b.c': 1, 'a.b.d': 2}

    >>> flatten([{'a': {'b': 1}}, {'a': {'b': [{'c': {'d': 1}}], 'e': 2}}])
    [{'a.b': 1}, {'a.b': [{'c.d': 1}], 'a.e': 2}]

    """
    if isinstance(__obj, dict):
        _data = {}
        for key, value in __obj.items():
            prefix = f"{key}{delimiter}"
            if isinstance(value, dict):
                value = flatten(value, delimiter=delimiter)
                for k, v in value.items():
                    k = f"{prefix}{k}"
                    _data[k] = v
            elif isinstance(value, Collection) and not isinstance(value, str):
                _data[key] = [flatten(sub, delimiter=delimiter) for sub in value]
            else:
                _data[key] = value
        return _data
    elif isinstance(__obj, (list, tuple)):
        return type(__obj)(flatten(sub, delimiter=delimiter) for sub in __obj)
    else:
        return __obj


def unflatten(__obj: _DictLike, *, delimiter: str = ".") -> _DictLike:
    """Unflatten a dict or a list of dicts into a nested structure.

    >>> unflatten({'a.b.c': True, 'a.c.d': False, 'e': True})
    {'a': {'b': {'c': True}, 'c': {'d': False}}, 'e': True}

    >>> unflatten([{'a.b.c': 1}, {'a.b.d': 2}])
    [{'a': {'b': {'c': 1}}}, {'a': {'b': {'d': 2}}}]

    """
    if isinstance(__obj, dict):
        _data: dict = {}
        for key, value in __obj.items():
            key = key.split(delimiter)
            _d = _data
            for k in key[:-1]:
                if k in _d:
                    _d = _d[k]
                else:
                    _new_d: dict = {}
                    _d[k] = _new_d
                    _d = _new_d
            _d[key[-1]] = value
        return _data
    elif isinstance(__obj, (list, tuple)):
        return type(__obj)(unflatten(sub, delimiter=delimiter) for sub in __obj)
    else:
        return __obj


def get_field(__obj: _DictLike, __key: str | list[str], *, default: Any = KeyError, delimiter: str = ".") -> Any:
    """Get a field from a nested dict using a flattened key.

    >>> get_field({'a': {'b': [1], 'c': 2}}, 'a.b')
    [1]

    using a custom delimiter:

    >>> get_field({'a': [{'b': 1}, {'b': 2}, {}]}, 'a-b', default=None, delimiter='-')
    [1, 2, None]

    aggregate from a list:

    >>> get_field([{'b': {'c': [{'d': 1}, {'d': 2}, {}]}}, {'b': 3}], 'b.c.d', default=None)
    [[1, 2, None], None]

    """
    # if type(obj) is dict and key in obj:
    #     return obj[key]

    if isinstance(__key, str):
        __key = __key.split(delimiter)

    for n, _key in enumerate(__key):
        if _key:
            if isinstance(__obj, dict):
                if _key in __obj:
                    __obj = __obj[_key]
                else:
                    if type(default) is type:
                        if issubclass(default, Exception):
                            raise default(__key)
                    return default
            elif isinstance(__obj, (list, tuple)):
                __obj = type(__obj)(
                    get_field(sub_obj, __key[n:], default=default, delimiter=delimiter) for sub_obj in __obj
                )
                return __obj
            else:
                return default

    return __obj


def set_field(__obj: dict, __key: str, value, *, delimiter: str = ".") -> None:
    """Set a field in a nested dict using a flattened key.

    >>> o = {'data': {}}
    >>> set_field(o, 'data.shite.name', True)
    >>> o
    {'data': {'shite': {'name': True}}}

    """
    __key = __key.split(delimiter)
    for _key in __key[:-1]:
        if _key not in __obj:
            __obj[_key] = {}
        __obj = __obj[_key]
    __obj[__key[-1]] = value


def recursive_update(__obj1: _DictLike, __obj2: tuple | list | dict) -> _DictLike:
    """Recursively update a dict from another dict.

    Note that it returns the updated object and not a new one.

    >>> recursive_update({'a': {'b': 1}}, {'a': {'c': 2}, 'd': 3})
    {'a': {'b': 1, 'c': 2}, 'd': 3}

    >>> recursive_update([{'a': {'b': 1}}, {'a': {'b': 1}}], [None, {'a': {'c': 2}, 'd': 3}])
    [{'a': {'b': 1}}, {'a': {'b': 1, 'c': 2}, 'd': 3}]

    """
    if isinstance(__obj1, dict):
        if isinstance(__obj2, dict):
            for key, value in __obj2.items():
                if key in __obj1:
                    __obj1[key] = recursive_update(__obj1[key], value)
                else:
                    __obj1[key] = value
        else:
            __obj1 = __obj2
    elif isinstance(__obj1, (list, tuple)):
        result = []
        if isinstance(__obj2, (list, tuple)):
            for o1, o2 in zip_longest(__obj1, __obj2):
                if o1 is not None:
                    if o2 is not None:
                        result.append(recursive_update(o1, o2))
                    else:
                        result.append(o1)
                else:
                    result.append(o2)
        __obj1 = type(__obj1)(result)
    else:
        __obj1 = __obj2
    return __obj1


def _filter_field(obj, keys, default):
    for n, key in enumerate(keys):
        if isinstance(obj, dict):
            return {key: _filter_field(obj.get(key, default), keys[n + 1 :], default)}  # noqa: linter?
        elif isinstance(obj, Collection) and not isinstance(obj, str):
            return [_filter_field(o, keys[n:], default) for o in obj]
    return obj


def filter_fields(__obj: dict, fields: Iterable[str], *, default=None, delimiter: str = ".") -> dict:
    """Filter dict keys using a specified set of flattened fields.

    >>> filter_fields({'a': {'b': 1, 'c': 2}}, fields=['a.b', 'a.d'])
    {'a': {'b': 1, 'd': None}}

    >>> filter_fields({'a': [{'b': 1, 'c': 2}, {'b': 2, 'c': 3}]}, fields=['a.b', 'a.g'], default=False)
    {'a': [{'b': 1, 'g': False}, {'b': 2, 'g': False}]}

    """
    result = {}
    for field in fields:
        result = recursive_update(result, _filter_field(__obj, field.split(delimiter), default))
    return result


def struct_to_tuple(struct: Struct) -> tuple:
    """Convert a struct object to a normal tuple.

    >>> class S(Struct):
    ...     name: str
    ...     value: int = 0
    >>> struct_to_tuple(S(name='test', value=11))
    ('test', 11)

    """
    data = []
    for key in struct.__struct_fields__:
        value = getattr(struct, key, None)
        if isinstance(value, Struct):
            value = struct_to_dict(value)
        data.append(value)
    return tuple(data)


def struct_to_dict(struct: Struct) -> dict[str, Any]:
    """Convert a struct object to a normal dictionary.

    >>> class S(Struct):
    ...     name: str
    ...     value: int = 0
    >>> struct_to_dict(S(name='test', value=11))
    {'name': 'test', 'value': 11}

    """
    data = {}
    for key in struct.__struct_fields__:
        value = getattr(struct, key, None)
        if isinstance(value, Struct):
            value = struct_to_dict(value)
        data[key] = value
    return data


def convert_struct_type(struct: type[_Struct], recursive: bool = False, **struct_attrs) -> type[_Struct]:
    """Convert between `msgspec` struct types.

    :param struct: Struct type to convert from
    :param recursive: recursively convert struct types inside this type
    :param struct_attrs: struct configuration attributes

    This method allows to dynamically create new struct type with the same interface but with different configuration.

    >>> class S(Struct):
    ...     name: str
    ...     value: int = 0
    >>> NewType = convert_struct_type(S, array_like=True)
    >>> NewType.__struct_config__.array_like
    True
    >>> obj = NewType(name='Test')
    >>> obj.name
    'Test'
    >>> obj.value
    0

    """
    struct_fields = []
    struct_defaults = getattr(struct, "__struct_defaults__", tuple())
    struct_config = getattr(struct, "__struct_config__", struct_defaults)
    for (attr, typ), value in zip_longest(
        reversed(struct.__annotations__.items()), reversed(struct_defaults), fillvalue=...
    ):
        if recursive:
            if type(typ) is GenericAlias:
                if typ.__origin__ in {list, set, frozenset}:
                    typ = typ.__origin__[convert_struct_type(typ.__args__[0], recursive=True, **struct_attrs)]
            elif isclass(typ) and issubclass(typ, Struct):
                typ = convert_struct_type(typ, recursive=True, **struct_attrs)
        if value is ...:
            struct_fields.insert(0, (attr, typ))
        else:
            struct_fields.insert(0, (attr, typ, value))

    params = {k: getattr(struct_config, k, None) for k in dir(struct_config) if not k.startswith("_")}
    params.update(struct_attrs)
    new_struct = defstruct(f"{struct.__name__}Array", fields=struct_fields, **params)
    return new_struct
