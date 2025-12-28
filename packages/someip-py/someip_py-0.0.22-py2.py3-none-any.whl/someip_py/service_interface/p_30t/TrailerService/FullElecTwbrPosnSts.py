from someip_py.codec import *


class IdtTwbrPosn(SomeIpPayload):

    IdtTwbrPosn: Uint8

    def __init__(self):

        self.IdtTwbrPosn = Uint8()
