from someip_py.codec import *


class IdtExtCenLockgReqKls(SomeIpPayload):

    _include_struct_len = True

    LockgCenReq: Uint8

    DoorLockID: Uint8

    def __init__(self):

        self.LockgCenReq = Uint8()

        self.DoorLockID = Uint8()


class IdtExtCenLockgReq(SomeIpPayload):

    IdtExtCenLockgReq: IdtExtCenLockgReqKls

    def __init__(self):

        self.IdtExtCenLockgReq = IdtExtCenLockgReqKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
