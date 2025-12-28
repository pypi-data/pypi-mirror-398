from someip_py.codec import *


class IdtVSTDModeReq(SomeIpPayload):

    IdtVSTDModeReq: Uint8

    def __init__(self):

        self.IdtVSTDModeReq = Uint8()


class IdtRemoteControlCode(SomeIpPayload):

    IdtRemoteControlCode: Uint8

    def __init__(self):

        self.IdtRemoteControlCode = Uint8()
