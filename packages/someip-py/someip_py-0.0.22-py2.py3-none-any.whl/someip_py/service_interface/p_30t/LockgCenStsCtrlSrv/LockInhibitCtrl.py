from someip_py.codec import *


class IdtLockInhbReqKls(SomeIpPayload):

    _include_struct_len = True

    InhibitUninhibit: Uint8

    InhibitExtInt: Uint8

    InhibitSrc: Uint8

    def __init__(self):

        self.InhibitUninhibit = Uint8()

        self.InhibitExtInt = Uint8()

        self.InhibitSrc = Uint8()


class IdtLockInhbReq(SomeIpPayload):

    IdtLockInhbReq: IdtLockInhbReqKls

    def __init__(self):

        self.IdtLockInhbReq = IdtLockInhbReqKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
