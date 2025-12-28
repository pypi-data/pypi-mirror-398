from someip_py.codec import *


class IdtDrvrPfmncAlrmSts(SomeIpPayload):

    IdtDrvrPfmncAlrmSts: Uint8

    def __init__(self):

        self.IdtDrvrPfmncAlrmSts = Uint8()
