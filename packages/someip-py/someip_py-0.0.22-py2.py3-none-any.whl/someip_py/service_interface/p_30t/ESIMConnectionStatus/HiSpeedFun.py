from someip_py.codec import *


class IdtSimHiSpdFun(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimHiSpdFun: Bool

    def __init__(self):

        self.SimNo = Uint8()

        self.SimHiSpdFun = Bool()


class IdtAllHiSpdFun(SomeIpPayload):

    IdtAllHiSpdFun: SomeIpDynamicSizeArray[IdtSimHiSpdFun]

    def __init__(self):

        self.IdtAllHiSpdFun = SomeIpDynamicSizeArray(IdtSimHiSpdFun)
