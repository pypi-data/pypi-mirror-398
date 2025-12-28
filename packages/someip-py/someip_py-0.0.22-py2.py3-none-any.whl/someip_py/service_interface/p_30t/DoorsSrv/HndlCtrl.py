from someip_py.codec import *


class IdtSingleDoorHndlCtrl(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorHndlCmd: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorHndlCmd = Uint8()


class IdtDoorsHndlCtrl(SomeIpPayload):

    IdtDoorsHndlCtrl: SomeIpDynamicSizeArray[IdtSingleDoorHndlCtrl]

    def __init__(self):

        self.IdtDoorsHndlCtrl = SomeIpDynamicSizeArray(IdtSingleDoorHndlCtrl)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
