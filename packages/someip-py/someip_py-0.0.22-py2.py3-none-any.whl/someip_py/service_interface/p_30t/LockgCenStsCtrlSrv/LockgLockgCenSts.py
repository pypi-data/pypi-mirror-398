from someip_py.codec import *


class IdtLockgCenStsKls(SomeIpPayload):

    _include_struct_len = True

    LockSt: Uint8

    TrigSrc: Uint8

    UpdEve: Uint8

    def __init__(self):

        self.LockSt = Uint8()

        self.TrigSrc = Uint8()

        self.UpdEve = Uint8()


class IdtLockgCenSts(SomeIpPayload):

    IdtLockgCenSts: IdtLockgCenStsKls

    def __init__(self):

        self.IdtLockgCenSts = IdtLockgCenStsKls()
