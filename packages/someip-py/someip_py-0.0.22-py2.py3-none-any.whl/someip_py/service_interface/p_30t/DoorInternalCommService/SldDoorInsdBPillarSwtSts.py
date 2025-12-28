from someip_py.codec import *


class IdtSingleDoorInsdBPillarSwtStruct(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    SwtSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.SwtSts = Uint8()


class IdtDoorsInsdBPillarSwtAry(SomeIpPayload):

    IdtDoorsInsdBPillarSwtAry: SomeIpDynamicSizeArray[IdtSingleDoorInsdBPillarSwtStruct]

    def __init__(self):

        self.IdtDoorsInsdBPillarSwtAry = SomeIpDynamicSizeArray(
            IdtSingleDoorInsdBPillarSwtStruct
        )
