from someip_py.codec import *


class IdtEzyLoadFuncSts(SomeIpPayload):

    IdtEzyLoadFuncSts: Uint8

    def __init__(self):

        self.IdtEzyLoadFuncSts = Uint8()
