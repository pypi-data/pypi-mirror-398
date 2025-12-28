from someip_py.codec import *


class IdtSimCnctnSts(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimCnctnSts: Uint8

    def __init__(self):

        self.SimNo = Uint8()

        self.SimCnctnSts = Uint8()


class IdtAllCnctnSts(SomeIpPayload):

    IdtAllCnctnSts: SomeIpDynamicSizeArray[IdtSimCnctnSts]

    def __init__(self):

        self.IdtAllCnctnSts = SomeIpDynamicSizeArray(IdtSimCnctnSts)
