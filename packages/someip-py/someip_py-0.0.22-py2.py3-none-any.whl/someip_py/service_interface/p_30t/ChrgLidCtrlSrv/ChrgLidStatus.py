from someip_py.codec import *


class IdtChrgLidSts(SomeIpPayload):

    _include_struct_len = True

    ChrgLidID: Uint8

    ChrgLidSts: Uint8

    def __init__(self):

        self.ChrgLidID = Uint8()

        self.ChrgLidSts = Uint8()


class IdtChrgLidsSts(SomeIpPayload):

    IdtChrgLidsSts: SomeIpDynamicSizeArray[IdtChrgLidSts]

    def __init__(self):

        self.IdtChrgLidsSts = SomeIpDynamicSizeArray(IdtChrgLidSts)
