from someip_py.codec import *


class IdtAllWindowSwitchPopup(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowSwitchPopup: Uint8

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowSwitchPopup = Uint8()


class IdtWindowSwitchPopupAry(SomeIpPayload):

    IdtWindowSwitchPopupAry: SomeIpDynamicSizeArray[IdtAllWindowSwitchPopup]

    def __init__(self):

        self.IdtWindowSwitchPopupAry = SomeIpDynamicSizeArray(IdtAllWindowSwitchPopup)
