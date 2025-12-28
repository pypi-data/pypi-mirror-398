from someip_py.codec import *


class IdtVSTDModeStatus(SomeIpPayload):

    IdtVSTDModeStatus: Uint8

    def __init__(self):

        self.IdtVSTDModeStatus = Uint8()
