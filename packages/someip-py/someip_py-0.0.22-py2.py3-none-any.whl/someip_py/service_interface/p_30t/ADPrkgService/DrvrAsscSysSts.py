from someip_py.codec import *


class IdtDrvrAsscSysSts(SomeIpPayload):

    IdtDrvrAsscSysSts: Uint8

    def __init__(self):

        self.IdtDrvrAsscSysSts = Uint8()
