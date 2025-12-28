from someip_py.codec import *


class IdtExtLiCtrlReqStrFogAltKls(SomeIpPayload):

    _include_struct_len = True

    Request: Uint8

    Priority: Uint8

    def __init__(self):

        self.Request = Uint8()

        self.Priority = Uint8()


class IdtExtLiCtrlReqStrFogAlt(SomeIpPayload):

    IdtExtLiCtrlReqStrFogAlt: IdtExtLiCtrlReqStrFogAltKls

    def __init__(self):

        self.IdtExtLiCtrlReqStrFogAlt = IdtExtLiCtrlReqStrFogAltKls()


class IdtExLiUint8(SomeIpPayload):

    IdtExLiUint8: Uint8

    def __init__(self):

        self.IdtExLiUint8 = Uint8()


class IdtExLiReturnCode(SomeIpPayload):

    IdtExLiReturnCode: Uint8

    def __init__(self):

        self.IdtExLiReturnCode = Uint8()
