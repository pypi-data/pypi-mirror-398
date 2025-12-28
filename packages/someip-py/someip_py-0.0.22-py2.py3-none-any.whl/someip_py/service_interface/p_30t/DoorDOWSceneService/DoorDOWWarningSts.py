from someip_py.codec import *


class IdtDoorDOWWarning(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorDOWWaringSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorDOWWaringSts = Uint8()


class IdtDoorDOWWarningArry(SomeIpPayload):

    IdtDoorDOWWarningArry: SomeIpDynamicSizeArray[IdtDoorDOWWarning]

    def __init__(self):

        self.IdtDoorDOWWarningArry = SomeIpDynamicSizeArray(IdtDoorDOWWarning)
