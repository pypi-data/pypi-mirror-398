from someip_py.codec import *


class IdtAutoManualSts(SomeIpPayload):

    _include_struct_len = True

    TailgateID: Uint8

    DoorModeSts: Uint8

    UpdEve: Uint8

    def __init__(self):

        self.TailgateID = Uint8()

        self.DoorModeSts = Uint8()

        self.UpdEve = Uint8()


class IdtTailgatesAutoManualSts(SomeIpPayload):

    IdtTailgatesAutoManualSts: SomeIpDynamicSizeArray[IdtAutoManualSts]

    def __init__(self):

        self.IdtTailgatesAutoManualSts = SomeIpDynamicSizeArray(IdtAutoManualSts)
