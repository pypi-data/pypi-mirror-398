from someip_py.codec import *


class IdtSimICCIDInfo(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimICCIDInfo: SomeIpDynamicSizeString

    def __init__(self):

        self.SimNo = Uint8()

        self.SimICCIDInfo = SomeIpDynamicSizeString()


class IdtAllICCIDInfo(SomeIpPayload):

    IdtAllICCIDInfo: SomeIpDynamicSizeArray[IdtSimICCIDInfo]

    def __init__(self):

        self.IdtAllICCIDInfo = SomeIpDynamicSizeArray(IdtSimICCIDInfo)
