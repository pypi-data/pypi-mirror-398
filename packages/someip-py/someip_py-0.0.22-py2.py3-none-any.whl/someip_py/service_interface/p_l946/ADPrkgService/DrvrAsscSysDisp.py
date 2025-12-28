from someip_py.codec import *


class IdtDrvrAsscSysDisp(SomeIpPayload):

    IdtDrvrAsscSysDisp: Uint8

    def __init__(self):

        self.IdtDrvrAsscSysDisp = Uint8()
