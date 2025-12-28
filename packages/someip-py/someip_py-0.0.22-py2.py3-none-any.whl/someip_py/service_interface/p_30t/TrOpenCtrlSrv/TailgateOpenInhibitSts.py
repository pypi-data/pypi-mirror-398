from someip_py.codec import *


class IdtTailgateOpenInhabitStsKls(SomeIpPayload):

    _include_struct_len = True

    InhibitUninhibit: Uint8

    InhibitOpenClose: Uint8

    InhibitSrc: Uint8

    def __init__(self):

        self.InhibitUninhibit = Uint8()

        self.InhibitOpenClose = Uint8()

        self.InhibitSrc = Uint8()


class IdtTailgateOpenInhabitSts(SomeIpPayload):

    IdtTailgateOpenInhabitSts: IdtTailgateOpenInhabitStsKls

    def __init__(self):

        self.IdtTailgateOpenInhabitSts = IdtTailgateOpenInhabitStsKls()
