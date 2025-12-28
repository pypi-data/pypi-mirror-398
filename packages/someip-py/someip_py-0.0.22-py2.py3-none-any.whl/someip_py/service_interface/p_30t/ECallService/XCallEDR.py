from someip_py.codec import *


class IdtEDRdata(SomeIpPayload):

    IdtEDRdata: Uint8

    def __init__(self):

        self.IdtEDRdata = Uint8()
