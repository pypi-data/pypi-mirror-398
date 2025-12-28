from someip_py.codec import *


class IdtADFaultsField(SomeIpPayload):

    _include_struct_len = True

    Key: Uint16

    Value: Int32

    def __init__(self):

        self.Key = Uint16()

        self.Value = Int32()


class IdtADFaultsFields(SomeIpPayload):

    IdtADFaultsFields: SomeIpDynamicSizeArray[IdtADFaultsField]

    def __init__(self):

        self.IdtADFaultsFields = SomeIpDynamicSizeArray(IdtADFaultsField)
