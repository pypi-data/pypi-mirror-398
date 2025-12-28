from someip_py.codec import *


class IdtSuspTargetHeiValueKls(SomeIpPayload):

    _include_struct_len = True

    SuspTargetHeiFL: Float32

    SuspTargetHeiRR: Float32

    SuspTargetHeiRL: Float32

    SuspTargetHeiFR: Float32

    def __init__(self):

        self.SuspTargetHeiFL = Float32()

        self.SuspTargetHeiRR = Float32()

        self.SuspTargetHeiRL = Float32()

        self.SuspTargetHeiFR = Float32()


class IdtSuspTargetHeiValue(SomeIpPayload):

    IdtSuspTargetHeiValue: IdtSuspTargetHeiValueKls

    def __init__(self):

        self.IdtSuspTargetHeiValue = IdtSuspTargetHeiValueKls()
