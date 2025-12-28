from someip_py.codec import *


class IdtSimSigLevel(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimSigLevel: Uint8

    def __init__(self):

        self.SimNo = Uint8()

        self.SimSigLevel = Uint8()


class IdtAllSigLevel(SomeIpPayload):

    IdtAllSigLevel: SomeIpDynamicSizeArray[IdtSimSigLevel]

    def __init__(self):

        self.IdtAllSigLevel = SomeIpDynamicSizeArray(IdtSimSigLevel)
