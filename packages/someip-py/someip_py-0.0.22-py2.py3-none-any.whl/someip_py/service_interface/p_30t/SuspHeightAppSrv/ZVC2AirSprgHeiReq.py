from someip_py.codec import *


class IdtSuspHeiValReqKls(SomeIpPayload):

    _include_struct_len = True

    CtrlReqFL: Uint8

    CtrlReqFR: Uint8

    CtrlReqRL: Uint8

    CtrlReqRR: Uint8

    SuspHeiValReqFL: Float32

    SuspHeiValReqFR: Float32

    SuspHeiValReqRL: Float32

    SuspHeiValReqRR: Float32

    def __init__(self):

        self.CtrlReqFL = Uint8()

        self.CtrlReqFR = Uint8()

        self.CtrlReqRL = Uint8()

        self.CtrlReqRR = Uint8()

        self.SuspHeiValReqFL = Float32()

        self.SuspHeiValReqFR = Float32()

        self.SuspHeiValReqRL = Float32()

        self.SuspHeiValReqRR = Float32()


class IdtSuspHeiValReq(SomeIpPayload):

    IdtSuspHeiValReq: IdtSuspHeiValReqKls

    def __init__(self):

        self.IdtSuspHeiValReq = IdtSuspHeiValReqKls()
