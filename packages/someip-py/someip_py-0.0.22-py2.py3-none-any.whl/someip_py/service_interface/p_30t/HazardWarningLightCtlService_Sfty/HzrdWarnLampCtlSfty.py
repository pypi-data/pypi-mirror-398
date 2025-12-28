from someip_py.codec import *


class IdtHzrdWarnLampCmd(SomeIpPayload):

    IdtHzrdWarnLampCmd: Uint8

    def __init__(self):

        self.IdtHzrdWarnLampCmd = Uint8()


class IdtHWLSourceSfty(SomeIpPayload):

    IdtHWLSourceSfty: Uint8

    def __init__(self):

        self.IdtHWLSourceSfty = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
