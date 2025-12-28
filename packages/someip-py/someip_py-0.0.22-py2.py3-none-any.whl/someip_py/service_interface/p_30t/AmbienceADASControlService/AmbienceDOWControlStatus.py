from someip_py.codec import *


class IdtAmbienceDOWControl(SomeIpPayload):

    _include_struct_len = True

    DOWDoorType: Uint8

    DOWDoorControl: Uint8

    def __init__(self):

        self.DOWDoorType = Uint8()

        self.DOWDoorControl = Uint8()


class IdtAmbienceDOWControlArry(SomeIpPayload):

    IdtAmbienceDOWControlArry: SomeIpDynamicSizeArray[IdtAmbienceDOWControl]

    def __init__(self):

        self.IdtAmbienceDOWControlArry = SomeIpDynamicSizeArray(IdtAmbienceDOWControl)
