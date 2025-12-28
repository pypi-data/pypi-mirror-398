from someip_py.codec import *


class IdtHealthLocalCmd(SomeIpPayload):

    IdtHealthLocalCmd: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtHealthLocalCmd = SomeIpDynamicSizeString()


class IdtHealthLocalResult(SomeIpPayload):

    IdtHealthLocalResult: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtHealthLocalResult = SomeIpDynamicSizeString()
