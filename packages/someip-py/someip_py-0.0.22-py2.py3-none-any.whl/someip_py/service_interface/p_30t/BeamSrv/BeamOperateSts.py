from someip_py.codec import *


class IdtAutoBeamSwtDevSts(SomeIpPayload):

    IdtAutoBeamSwtDevSts: Uint8

    def __init__(self):

        self.IdtAutoBeamSwtDevSts = Uint8()
