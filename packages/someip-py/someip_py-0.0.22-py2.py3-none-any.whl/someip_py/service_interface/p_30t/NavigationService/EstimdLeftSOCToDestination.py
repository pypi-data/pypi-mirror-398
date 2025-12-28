from someip_py.codec import *


class IdtLeftSOC(SomeIpPayload):

    IdtLeftSOC: Uint8

    def __init__(self):

        self.IdtLeftSOC = Uint8()
