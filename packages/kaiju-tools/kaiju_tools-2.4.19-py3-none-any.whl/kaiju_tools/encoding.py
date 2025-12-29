"""Object serialization interfaces and classes."""

from enum import Enum

import msgspec


__all__ = [
    'MimeType',
    'dumps', 'loads',
    'msgpack_dumps', 'msgpack_loads',
    'yaml_dumps', 'yaml_loads',
    'ENCODERS'
]


class Serializable:
    """Class which supports serialization of its attributes."""

    serializable_attrs = None  #: Should be a frozenset or None. If None, then all will be used for serialization.
    include_null_values = True  #: include null values in a representation

    def repr(self) -> dict:
        """Must return a representation of object __init__ arguments."""
        _repr = {}
        if self.serializable_attrs is None:
            if hasattr(self, '__slots__'):
                for slot in self.__slots__:
                    if not slot.startswith('_') and hasattr(self, slot):
                        v = getattr(self, slot)
                        if not self.include_null_values and v is None:
                            continue
                        if isinstance(v, Serializable):
                            _repr[slot] = v.repr()
                        else:
                            _repr[slot] = v
            else:
                for k, v in self.__dict__.items():
                    if not self.include_null_values and v is None:
                        continue
                    if not k.startswith('_'):
                        if isinstance(v, Serializable):
                            _repr[k] = v.repr()
                        else:
                            _repr[k] = v
        else:
            if hasattr(self, '__slots__'):
                for slot in self.__slots__:
                    if slot in self.serializable_attrs and hasattr(self, slot):
                        v = getattr(self, slot)
                        if not self.include_null_values and v is None:
                            continue
                        if isinstance(v, Serializable):
                            _repr[slot] = v.repr()
                        else:
                            _repr[slot] = v
            else:
                for k, v in self.__dict__.items():
                    if not self.include_null_values and v is None:
                        continue
                    if k in self.serializable_attrs:
                        if isinstance(v, Serializable):
                            _repr[k] = v.repr()
                        else:
                            _repr[k] = v

        return _repr

    def __repr__(self):
        return f'<{self.__class__.__name__}(**{self.repr()})>'


class SerializedClass(Serializable):
    """Serialized class."""

    def repr(self) -> dict:
        return {'__cls': self.__class__.__name__, '__attrs': super().repr()}

    @classmethod
    def from_repr(cls, attrs: dict):
        return cls(**attrs)  # noqa


class MimeType(Enum):
    """Standard data types."""

    json = 'application/json'
    msgpack = 'application/msgpack'
    yaml = 'application/yaml'


_ExtType = msgspec.msgpack.Ext


def enc_hook_msgpack(obj):
    if isinstance(obj, Serializable):
        return obj.repr()
    raise NotImplementedError(f"Objects of type {obj} are not supported")


def enc_hook(obj):
    if isinstance(obj, Serializable):
        return obj.repr()
    raise NotImplementedError(f"Objects of type {obj} are not supported")


_json_encoder = msgspec.json.Encoder(enc_hook=enc_hook)
_json_decoder = msgspec.json.Decoder()
_msgpack_encoder = msgspec.msgpack.Encoder(enc_hook=enc_hook_msgpack)
_msgpack_decoder = msgspec.msgpack.Decoder()

dumps = _json_encoder.encode
loads = _json_decoder.decode
msgpack_dumps = _msgpack_encoder.encode
msgpack_loads = _msgpack_decoder.decode
yaml_dumps = msgspec.yaml.encode
yaml_loads = msgspec.yaml.decode

ENCODERS = {
    MimeType.json.value: (dumps, loads),
    MimeType.msgpack.value: (msgpack_dumps, msgpack_loads),
    MimeType.yaml.value: (yaml_dumps, yaml_loads),
}
