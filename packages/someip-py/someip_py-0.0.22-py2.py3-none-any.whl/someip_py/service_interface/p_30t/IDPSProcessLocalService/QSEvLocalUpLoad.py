from someip_py.codec import *


class IdtQSEvLocalUpLoadCmd(SomeIpPayload):

    IdtQSEvLocalUpLoadCmd: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtQSEvLocalUpLoadCmd = SomeIpDynamicSizeString()


class IdtQSEvLocalUpLoadResult(SomeIpPayload):

    IdtQSEvLocalUpLoadResult: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtQSEvLocalUpLoadResult = SomeIpDynamicSizeString()
