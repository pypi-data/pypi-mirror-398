from someip_py.codec import *


class IdtSimMainCardSts(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimMainCardSts: Bool

    def __init__(self):

        self.SimNo = Uint8()

        self.SimMainCardSts = Bool()


class IdtAllMainCardSts(SomeIpPayload):

    IdtAllMainCardSts: SomeIpDynamicSizeArray[IdtSimMainCardSts]

    def __init__(self):

        self.IdtAllMainCardSts = SomeIpDynamicSizeArray(IdtSimMainCardSts)
