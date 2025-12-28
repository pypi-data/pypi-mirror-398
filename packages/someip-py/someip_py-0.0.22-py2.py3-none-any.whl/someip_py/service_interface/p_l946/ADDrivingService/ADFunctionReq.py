from someip_py.codec import *


class IdtADFunctionReq(SomeIpPayload):

    IdtADFunctionReq: Uint8

    def __init__(self):

        self.IdtADFunctionReq = Uint8()


class IdtADFunctionRet(SomeIpPayload):

    IdtADFunctionRet: Uint8

    def __init__(self):

        self.IdtADFunctionRet = Uint8()
