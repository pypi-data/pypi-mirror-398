from someip_py.codec import *


class IdtPrkgField(SomeIpPayload):

    _include_struct_len = True

    Key: Uint16

    Value: Int32

    def __init__(self):

        self.Key = Uint16()

        self.Value = Int32()


class IdtPrkgFields(SomeIpPayload):

    IdtPrkgFields: SomeIpDynamicSizeArray[IdtPrkgField]

    def __init__(self):

        self.IdtPrkgFields = SomeIpDynamicSizeArray(IdtPrkgField)
