import struct

from . import DeviceField, FieldName


class IntField(DeviceField):
    def __init__(
        self,
        name: FieldName,
        address: int,
        min: int | None = None,
        max: int | None = None,
    ):
        super().__init__(name, address, 1)
        self.min = min
        self.max = max

    def parse(self, data: bytes) -> int:
        return struct.unpack(">h", data)[0]

    def in_range(self, value: int) -> bool:
        if self.min is not None and self.min > value:
            return False
        if self.max is not None and self.max < value:
            return False
        return True
