from someip_py.codec import *


class IdtAllWindowPositionFb(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowPositionFb: Uint8

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowPositionFb = Uint8()


class IdtWindowPosFbAry(SomeIpPayload):

    IdtWindowPosFbAry: SomeIpDynamicSizeArray[IdtAllWindowPositionFb]

    def __init__(self):

        self.IdtWindowPosFbAry = SomeIpDynamicSizeArray(IdtAllWindowPositionFb)
