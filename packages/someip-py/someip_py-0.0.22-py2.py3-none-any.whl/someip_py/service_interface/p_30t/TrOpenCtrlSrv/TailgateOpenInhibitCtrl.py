from someip_py.codec import *


class IdtTrOpnInhbReqKls(SomeIpPayload):

    _include_struct_len = True

    InhibitUninhibit: Uint8

    InhibitOpenClose: Uint8

    InhibitSrc: Uint8

    def __init__(self):

        self.InhibitUninhibit = Uint8()

        self.InhibitOpenClose = Uint8()

        self.InhibitSrc = Uint8()


class IdtTrOpnInhbReq(SomeIpPayload):

    IdtTrOpnInhbReq: IdtTrOpnInhbReqKls

    def __init__(self):

        self.IdtTrOpnInhbReq = IdtTrOpnInhbReqKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
