from someip_py.codec import *


class IdtPathDirectionArrowKls(SomeIpPayload):

    MainActionSeN: Uint8

    CrossOutCntSeN: Uint8

    DirectionDistanceSeN: Uint32

    def __init__(self):

        self.MainActionSeN = Uint8()

        self.CrossOutCntSeN = Uint8()

        self.DirectionDistanceSeN = Uint32()


class IdtPathDirectionArrow(SomeIpPayload):

    IdtPathDirectionArrow: IdtPathDirectionArrowKls

    def __init__(self):

        self.IdtPathDirectionArrow = IdtPathDirectionArrowKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
