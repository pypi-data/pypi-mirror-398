from someip_py.codec import *


class IdtLockgIndcnKls(SomeIpPayload):

    _include_struct_len = True

    LockgCenIndcn: Uint8

    UpdEve: Uint8

    def __init__(self):

        self.LockgCenIndcn = Uint8()

        self.UpdEve = Uint8()


class IdtLockgIndcn(SomeIpPayload):

    IdtLockgIndcn: IdtLockgIndcnKls

    def __init__(self):

        self.IdtLockgIndcn = IdtLockgIndcnKls()
