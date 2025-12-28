from someip_py.codec import *


class IdtTailgateOpenSts(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    DoorOpenSts: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.DoorOpenSts = Uint8()


class IdtTailgatesOpenSts(SomeIpPayload):

    IdtTailgatesOpenSts: SomeIpDynamicSizeArray[IdtTailgateOpenSts]

    def __init__(self):

        self.IdtTailgatesOpenSts = SomeIpDynamicSizeArray(IdtTailgateOpenSts)
