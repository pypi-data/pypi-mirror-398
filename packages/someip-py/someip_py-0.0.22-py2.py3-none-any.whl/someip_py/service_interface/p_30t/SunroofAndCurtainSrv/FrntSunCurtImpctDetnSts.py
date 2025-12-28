from someip_py.codec import *


class IdtImpctDetnSts(SomeIpPayload):

    IdtImpctDetnSts: Uint8

    def __init__(self):

        self.IdtImpctDetnSts = Uint8()
