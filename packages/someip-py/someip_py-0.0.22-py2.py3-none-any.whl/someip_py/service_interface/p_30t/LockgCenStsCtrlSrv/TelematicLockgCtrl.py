from someip_py.codec import *


class IdtTeleLockgCmdReqKls(SomeIpPayload):

    _include_struct_len = True

    LockgCenReq: Uint8

    DoorLockID: Uint8

    def __init__(self):

        self.LockgCenReq = Uint8()

        self.DoorLockID = Uint8()


class IdtTeleLockgCmdReq(SomeIpPayload):

    IdtTeleLockgCmdReq: IdtTeleLockgCmdReqKls

    def __init__(self):

        self.IdtTeleLockgCmdReq = IdtTeleLockgCmdReqKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
