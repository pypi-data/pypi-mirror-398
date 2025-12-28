from someip_py.codec import *


class IdtSteerAsscLvl(SomeIpPayload):

    IdtSteerAsscLvl: Uint8

    def __init__(self):

        self.IdtSteerAsscLvl = Uint8()
