from someip_py.codec import *


class IdtDILampCmd(SomeIpPayload):

    IdtDILampCmd: Uint8

    def __init__(self):

        self.IdtDILampCmd = Uint8()


class IdtDITriggerSrcSfty(SomeIpPayload):

    IdtDITriggerSrcSfty: Uint8

    def __init__(self):

        self.IdtDITriggerSrcSfty = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
