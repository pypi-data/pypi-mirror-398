from someip_py.codec import *


class IdtExLiOnOff(SomeIpPayload):

    IdtExLiOnOff: Uint8

    def __init__(self):

        self.IdtExLiOnOff = Uint8()


class IdtExLiReturnCode(SomeIpPayload):

    IdtExLiReturnCode: Uint8

    def __init__(self):

        self.IdtExLiReturnCode = Uint8()
