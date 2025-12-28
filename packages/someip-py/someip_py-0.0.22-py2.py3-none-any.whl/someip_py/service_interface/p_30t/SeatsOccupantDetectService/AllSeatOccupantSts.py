from someip_py.codec import *


class IdtSeatOccupantStsItem(SomeIpPayload):

    _include_struct_len = True

    TargetSeatId: Uint8

    SeatOccupantSts: Uint8

    def __init__(self):

        self.TargetSeatId = Uint8()

        self.SeatOccupantSts = Uint8()


class IdtSeatOccupantStsArray(SomeIpPayload):

    IdtSeatOccupantStsArray: SomeIpDynamicSizeArray[IdtSeatOccupantStsItem]

    def __init__(self):

        self.IdtSeatOccupantStsArray = SomeIpDynamicSizeArray(IdtSeatOccupantStsItem)
