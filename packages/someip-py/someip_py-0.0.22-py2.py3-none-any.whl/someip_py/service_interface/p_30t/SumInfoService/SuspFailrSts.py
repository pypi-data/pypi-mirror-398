from someip_py.codec import *


class IdtSuspFailrStatusKls(SomeIpPayload):

    _include_struct_len = True

    LvlgSuspFailrStatus: Uint8

    SuspFailrStatusQuality: Uint8

    def __init__(self):

        self.LvlgSuspFailrStatus = Uint8()

        self.SuspFailrStatusQuality = Uint8()


class IdtSuspFailrStatus(SomeIpPayload):

    IdtSuspFailrStatus: IdtSuspFailrStatusKls

    def __init__(self):

        self.IdtSuspFailrStatus = IdtSuspFailrStatusKls()
