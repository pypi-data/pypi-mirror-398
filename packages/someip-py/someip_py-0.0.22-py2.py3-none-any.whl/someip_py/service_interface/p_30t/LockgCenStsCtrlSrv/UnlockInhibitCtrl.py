from someip_py.codec import *


class IdtUnlockInhbReqKls(SomeIpPayload):

    _include_struct_len = True

    InhibitUninhibit: Uint8

    InhibitExtInt: Uint8

    InhibitSrc: Uint8

    def __init__(self):

        self.InhibitUninhibit = Uint8()

        self.InhibitExtInt = Uint8()

        self.InhibitSrc = Uint8()


class IdtUnlockInhbReq(SomeIpPayload):

    IdtUnlockInhbReq: IdtUnlockInhbReqKls

    def __init__(self):

        self.IdtUnlockInhbReq = IdtUnlockInhbReqKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
