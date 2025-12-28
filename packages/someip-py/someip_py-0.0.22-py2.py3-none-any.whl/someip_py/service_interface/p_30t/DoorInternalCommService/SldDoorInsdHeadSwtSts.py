from someip_py.codec import *


class IdtSingleDoorInsdHeadSwtStruct(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    SwtSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.SwtSts = Uint8()


class IdtDoorsInsdHeadSwtAry(SomeIpPayload):

    IdtDoorsInsdHeadSwtAry: SomeIpDynamicSizeArray[IdtSingleDoorInsdHeadSwtStruct]

    def __init__(self):

        self.IdtDoorsInsdHeadSwtAry = SomeIpDynamicSizeArray(
            IdtSingleDoorInsdHeadSwtStruct
        )
