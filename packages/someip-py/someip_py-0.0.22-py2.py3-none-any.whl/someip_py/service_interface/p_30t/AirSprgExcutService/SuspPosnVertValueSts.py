from someip_py.codec import *


class IdtSuspPosnVertValueKls(SomeIpPayload):

    _include_struct_len = True

    SuspPosnVertFR: Float32

    SuspPosnVertRR: Float32

    SuspPosnVertFRQf: Uint8

    SuspPosnVertRRQf: Uint8

    SuspPosnVertFL: Float32

    SuspPosnVertRL: Float32

    SuspPosnVertFLQf: Uint8

    SuspPosnVertRLQf: Uint8

    def __init__(self):

        self.SuspPosnVertFR = Float32()

        self.SuspPosnVertRR = Float32()

        self.SuspPosnVertFRQf = Uint8()

        self.SuspPosnVertRRQf = Uint8()

        self.SuspPosnVertFL = Float32()

        self.SuspPosnVertRL = Float32()

        self.SuspPosnVertFLQf = Uint8()

        self.SuspPosnVertRLQf = Uint8()


class IdtSuspPosnVertValue(SomeIpPayload):

    IdtSuspPosnVertValue: IdtSuspPosnVertValueKls

    def __init__(self):

        self.IdtSuspPosnVertValue = IdtSuspPosnVertValueKls()
