from someip_py.codec import *


class IdtCardSwitchStsCode(SomeIpPayload):

    IdtCardSwitchStsCode: Uint8

    def __init__(self):

        self.IdtCardSwitchStsCode = Uint8()
