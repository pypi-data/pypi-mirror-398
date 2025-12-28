from someip_py.codec import *


class IdtWMRBoolFb(SomeIpPayload):

    IdtWMRBoolFb: Uint8

    def __init__(self):

        self.IdtWMRBoolFb = Uint8()
