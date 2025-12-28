from someip_py.codec import *


class IdtSimDataCnctnSts(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimDataCnctnSts: Uint8

    def __init__(self):

        self.SimNo = Uint8()

        self.SimDataCnctnSts = Uint8()


class IdtAllDataCnctnSts(SomeIpPayload):

    IdtAllDataCnctnSts: SomeIpDynamicSizeArray[IdtSimDataCnctnSts]

    def __init__(self):

        self.IdtAllDataCnctnSts = SomeIpDynamicSizeArray(IdtSimDataCnctnSts)
