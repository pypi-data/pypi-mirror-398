from someip_py.codec import *


class IdtDrvrMonrAlrmSts(SomeIpPayload):

    IdtDrvrMonrAlrmSts: Uint8

    def __init__(self):

        self.IdtDrvrMonrAlrmSts = Uint8()
