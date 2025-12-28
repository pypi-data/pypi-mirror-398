from someip_py.codec import *


class IdtChrgLidBlkSts(SomeIpPayload):

    _include_struct_len = True

    ChrgLidID: Uint8

    ChrgLidBlkSts: Uint8

    def __init__(self):

        self.ChrgLidID = Uint8()

        self.ChrgLidBlkSts = Uint8()


class IdtChrgLidsBlkSts(SomeIpPayload):

    IdtChrgLidsBlkSts: SomeIpDynamicSizeArray[IdtChrgLidBlkSts]

    def __init__(self):

        self.IdtChrgLidsBlkSts = SomeIpDynamicSizeArray(IdtChrgLidBlkSts)
