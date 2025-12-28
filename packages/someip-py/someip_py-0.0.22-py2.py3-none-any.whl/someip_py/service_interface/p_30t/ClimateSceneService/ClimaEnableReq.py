from someip_py.codec import *


class IdtClimaSrc(SomeIpPayload):

    IdtClimaSrc: Uint8

    def __init__(self):

        self.IdtClimaSrc = Uint8()


class IdtEnaReq(SomeIpPayload):

    IdtEnaReq: Uint8

    def __init__(self):

        self.IdtEnaReq = Uint8()


class IdtClimaRspn(SomeIpPayload):

    IdtClimaRspn: Bool

    def __init__(self):

        self.IdtClimaRspn = Bool()
