import struct
from enum import Enum
from typing import Any, Type, TypeVar

from . import DeviceField, FieldName


E = TypeVar("E", bound=Enum)


class SelectField(DeviceField):
    def __init__(self, name: FieldName, address: int, e: Type[E]):
        super().__init__(name, address, 1)
        self.e = e

    def parse(self, data: bytes) -> E | None:
        val = struct.unpack("!H", data)[0]
        return self.e(val)

    def is_writeable(self):
        return True

    def allowed_write_type(self, value: Any) -> bool:
        return isinstance(value, Type[Enum])
