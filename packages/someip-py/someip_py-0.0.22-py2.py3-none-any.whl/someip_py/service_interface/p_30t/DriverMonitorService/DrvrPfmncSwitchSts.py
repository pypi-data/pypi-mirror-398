from someip_py.codec import *


class IdtOnOff(SomeIpPayload):

    IdtOnOff: Uint8

    def __init__(self):

        self.IdtOnOff = Uint8()
