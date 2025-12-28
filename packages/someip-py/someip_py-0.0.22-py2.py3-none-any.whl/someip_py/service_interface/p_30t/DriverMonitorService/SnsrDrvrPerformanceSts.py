from someip_py.codec import *


class IdtSnsrDrvrPfmncSts(SomeIpPayload):

    IdtSnsrDrvrPfmncSts: Uint8

    def __init__(self):

        self.IdtSnsrDrvrPfmncSts = Uint8()
