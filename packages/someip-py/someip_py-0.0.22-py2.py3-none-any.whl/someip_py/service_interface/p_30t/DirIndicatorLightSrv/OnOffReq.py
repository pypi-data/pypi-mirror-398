from someip_py.codec import *


class IdtExtLiTurnLiCtrlReqStrKls(SomeIpPayload):

    _include_struct_len = True

    Request: Uint8

    Priority: Uint8

    HighTime: Uint8

    LowTime: Uint8

    DetailParameter1: Uint8

    DetailParameter2: Uint8

    def __init__(self):

        self.Request = Uint8()

        self.Priority = Uint8()

        self.HighTime = Uint8()

        self.LowTime = Uint8()

        self.DetailParameter1 = Uint8()

        self.DetailParameter2 = Uint8()


class IdtExtLiTurnLiCtrlReqStr(SomeIpPayload):

    IdtExtLiTurnLiCtrlReqStr: IdtExtLiTurnLiCtrlReqStrKls

    def __init__(self):

        self.IdtExtLiTurnLiCtrlReqStr = IdtExtLiTurnLiCtrlReqStrKls()


class IdtExtLiUint8(SomeIpPayload):

    IdtExtLiUint8: Uint8

    def __init__(self):

        self.IdtExtLiUint8 = Uint8()


class IdtExLiReturnCode(SomeIpPayload):

    IdtExLiReturnCode: Uint8

    def __init__(self):

        self.IdtExLiReturnCode = Uint8()
