from someip_py.codec import *


class IdtIntCenLockgReqKls(SomeIpPayload):

    _include_struct_len = True

    LockgCenReq: Uint8

    DoorLockID: Uint8

    def __init__(self):

        self.LockgCenReq = Uint8()

        self.DoorLockID = Uint8()


class IdtIntCenLockgReq(SomeIpPayload):

    IdtIntCenLockgReq: IdtIntCenLockgReqKls

    def __init__(self):

        self.IdtIntCenLockgReq = IdtIntCenLockgReqKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
