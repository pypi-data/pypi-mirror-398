from someip_py.codec import *


class IdtSingleDoorOpenIntExtTrg(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorOpenIntExtTrg: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorOpenIntExtTrg = Uint8()


class IdtDoorsOpenIntExtTrg(SomeIpPayload):

    IdtDoorsOpenIntExtTrg: SomeIpDynamicSizeArray[IdtSingleDoorOpenIntExtTrg]

    def __init__(self):

        self.IdtDoorsOpenIntExtTrg = SomeIpDynamicSizeArray(IdtSingleDoorOpenIntExtTrg)
