from someip_py.codec import *


class IdtDoorHoverStatus(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorStatus: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorStatus = Uint8()


class IdtDoorsHoverStatus(SomeIpPayload):

    IdtDoorsHoverStatus: SomeIpDynamicSizeArray[IdtDoorHoverStatus]

    def __init__(self):

        self.IdtDoorsHoverStatus = SomeIpDynamicSizeArray(IdtDoorHoverStatus)
