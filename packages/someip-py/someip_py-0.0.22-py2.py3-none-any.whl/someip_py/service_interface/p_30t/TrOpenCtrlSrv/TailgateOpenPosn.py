from someip_py.codec import *


class IdtTailgatePosition(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    DoorPositon: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.DoorPositon = Uint8()


class IdtTailgatesPosition(SomeIpPayload):

    IdtTailgatesPosition: SomeIpDynamicSizeArray[IdtTailgatePosition]

    def __init__(self):

        self.IdtTailgatesPosition = SomeIpDynamicSizeArray(IdtTailgatePosition)
