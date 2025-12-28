from someip_py.codec import *


class IdtAllWindowAntiPinchSts(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowAntiPinchSts: Uint8

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowAntiPinchSts = Uint8()


class IdtWindowAntiPinchStsAry(SomeIpPayload):

    IdtWindowAntiPinchStsAry: SomeIpDynamicSizeArray[IdtAllWindowAntiPinchSts]

    def __init__(self):

        self.IdtWindowAntiPinchStsAry = SomeIpDynamicSizeArray(IdtAllWindowAntiPinchSts)
