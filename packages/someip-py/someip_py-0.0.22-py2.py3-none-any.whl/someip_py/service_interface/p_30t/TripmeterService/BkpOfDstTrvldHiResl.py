from someip_py.codec import *


class IdtOdoResolution(SomeIpPayload):

    IdtOdoResolution: Uint32

    def __init__(self):

        self.IdtOdoResolution = Uint32()
