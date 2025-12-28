from someip_py.codec import *


class IdtADDrivingField(SomeIpPayload):

    _include_struct_len = True

    Key: Uint16

    Value: Int32

    def __init__(self):

        self.Key = Uint16()

        self.Value = Int32()


class IdtADDrivingFields(SomeIpPayload):

    IdtADDrivingFields: SomeIpDynamicSizeArray[IdtADDrivingField]

    def __init__(self):

        self.IdtADDrivingFields = SomeIpDynamicSizeArray(IdtADDrivingField)
