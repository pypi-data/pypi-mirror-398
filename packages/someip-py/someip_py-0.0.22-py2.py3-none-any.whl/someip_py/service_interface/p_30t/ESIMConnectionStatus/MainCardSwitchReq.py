from someip_py.codec import *


class IdtSimNo(SomeIpPayload):

    IdtSimNo: Uint8

    def __init__(self):

        self.IdtSimNo = Uint8()


class IdtCmdResp(SomeIpPayload):

    IdtCmdResp: Bool

    def __init__(self):

        self.IdtCmdResp = Bool()
