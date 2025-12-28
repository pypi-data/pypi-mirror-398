from someip_py.codec import *


class IdtSingleDoorOpenCtrl(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorOpenCtrl: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorOpenCtrl = Uint8()


class IdtDoorsOpenCtrl(SomeIpPayload):

    IdtDoorsOpenCtrl: SomeIpDynamicSizeArray[IdtSingleDoorOpenCtrl]

    def __init__(self):

        self.IdtDoorsOpenCtrl = SomeIpDynamicSizeArray(IdtSingleDoorOpenCtrl)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
