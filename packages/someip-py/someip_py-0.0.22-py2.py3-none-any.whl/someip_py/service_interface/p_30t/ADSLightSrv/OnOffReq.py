from someip_py.codec import *


class IdtExtLiCtrlReqStrADSAltKls(SomeIpPayload):

    _include_struct_len = True

    Request: Uint8

    Priority: Uint8

    def __init__(self):

        self.Request = Uint8()

        self.Priority = Uint8()


class IdtExtLiCtrlReqStrADSAlt(SomeIpPayload):

    IdtExtLiCtrlReqStrADSAlt: IdtExtLiCtrlReqStrADSAltKls

    def __init__(self):

        self.IdtExtLiCtrlReqStrADSAlt = IdtExtLiCtrlReqStrADSAltKls()


class IdExLiUint8(SomeIpPayload):

    IdExLiUint8: Uint8

    def __init__(self):

        self.IdExLiUint8 = Uint8()


class IdtExLiReturnCode(SomeIpPayload):

    IdtExLiReturnCode: Uint8

    def __init__(self):

        self.IdtExLiReturnCode = Uint8()
