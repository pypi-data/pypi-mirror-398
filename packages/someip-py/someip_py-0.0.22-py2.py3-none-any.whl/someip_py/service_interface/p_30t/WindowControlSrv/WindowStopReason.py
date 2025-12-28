from someip_py.codec import *


class IdtAllWindowStopReason(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowStopReason: Uint8

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowStopReason = Uint8()


class IdtWindowStopReasonAry(SomeIpPayload):

    IdtWindowStopReasonAry: SomeIpDynamicSizeArray[IdtAllWindowStopReason]

    def __init__(self):

        self.IdtWindowStopReasonAry = SomeIpDynamicSizeArray(IdtAllWindowStopReason)
