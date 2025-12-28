from someip_py.codec import *


class IdtAIChassisFuncSts(SomeIpPayload):

    IdtAIChassisFuncSts: Uint8

    def __init__(self):

        self.IdtAIChassisFuncSts = Uint8()
