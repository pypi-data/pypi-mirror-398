from someip_py.codec import *


class IdtClimaSrc(SomeIpPayload):

    IdtClimaSrc: Uint8

    def __init__(self):

        self.IdtClimaSrc = Uint8()


class IdtClimaAppl(SomeIpPayload):

    IdtClimaAppl: Uint8

    def __init__(self):

        self.IdtClimaAppl = Uint8()


class IdtSceneTi(SomeIpPayload):

    IdtSceneTi: Int8

    def __init__(self):

        self.IdtSceneTi = Int8()


class IdtClimaT(SomeIpPayload):

    IdtClimaT: Float32

    def __init__(self):

        self.IdtClimaT = Float32()


class IdtClimaRspn(SomeIpPayload):

    IdtClimaRspn: Bool

    def __init__(self):

        self.IdtClimaRspn = Bool()
