from someip_py.codec import *


class IdtPrkgProcDstDisp(SomeIpPayload):

    IdtPrkgProcDstDisp: Uint16

    def __init__(self):

        self.IdtPrkgProcDstDisp = Uint16()
