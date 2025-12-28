from someip_py.codec import *


class IdtSingleDoorOpnInsdSwtStruct(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    SwtSts: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.SwtSts = Uint8()


class IdtDoorsOpnInsdSwtAry(SomeIpPayload):

    IdtDoorsOpnInsdSwtAry: SomeIpDynamicSizeArray[IdtSingleDoorOpnInsdSwtStruct]

    def __init__(self):

        self.IdtDoorsOpnInsdSwtAry = SomeIpDynamicSizeArray(
            IdtSingleDoorOpnInsdSwtStruct
        )
