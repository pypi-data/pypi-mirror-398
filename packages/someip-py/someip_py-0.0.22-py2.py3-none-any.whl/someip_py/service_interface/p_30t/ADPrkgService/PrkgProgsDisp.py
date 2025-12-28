from someip_py.codec import *


class IdtPrkgProgsDisp(SomeIpPayload):

    IdtPrkgProgsDisp: Uint8

    def __init__(self):

        self.IdtPrkgProgsDisp = Uint8()
