from someip_py.codec import *


class IdtSingleDoorPosnProgmSts(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorPosnProgmSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorPosnProgmSts = Uint8()


class IdtDoorsPosnProgmSts(SomeIpPayload):

    IdtDoorsPosnProgmSts: SomeIpDynamicSizeArray[IdtSingleDoorPosnProgmSts]

    def __init__(self):

        self.IdtDoorsPosnProgmSts = SomeIpDynamicSizeArray(IdtSingleDoorPosnProgmSts)
