from someip_py.codec import *


class IdtAiChassisSusSts(SomeIpPayload):

    IdtAiChassisSusSts: Uint8

    def __init__(self):

        self.IdtAiChassisSusSts = Uint8()
