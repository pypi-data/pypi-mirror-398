from someip_py.codec import *


class IdtWipgOnOffSts(SomeIpPayload):

    IdtWipgOnOffSts: Uint8

    def __init__(self):

        self.IdtWipgOnOffSts = Uint8()
