from someip_py.codec import *


class IdtSingleDoorSts_Sfty(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorSts_Sfty: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorSts_Sfty = Uint8()


class IdtDoorsSts_Sfty(SomeIpPayload):

    IdtDoorsSts_Sfty: SomeIpDynamicSizeArray[IdtSingleDoorSts_Sfty]

    def __init__(self):

        self.IdtDoorsSts_Sfty = SomeIpDynamicSizeArray(IdtSingleDoorSts_Sfty)
