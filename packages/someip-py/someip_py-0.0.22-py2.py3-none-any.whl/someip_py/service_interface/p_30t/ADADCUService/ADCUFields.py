from someip_py.codec import *


class IdtADCUField(SomeIpPayload):

    _include_struct_len = True

    Key: Uint16

    Value: Int32

    def __init__(self):

        self.Key = Uint16()

        self.Value = Int32()


class IdtADCUFields(SomeIpPayload):

    IdtADCUFields: SomeIpDynamicSizeArray[IdtADCUField]

    def __init__(self):

        self.IdtADCUFields = SomeIpDynamicSizeArray(IdtADCUField)
