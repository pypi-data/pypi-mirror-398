from someip_py.codec import *


class IdtAllWindowMovSts(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowMovSts: Uint8

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowMovSts = Uint8()


class IdtWindowMovStsAry(SomeIpPayload):

    IdtWindowMovStsAry: SomeIpDynamicSizeArray[IdtAllWindowMovSts]

    def __init__(self):

        self.IdtWindowMovStsAry = SomeIpDynamicSizeArray(IdtAllWindowMovSts)
