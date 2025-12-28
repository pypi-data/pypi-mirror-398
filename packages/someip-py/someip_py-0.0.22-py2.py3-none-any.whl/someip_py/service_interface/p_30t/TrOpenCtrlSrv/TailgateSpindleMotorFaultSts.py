from someip_py.codec import *


class IdtTailgateMotorFaultStatus(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    MotorFaultSts: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.MotorFaultSts = Uint8()


class IdtTailgatesMotorFaultStatus(SomeIpPayload):

    IdtTailgatesMotorFaultStatus: SomeIpDynamicSizeArray[IdtTailgateMotorFaultStatus]

    def __init__(self):

        self.IdtTailgatesMotorFaultStatus = SomeIpDynamicSizeArray(
            IdtTailgateMotorFaultStatus
        )
