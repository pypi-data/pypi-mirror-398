from someip_py.codec import *


class IdtEnable(SomeIpPayload):

    IdtEnable: Bool

    def __init__(self):

        self.IdtEnable = Bool()


class IdtCooltFlowReq(SomeIpPayload):

    IdtCooltFlowReq: Float32

    def __init__(self):

        self.IdtCooltFlowReq = Float32()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
