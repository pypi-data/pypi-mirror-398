import abc
from typing import Tuple, Type

import pytest  # noqa: pycharm

from kaiju_tools.registry import ClassRegistry, RegistryError


def test_class_manager():
    class Base:
        pass

    class Registry(ClassRegistry):
        @classmethod
        def get_base_classes(cls) -> Tuple[Type, ...]:
            return (Base,)

    class Class1(Base):
        pass

    class Class2(Base, abc.ABC):
        pass

    class Class3:
        pass

    registry = Registry(raise_if_exists=True)
    registry.register(Class1)

    # should raise on duplicate class
    with pytest.raises(RegistryError):
        registry.register(Class1)

    # should raise on abstract class
    with pytest.raises(RegistryError):
        registry.register(Class2)
    assert registry.can_register(Class2) is False

    # should raise on wrong bases class
    with pytest.raises(RegistryError):
        registry.register(Class3)
    assert registry.can_register(Class3) is False

    # access registered classes
    assert registry['Class1'] is Class1
    assert 'Class1' in registry
    for cls in registry:
        assert issubclass(registry[cls], Base)

    # check namespace registration
    registry = Registry()
    registry.register_from_namespace(locals())
    assert registry['Class1'] is Class1

    # test dictionary handling
    namespace = dict(registry)
    assert 'Class1' in namespace
