from someip_py.codec import *


class IdtTailgateOnOffSts(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    DoorSts: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.DoorSts = Uint8()


class IdtTailgatesOnOffSts(SomeIpPayload):

    IdtTailgatesOnOffSts: SomeIpDynamicSizeArray[IdtTailgateOnOffSts]

    def __init__(self):

        self.IdtTailgatesOnOffSts = SomeIpDynamicSizeArray(IdtTailgateOnOffSts)
