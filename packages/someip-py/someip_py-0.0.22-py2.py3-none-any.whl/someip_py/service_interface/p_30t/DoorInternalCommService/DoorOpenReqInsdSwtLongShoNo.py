from someip_py.codec import *


class IdtSingleDoorOpenReqInsdSwtSts(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorOpenReqInsdSwt: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorOpenReqInsdSwt = Uint8()


class IdtDoorsOpenReqInsdSwtSts(SomeIpPayload):

    IdtDoorsOpenReqInsdSwtSts: SomeIpDynamicSizeArray[IdtSingleDoorOpenReqInsdSwtSts]

    def __init__(self):

        self.IdtDoorsOpenReqInsdSwtSts = SomeIpDynamicSizeArray(
            IdtSingleDoorOpenReqInsdSwtSts
        )
