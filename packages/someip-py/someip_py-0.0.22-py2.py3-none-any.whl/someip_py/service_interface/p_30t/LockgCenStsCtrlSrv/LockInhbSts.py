from someip_py.codec import *


class IdtLockInhbStsKls(SomeIpPayload):

    _include_struct_len = True

    InhibitUninhibit: Uint8

    InhibitExtInt: Uint8

    InhibitSrc: Uint8

    def __init__(self):

        self.InhibitUninhibit = Uint8()

        self.InhibitExtInt = Uint8()

        self.InhibitSrc = Uint8()


class IdtLockInhbSts(SomeIpPayload):

    IdtLockInhbSts: IdtLockInhbStsKls

    def __init__(self):

        self.IdtLockInhbSts = IdtLockInhbStsKls()
