from someip_py.codec import *


class IdtPrkgFunctionReq(SomeIpPayload):

    IdtPrkgFunctionReq: Uint8

    def __init__(self):

        self.IdtPrkgFunctionReq = Uint8()


class IdtPrkgFunctionRet(SomeIpPayload):

    IdtPrkgFunctionRet: Uint8

    def __init__(self):

        self.IdtPrkgFunctionRet = Uint8()
