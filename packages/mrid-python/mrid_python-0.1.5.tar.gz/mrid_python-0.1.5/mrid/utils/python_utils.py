import importlib.util
from collections.abc import Mapping, Sequence
from typing import Any


# lazy loader from https://stackoverflow.com/a/78312674/15673832
class LazyLoader:
    'thin shell class to wrap modules.  load real module on first access and pass thru'

    def __init__(self, modname):
        self._modname = modname
        self._mod = None

    def __getattr__(self, attr):
        'import module on first attribute access'

        try:
            return getattr(self._mod, attr)

        except Exception as e :
            if self._mod is None :
                # module is unset, load it
                self._mod = importlib.import_module (self._modname)
            else :
                # module is set, got different exception from getattr ().  reraise it
                raise e

        # retry getattr if module was just loaded for first time
        # call this outside exception handler in case it raises new exception
        return getattr (self._mod, attr)


# this allows transforms to support any kind of container
# class _Packer[T: Sequence | Mapping]:
#     def __init__(self, type: type[T], keys: list | None = None):
#         self.type: Any = type
#         self.keys = keys

#     def pack(self, unpacked: Sequence) -> T:
#         if self.keys is not None: return self.type(dict(zip(self.keys, unpacked)))
#         return self.type(unpacked)

# def unpack_struct[T: Sequence | Mapping](struct: T) -> tuple[Any, _Packer[T]]:
#     if isinstance(struct, Sequence):
#         return list(struct), _Packer(type(struct))
#     if isinstance(struct, Mapping):
#         return list(struct.values()), _Packer(type(struct), list(struct.values()))
#     raise TypeError(f"Transformation functions accept lists and dictionaries, but received {type(struct)}")
