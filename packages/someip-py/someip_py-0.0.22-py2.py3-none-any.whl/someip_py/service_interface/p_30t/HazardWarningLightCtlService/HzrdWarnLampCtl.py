from someip_py.codec import *


class IdtHzrdWarnLampCmd(SomeIpPayload):

    IdtHzrdWarnLampCmd: Uint8

    def __init__(self):

        self.IdtHzrdWarnLampCmd = Uint8()


class IdtHzrdWarnLampSource(SomeIpPayload):

    IdtHzrdWarnLampSource: Uint8

    def __init__(self):

        self.IdtHzrdWarnLampSource = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
