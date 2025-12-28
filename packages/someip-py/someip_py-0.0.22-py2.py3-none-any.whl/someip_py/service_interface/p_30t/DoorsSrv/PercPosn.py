from someip_py.codec import *


class IdtSingleDoorPercPosn(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorPercPosn: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorPercPosn = Uint8()


class IdtDoorsPercPosn(SomeIpPayload):

    IdtDoorsPercPosn: SomeIpDynamicSizeArray[IdtSingleDoorPercPosn]

    def __init__(self):

        self.IdtDoorsPercPosn = SomeIpDynamicSizeArray(IdtSingleDoorPercPosn)
