from ..base_devices import BaseDeviceV2
from ..fields import FieldName, UIntField


class AP300(BaseDeviceV2):
    def __init__(self):
        super().__init__(
            [
                UIntField(FieldName.AC_OUTPUT_POWER, 142),
                UIntField(FieldName.DC_INPUT_POWER, 144),
                UIntField(FieldName.AC_INPUT_POWER, 146),
                UIntField(FieldName.AC_INPUT_VOLTAGE, 1314, 0.1),
            ],
        )
