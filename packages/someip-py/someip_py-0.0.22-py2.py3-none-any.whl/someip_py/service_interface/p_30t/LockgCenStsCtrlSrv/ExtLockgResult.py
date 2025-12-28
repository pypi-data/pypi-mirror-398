from someip_py.codec import *


class IdtLockUnlockResultKls(SomeIpPayload):

    _include_struct_len = True

    LockUnlckSts: Uint8

    ResultSts: Uint8

    def __init__(self):

        self.LockUnlckSts = Uint8()

        self.ResultSts = Uint8()


class IdtLockUnlockResult(SomeIpPayload):

    IdtLockUnlockResult: IdtLockUnlockResultKls

    def __init__(self):

        self.IdtLockUnlockResult = IdtLockUnlockResultKls()
