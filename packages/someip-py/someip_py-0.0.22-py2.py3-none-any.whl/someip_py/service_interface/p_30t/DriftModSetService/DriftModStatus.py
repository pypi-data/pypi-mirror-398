from someip_py.codec import *


class IdtDriftModStatus(SomeIpPayload):

    IdtDriftModStatus: Uint8

    def __init__(self):

        self.IdtDriftModStatus = Uint8()
