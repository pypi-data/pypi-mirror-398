"""Class and object registries."""

import abc
import inspect
from collections.abc import Callable, Collection, Generator, Hashable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, TypeVar


__all__ = ['RegistryError', 'RegistrationFailed', 'Registry', 'ClassRegistry', 'ObjectRegistry', 'FunctionRegistry']

_Key = TypeVar('_Key', bound=Hashable)
_Obj = TypeVar('_Obj')
_Default = TypeVar('_Default')


class RegistryError(Exception):
    """A base class for all registry errors."""


class RegistrationFailed(ValueError, RegistryError):
    """Object cannot be registered in this registry."""


@dataclass
class Registry(Mapping, Generic[_Key, _Obj], abc.ABC):
    """Base registry."""

    objects: dict = field(default_factory=dict)
    raise_if_exists: bool = False

    def can_register(self, obj, /) -> bool:
        """Check if an object can be registered."""
        try:
            self._validate_object(obj)
        except RegistrationFailed:
            return False
        else:
            return True

    def register(self, obj: _Obj, /, name: _Key = None) -> _Key:
        """Register an object in the registry and return a key under which it has been registered.

        :param obj: object to register
        :param name: provide a custom name (not recommended)
        :raises RegistrationFailed: if an object can't be registered
        :returns: object key in the registry
        """
        key = self._validate_object(obj)
        if name:
            key = name
        self.objects[key] = obj
        return key

    def register_many(self, obj: Collection[_Obj], /) -> tuple[_Key, ...]:
        """Register multiple objects at once.

        :param obj: objects
        :raises RegistrationFailed: if any of the objects can't be registered
        :returns: a tuple of object keys
        """
        return tuple(self.register(item) for item in obj)

    def get_key(self, obj: _Obj) -> _Key:
        """Get a key by which an object will be referenced in the registry."""
        raise NotImplementedError()

    def register_from_namespace(
        self, namespace: Mapping[_Key, _Obj], *, use_key_names: bool = False
    ) -> frozenset[_Key]:
        """Register all supported objects from an arbitrary mapping.

        Incompatible objects will be ignored. Returns a set of registered keys.

        :param namespace: any mapping
        :param use_key_names: use namespace key names instead of a registry name function
        :returns: a set of registered keys
        """
        keys = set()
        for key, obj in namespace.items():
            if not use_key_names:
                key = None
            try:
                key = self.register(obj, name=key)
            except RegistrationFailed:
                pass
            else:
                keys.add(key)
        return frozenset(keys)

    def register_from_module(self, module: object, *, use_key_names: bool = False) -> frozenset[_Key]:
        """Register classes from current object.

        :param module: any object with `__dict__`
        :param use_key_names: use namespace key names instead of a registry name function
        :returns: a set of registered keys
        """
        return self.register_from_namespace(module.__dict__, use_key_names=use_key_names)

    def find_all(self, condition: Callable[[Any], bool]) -> Generator[_Obj, None, None]:
        """Find all objects matching a condition."""
        for value in self.objects.values():
            if condition(value):
                yield value

    def find(self, condition: Callable[[Any], bool]) -> _Obj:
        """Find an object matching a condition."""
        return next(self.find_all(condition), None)

    def clear(self) -> None:
        """Unlink all registered objects. Use it with caution."""
        self.objects.clear()

    def __enter__(self):
        """Enter the context."""

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear all registered objects on exit."""
        self.clear()

    def __contains__(self, item: _Key) -> bool:
        return item in self.objects

    def __getitem__(self, item: _Key) -> _Obj:
        return self.objects[item]

    def __delitem__(self, item: _Key) -> None:
        del self.objects[item]

    def __iter__(self) -> Iterable[_Key]:
        return iter(self.objects.keys())

    def __len__(self) -> int:
        return len(self.objects)

    def get(self, key: _Key, default: _Default = None) -> _Obj | _Default:
        try:
            return self[key]
        except KeyError:
            return default

    def _validate_object(self, obj) -> _Key:
        """Validate object before registration."""
        key = self.get_key(obj)
        if key in self.objects and self.raise_if_exists:
            raise RegistrationFailed(f'Object with the same name already present: {key}')
        return key


@dataclass
class ClassRegistry(Registry, Generic[_Key, _Obj], abc.ABC):
    """A default registry for classes.

    It can be used to register a set of classes for dynamic object initialization
    based on class names or other parameters.

    To create your own registry you need to define :py:meth:`~kaiju_tools.registry.ClassRegistry.get_base_classes`
    method returning a tuple of base classesd. All newly registered classes then must be a subclass of these bases.
    Additionaly you may want to configure at which keys your classes will be stored by changing
    :py:meth:`~kaiju_tools.registry.ClassRegistry.get_key` method. It uses `__name__` of a class by default.

    It's also a nice idea to provide a generic type hint for your registry key and item types in square brackets.

    >>> class BaseC(abc.ABC):
    ...     name: str
    ...     value: int

    >>> class Classes(ClassRegistry[str, type[BaseC]]):
    ...     @classmethod
    ...     def get_base_classes(cls):
    ...         return (BaseC,)
    ...
    ...     def get_key(self, obj: type[BaseC]) -> str:
    ...         return obj.name  # not required, the registry uses `__name__` by default

    When you have your registry configured, you can initialize a registry object and start adding your classes!
    There are a few methods such as :py:meth:`~kaiju_tools.registry.ClassRegistry.register`,
    :py:meth:`~kaiju_tools.registry.ClassRegistry.register_from_module` and
    :py:meth:`~kaiju_tools.registry.ClassRegistry.register_from_namespace` to help you with registering classes.

    >>> reg = Classes()

    >>> class C(BaseC):
    ...     name = 'my_class'
    ...     value = 1

    >>> reg.register(C)
    'my_class'

    >>> reg.register_from_namespace({'other_class': C}, use_key_names=True)
    frozenset({'other_class'})

    You can access registered classes by their keys or search for them using
    :py:meth:`~kaiju_tools.registry.ClassRegistry.find` and :py:meth:`~kaiju_tools.registry.ClassRegistry.find_all`
    methods.

    >>> reg['my_class'].value
    1

    >>> reg.find(condition=lambda o: o.value > 0).__name__
    'C'

    You can also find subclasses of a spacific class(es) using
    :py:meth:`~kaiju_tools.registry.ClassRegistry.find_subclass` and
    :py:meth:`~kaiju_tools.registry.ClassRegistry.find_subclasses` special methods.

    >>> reg.find_subclass(BaseC).__name__
    'C'

    """

    allow_abstract: ClassVar[bool] = False

    @classmethod
    @abc.abstractmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        ...

    def find_subclasses(self, *bases: Collection[_Obj] | _Obj) -> Generator[_Obj, None, None]:
        """Find all subclasses matching bases. A shortcut to `find_all` method."""
        return self.find_all(condition=lambda x: issubclass(x, bases))

    def find_subclass(self, *bases: Collection[_Obj] | _Obj) -> _Obj:
        """Find a first subclass matching bases. A shortcut to `find` method."""
        return next(self.find_subclasses(*bases), None)

    def get_key(self, obj: _Obj) -> _Key:
        """Get a class name."""
        return getattr(obj, '__name__', str(obj))

    def _validate_object(self, obj) -> _Key:
        if not inspect.isclass(obj):
            raise RegistrationFailed(f'Can\'t register object {obj} because it\'s not a class.')
        elif not self.allow_abstract and (inspect.isabstract(obj) or abc.ABC in obj.__bases__):
            raise RegistrationFailed(f'Can\'t register object {obj} because it\'s an abstract class.')
        elif not issubclass(obj, self.get_base_classes()):
            raise RegistrationFailed(
                f'Can\'t register object {obj} because it\'s not a subclass'
                f' of any of the base classes {self.get_base_classes()}'
            )
        key = Registry._validate_object(self, obj)
        return key


@dataclass
class ObjectRegistry(Registry, Generic[_Key, _Obj], abc.ABC):
    """Python objects registry.

    It can be used to store specific objects in a single mapping (for example for storing
    application services in a single service registry).

    >>> class BaseC(abc.ABC):
    ...     name: str
    ...
    ...     @staticmethod
    ...     def get_value(): return 1
    ...
    ...     def __repr__(self): return f'<[{self.name}]>'

    The initialization process and overall workflow is similar to :py:class:`~kaiju_tools.registry.ClassRegistry`
    with the only difference being that it stores objects instead of classes.

    >>> class Objects(ObjectRegistry[str, BaseC]):
    ...
    ...     @classmethod
    ...     def get_base_classes(cls):
    ...         return (BaseC,)
    ...
    ...     def get_key(self, obj: BaseC) -> str:
    ...         return obj.name  # not necessary, the registry uses `__name__` by default

    >>> reg = Objects()

    You can register objects and dynamically access them by their identifiers.

    >>> class C(BaseC):
    ...     name = 'C_name'
    >>> reg.register(C())
    'C_name'

    >>> reg['C_name'].get_value()
    1

    You can register objects from a namespace (any dictionary) using either the registry name function
    or names used in this dictionary (see :py:class:`~kaiju_tools.registry.Registry.register_from_namespace`).

    >>> reg.register_from_namespace({'Other_name': C()}, use_key_names=True)
    frozenset({'Other_name'})

    Standard mapping methods also work for registry classes.

    >>> 'Other_name' in reg
    True

    >>> del reg['Other_name']

    You can also find instances of a class(es) using
    :py:meth:`~kaiju_tools.registry.ObjectRegistry.find_instance` and
    :py:meth:`~kaiju_tools.registry.ObjectRegistry.find_instances` special methods.

    >>> reg.find_instance(BaseC)
    <[C_name]>

    """

    @classmethod
    @abc.abstractmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        ...

    def find_instances(self, *bases: Collection[type[_Obj]] | type[_Obj]) -> Generator[_Obj, None, None]:
        """Find all subclasses matching bases. A shortcut to `find_all` method."""
        return self.find_all(condition=lambda x: isinstance(x, bases))

    def find_instance(self, *bases: Collection[type[_Obj]] | type[_Obj]) -> _Obj | None:
        """Find a first subclass matching bases. A shortcut to `find` method."""
        return next(self.find_instances(*bases), None)

    def get_key(self, obj: _Obj) -> _Key:
        """Get a name by which a registered class will be referenced in the mapping."""
        return getattr(type(obj), '__name__', str(type(obj)))

    def _validate_object(self, obj) -> _Key:
        key = Registry._validate_object(self, obj)
        if not isinstance(obj, self.get_base_classes()):
            raise RegistrationFailed(
                f'Can\'t register object {obj} because it\'s not an instance'
                f' of any of the base classes {self.get_base_classes()}'
            )
        return key


@dataclass
class FunctionRegistry(Registry[str, Callable]):
    """A very simple function registry.

    You can use it to store and dynamically access functions by their identifiers.

    >>> reg = FunctionRegistry()
    >>> def inc_2(x: int): return x * 2
    >>> reg.register(inc_2)
    'inc_2'

    >>> reg['inc_2'](1)
    2

    """

    def call(self, name: _Key, *args, **kws):
        """Call a stored function with arguments."""
        return self[name](*args, **kws)

    def get_key(self, obj: Callable) -> _Key:
        """Get a name by which a registered class will be referenced in the mapping."""
        return obj.__name__

    def _validate_object(self, obj) -> _Key:
        key = Registry._validate_object(self, obj)
        if not callable(obj):
            raise RegistrationFailed(f'Can\'t register object {obj} because it\'s not a function.')
        return key
