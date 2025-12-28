from someip_py.codec import *


class IdtClimaSrc(SomeIpPayload):

    IdtClimaSrc: Uint8

    def __init__(self):

        self.IdtClimaSrc = Uint8()


class IdtClimaSet(SomeIpPayload):

    IdtClimaSet: Uint8

    def __init__(self):

        self.IdtClimaSet = Uint8()


class IdtOnOff(SomeIpPayload):

    IdtOnOff: Uint8

    def __init__(self):

        self.IdtOnOff = Uint8()


class IdtClimaRspn(SomeIpPayload):

    IdtClimaRspn: Bool

    def __init__(self):

        self.IdtClimaRspn = Bool()
