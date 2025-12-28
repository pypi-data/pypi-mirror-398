from someip_py.codec import *


class IdtSimNetAvl(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimNetAvl: Bool

    def __init__(self):

        self.SimNo = Uint8()

        self.SimNetAvl = Bool()


class IdtAllNetAvl(SomeIpPayload):

    IdtAllNetAvl: SomeIpDynamicSizeArray[IdtSimNetAvl]

    def __init__(self):

        self.IdtAllNetAvl = SomeIpDynamicSizeArray(IdtSimNetAvl)
