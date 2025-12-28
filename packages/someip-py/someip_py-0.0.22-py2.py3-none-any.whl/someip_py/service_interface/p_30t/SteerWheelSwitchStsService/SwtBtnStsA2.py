from someip_py.codec import *


class IdtSteerWhlTouchBdReqKls(SomeIpPayload):

    _include_struct_len = True

    SteerWhlTouchBdSts: Uint8

    SteerWhlSwtQf: Uint8

    def __init__(self):

        self.SteerWhlTouchBdSts = Uint8()

        self.SteerWhlSwtQf = Uint8()


class IdtSteerWhlTouchBdReq(SomeIpPayload):

    IdtSteerWhlTouchBdReq: IdtSteerWhlTouchBdReqKls

    def __init__(self):

        self.IdtSteerWhlTouchBdReq = IdtSteerWhlTouchBdReqKls()
