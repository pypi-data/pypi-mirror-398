from someip_py.codec import *


class IdtDevSts(SomeIpPayload):

    IdtDevSts: Uint8

    def __init__(self):

        self.IdtDevSts = Uint8()
