from someip_py.codec import *


class IdtPrkgAssiSysRemPrkgSts(SomeIpPayload):

    IdtPrkgAssiSysRemPrkgSts: Uint8

    def __init__(self):

        self.IdtPrkgAssiSysRemPrkgSts = Uint8()
