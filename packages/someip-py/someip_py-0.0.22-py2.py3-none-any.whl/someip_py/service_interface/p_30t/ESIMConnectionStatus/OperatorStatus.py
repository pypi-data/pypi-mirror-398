from someip_py.codec import *


class IdtSimOperatorSts(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimOperatorSts: Uint8

    def __init__(self):

        self.SimNo = Uint8()

        self.SimOperatorSts = Uint8()


class IdtAllOperatorSts(SomeIpPayload):

    IdtAllOperatorSts: SomeIpDynamicSizeArray[IdtSimOperatorSts]

    def __init__(self):

        self.IdtAllOperatorSts = SomeIpDynamicSizeArray(IdtSimOperatorSts)
