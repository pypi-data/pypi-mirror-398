from someip_py.codec import *


class IdtActvSafeCtrlrSts(SomeIpPayload):

    IdtActvSafeCtrlrSts: Uint8

    def __init__(self):

        self.IdtActvSafeCtrlrSts = Uint8()
