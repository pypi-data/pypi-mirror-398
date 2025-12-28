from someip_py.codec import *


class IdtNightVisionSnsrSts(SomeIpPayload):

    IdtNightVisionSnsrSts: Uint8

    def __init__(self):

        self.IdtNightVisionSnsrSts = Uint8()
