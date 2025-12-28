from someip_py.codec import *


class IdtFuelLidCtrlReq(SomeIpPayload):

    IdtFuelLidCtrlReq: Uint8

    def __init__(self):

        self.IdtFuelLidCtrlReq = Uint8()


class IdtFuelLidTrigSrc(SomeIpPayload):

    IdtFuelLidTrigSrc: Uint8

    def __init__(self):

        self.IdtFuelLidTrigSrc = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
