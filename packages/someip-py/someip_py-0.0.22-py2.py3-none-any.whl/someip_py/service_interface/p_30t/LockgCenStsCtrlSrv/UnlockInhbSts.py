from someip_py.codec import *


class IdtUnlockInhbStsKls(SomeIpPayload):

    _include_struct_len = True

    InhibitUninhibit: Uint8

    InhibitExtInt: Uint8

    InhibitSrc: Uint8

    def __init__(self):

        self.InhibitUninhibit = Uint8()

        self.InhibitExtInt = Uint8()

        self.InhibitSrc = Uint8()


class IdtUnlockInhbSts(SomeIpPayload):

    IdtUnlockInhbSts: IdtUnlockInhbStsKls

    def __init__(self):

        self.IdtUnlockInhbSts = IdtUnlockInhbStsKls()
