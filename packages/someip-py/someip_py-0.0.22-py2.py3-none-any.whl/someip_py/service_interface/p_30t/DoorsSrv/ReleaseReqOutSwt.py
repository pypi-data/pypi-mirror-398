from someip_py.codec import *


class IdtSingle2ReleaseReqOutdSwt(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    SwitchSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.SwitchSts = Uint8()


class IdtReleaseReqOutSwt(SomeIpPayload):

    IdtReleaseReqOutSwt: SomeIpDynamicSizeArray[IdtSingle2ReleaseReqOutdSwt]

    def __init__(self):

        self.IdtReleaseReqOutSwt = SomeIpDynamicSizeArray(IdtSingle2ReleaseReqOutdSwt)
