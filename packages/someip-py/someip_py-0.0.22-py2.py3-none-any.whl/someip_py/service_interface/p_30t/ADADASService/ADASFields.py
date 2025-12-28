from someip_py.codec import *


class IdtADASField(SomeIpPayload):

    _include_struct_len = True

    Key: Uint16

    Value: Int32

    def __init__(self):

        self.Key = Uint16()

        self.Value = Int32()


class IdtADASFields(SomeIpPayload):

    IdtADASFields: SomeIpDynamicSizeArray[IdtADASField]

    def __init__(self):

        self.IdtADASFields = SomeIpDynamicSizeArray(IdtADASField)
