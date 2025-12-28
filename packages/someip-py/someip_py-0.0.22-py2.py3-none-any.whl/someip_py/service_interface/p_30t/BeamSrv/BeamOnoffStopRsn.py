from someip_py.codec import *


class IdtExtLiStopCode(SomeIpPayload):

    IdtExtLiStopCode: Uint8

    def __init__(self):

        self.IdtExtLiStopCode = Uint8()
