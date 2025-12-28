from someip_py.codec import *


class IdtAVMMonrSysSts(SomeIpPayload):

    IdtAVMMonrSysSts: Uint8

    def __init__(self):

        self.IdtAVMMonrSysSts = Uint8()
