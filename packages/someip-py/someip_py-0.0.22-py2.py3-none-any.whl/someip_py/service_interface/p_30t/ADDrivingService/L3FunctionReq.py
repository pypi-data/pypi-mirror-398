from someip_py.codec import *


class IdtL3FunctionReq(SomeIpPayload):

    IdtL3FunctionReq: Uint8

    def __init__(self):

        self.IdtL3FunctionReq = Uint8()


class IdtL3FunctionRet(SomeIpPayload):

    IdtL3FunctionRet: Uint8

    def __init__(self):

        self.IdtL3FunctionRet = Uint8()
