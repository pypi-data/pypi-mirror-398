from someip_py.codec import *


class IdtVSTDFailureStatus(SomeIpPayload):

    IdtVSTDFailureStatus: Uint8

    def __init__(self):

        self.IdtVSTDFailureStatus = Uint8()
