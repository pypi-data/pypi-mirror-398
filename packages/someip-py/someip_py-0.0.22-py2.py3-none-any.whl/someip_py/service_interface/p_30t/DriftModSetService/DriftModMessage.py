from someip_py.codec import *


class IdtDriftModMessage(SomeIpPayload):

    IdtDriftModMessage: Uint8

    def __init__(self):

        self.IdtDriftModMessage = Uint8()
