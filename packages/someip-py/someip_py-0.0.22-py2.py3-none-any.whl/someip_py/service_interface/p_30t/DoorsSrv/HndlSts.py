from someip_py.codec import *


class IdtSingleDoorHndlSts(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorHndlSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorHndlSts = Uint8()


class IdtDoorsHndlSts(SomeIpPayload):

    IdtDoorsHndlSts: SomeIpDynamicSizeArray[IdtSingleDoorHndlSts]

    def __init__(self):

        self.IdtDoorsHndlSts = SomeIpDynamicSizeArray(IdtSingleDoorHndlSts)
