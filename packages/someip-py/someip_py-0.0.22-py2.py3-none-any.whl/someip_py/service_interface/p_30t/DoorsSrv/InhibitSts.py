from someip_py.codec import *


class IdtSingleDoorInhibitOpenCloseInhbSts(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    InhibitUninhibit: Uint8

    InhibitOpenClose: Uint8

    InhibitSrc: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.InhibitUninhibit = Uint8()

        self.InhibitOpenClose = Uint8()

        self.InhibitSrc = Uint8()


class IdtDoorsOpnClsInhbSts(SomeIpPayload):

    IdtDoorsOpnClsInhbSts: SomeIpDynamicSizeArray[IdtSingleDoorInhibitOpenCloseInhbSts]

    def __init__(self):

        self.IdtDoorsOpnClsInhbSts = SomeIpDynamicSizeArray(
            IdtSingleDoorInhibitOpenCloseInhbSts
        )
