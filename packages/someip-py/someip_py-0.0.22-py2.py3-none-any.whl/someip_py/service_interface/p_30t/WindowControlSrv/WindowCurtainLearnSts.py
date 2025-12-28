from someip_py.codec import *


class IdtAllWindowLearnSts(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowLearnSt: Uint8

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowLearnSt = Uint8()


class IdtWindowLearnStsAry(SomeIpPayload):

    IdtWindowLearnStsAry: SomeIpDynamicSizeArray[IdtAllWindowLearnSts]

    def __init__(self):

        self.IdtWindowLearnStsAry = SomeIpDynamicSizeArray(IdtAllWindowLearnSts)
