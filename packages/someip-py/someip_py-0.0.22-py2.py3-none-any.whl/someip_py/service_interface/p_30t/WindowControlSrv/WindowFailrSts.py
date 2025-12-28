from someip_py.codec import *


class IdtAllWindowFailrSts(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowFailrSts: Uint8

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowFailrSts = Uint8()


class IdtWindowFailrStsAry(SomeIpPayload):

    IdtWindowFailrStsAry: SomeIpDynamicSizeArray[IdtAllWindowFailrSts]

    def __init__(self):

        self.IdtWindowFailrStsAry = SomeIpDynamicSizeArray(IdtAllWindowFailrSts)
