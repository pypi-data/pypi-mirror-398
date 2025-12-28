from someip_py.codec import *


class IdtClimaSrc(SomeIpPayload):

    IdtClimaSrc: Uint8

    def __init__(self):

        self.IdtClimaSrc = Uint8()


class IdtClimaHvacRecircCmd(SomeIpPayload):

    IdtClimaHvacRecircCmd: Uint8

    def __init__(self):

        self.IdtClimaHvacRecircCmd = Uint8()


class IdtClimaRspn(SomeIpPayload):

    IdtClimaRspn: Bool

    def __init__(self):

        self.IdtClimaRspn = Bool()
