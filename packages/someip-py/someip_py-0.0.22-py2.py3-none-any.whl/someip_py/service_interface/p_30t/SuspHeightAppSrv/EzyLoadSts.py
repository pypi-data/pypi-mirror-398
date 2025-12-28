from someip_py.codec import *


class IdtEzyLoadSts(SomeIpPayload):

    IdtEzyLoadSts: Uint8

    def __init__(self):

        self.IdtEzyLoadSts = Uint8()
