from someip_py.codec import *


class IdtSingleDoorSts(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorSts = Uint8()


class IdtDoorsSts(SomeIpPayload):

    IdtDoorsSts: SomeIpDynamicSizeArray[IdtSingleDoorSts]

    def __init__(self):

        self.IdtDoorsSts = SomeIpDynamicSizeArray(IdtSingleDoorSts)
