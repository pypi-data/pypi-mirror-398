from someip_py.codec import *


class IdtSingle2ReleaseInhbActSts(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    InhibitUninhibit: Uint8

    InhibitExtInt: Uint8

    InhibitSrc: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.InhibitUninhibit = Uint8()

        self.InhibitExtInt = Uint8()

        self.InhibitSrc = Uint8()


class IdtDoors2ReleaseInhbActSts(SomeIpPayload):

    IdtDoors2ReleaseInhbActSts: SomeIpDynamicSizeArray[IdtSingle2ReleaseInhbActSts]

    def __init__(self):

        self.IdtDoors2ReleaseInhbActSts = SomeIpDynamicSizeArray(
            IdtSingle2ReleaseInhbActSts
        )
