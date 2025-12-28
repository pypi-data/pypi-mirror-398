from someip_py.codec import *


class IdtHighResolution(SomeIpPayload):

    IdtHighResolution: Uint8

    def __init__(self):

        self.IdtHighResolution = Uint8()
