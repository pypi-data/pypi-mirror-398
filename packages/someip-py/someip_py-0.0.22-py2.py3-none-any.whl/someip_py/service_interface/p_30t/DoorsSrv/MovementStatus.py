from someip_py.codec import *


class IdtSingleDoorMovementStatus(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorMovementStatus: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorMovementStatus = Uint8()


class IdtDoorsMovementStatus(SomeIpPayload):

    IdtDoorsMovementStatus: SomeIpDynamicSizeArray[IdtSingleDoorMovementStatus]

    def __init__(self):

        self.IdtDoorsMovementStatus = SomeIpDynamicSizeArray(
            IdtSingleDoorMovementStatus
        )
