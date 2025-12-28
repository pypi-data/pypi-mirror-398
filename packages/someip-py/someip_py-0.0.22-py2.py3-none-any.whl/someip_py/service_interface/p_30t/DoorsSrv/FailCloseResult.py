from someip_py.codec import *


class IdtSingleDoorFailCloseResult(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    Boolean: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.Boolean = Uint8()


class IdtFailCloseResult(SomeIpPayload):

    IdtFailCloseResult: SomeIpDynamicSizeArray[IdtSingleDoorFailCloseResult]

    def __init__(self):

        self.IdtFailCloseResult = SomeIpDynamicSizeArray(IdtSingleDoorFailCloseResult)
