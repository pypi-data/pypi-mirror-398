from someip_py.codec import *


class IdtSimSigStrength(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimSigStrength: Uint8

    def __init__(self):

        self.SimNo = Uint8()

        self.SimSigStrength = Uint8()


class IdtAllSigStrength(SomeIpPayload):

    IdtAllSigStrength: SomeIpDynamicSizeArray[IdtSimSigStrength]

    def __init__(self):

        self.IdtAllSigStrength = SomeIpDynamicSizeArray(IdtSimSigStrength)
