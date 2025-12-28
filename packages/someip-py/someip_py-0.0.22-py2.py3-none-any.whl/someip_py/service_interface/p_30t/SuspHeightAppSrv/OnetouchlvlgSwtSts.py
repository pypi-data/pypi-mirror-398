from someip_py.codec import *


class IdtOnOffSts(SomeIpPayload):

    IdtOnOffSts: Uint8

    def __init__(self):

        self.IdtOnOffSts = Uint8()
