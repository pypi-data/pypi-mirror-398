from someip_py.codec import *


class IdtBeamSwtDevSts(SomeIpPayload):

    IdtBeamSwtDevSts: Uint8

    def __init__(self):

        self.IdtBeamSwtDevSts = Uint8()
