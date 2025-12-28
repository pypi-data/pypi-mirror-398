from someip_py.codec import *


class IdtSingleDoorsInhibitCtrl(SomeIpPayload):

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


class IdtDoorsInhibitCtrl(SomeIpPayload):

    IdtDoorsInhibitCtrl: SomeIpDynamicSizeArray[IdtSingleDoorsInhibitCtrl]

    def __init__(self):

        self.IdtDoorsInhibitCtrl = SomeIpDynamicSizeArray(IdtSingleDoorsInhibitCtrl)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
