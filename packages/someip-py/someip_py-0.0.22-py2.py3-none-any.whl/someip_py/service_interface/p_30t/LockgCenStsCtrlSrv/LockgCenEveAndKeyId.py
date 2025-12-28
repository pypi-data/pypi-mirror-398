from someip_py.codec import *


class IdtLockgCenEveAndKeyIdKls(SomeIpPayload):

    _include_struct_len = True

    LockUnlckSts: Uint8

    KeyId: Uint8

    def __init__(self):

        self.LockUnlckSts = Uint8()

        self.KeyId = Uint8()


class IdtLockgCenEveAndKeyId(SomeIpPayload):

    IdtLockgCenEveAndKeyId: IdtLockgCenEveAndKeyIdKls

    def __init__(self):

        self.IdtLockgCenEveAndKeyId = IdtLockgCenEveAndKeyIdKls()
