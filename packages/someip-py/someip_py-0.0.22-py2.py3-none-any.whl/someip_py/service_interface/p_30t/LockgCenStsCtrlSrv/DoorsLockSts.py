from someip_py.codec import *


class IdtSingleDoorLockSts(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorLockSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorLockSts = Uint8()


class IdtDoorsLockSts(SomeIpPayload):

    IdtDoorsLockSts: SomeIpDynamicSizeArray[IdtSingleDoorLockSts]

    def __init__(self):

        self.IdtDoorsLockSts = SomeIpDynamicSizeArray(IdtSingleDoorLockSts)
