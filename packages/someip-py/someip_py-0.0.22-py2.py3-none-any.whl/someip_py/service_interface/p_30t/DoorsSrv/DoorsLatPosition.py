from someip_py.codec import *


class IdtSingleDoorLatPosition(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorLatPosition: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorLatPosition = Uint8()


class IdtDoorsLatPosition(SomeIpPayload):

    IdtDoorsLatPosition: SomeIpDynamicSizeArray[IdtSingleDoorLatPosition]

    def __init__(self):

        self.IdtDoorsLatPosition = SomeIpDynamicSizeArray(IdtSingleDoorLatPosition)
