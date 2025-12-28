from someip_py.codec import *


class IdtClimaSrc(SomeIpPayload):

    IdtClimaSrc: Uint8

    def __init__(self):

        self.IdtClimaSrc = Uint8()


class IdtClimaSceneZoneFanLvlReqKls(SomeIpPayload):

    _include_struct_len = True

    ClimateZoneID: Uint8

    ClimaFanLvlReq: Uint8

    def __init__(self):

        self.ClimateZoneID = Uint8()

        self.ClimaFanLvlReq = Uint8()


class IdtClimaSceneZoneFanLvlReq(SomeIpPayload):

    IdtClimaSceneZoneFanLvlReq: IdtClimaSceneZoneFanLvlReqKls

    def __init__(self):

        self.IdtClimaSceneZoneFanLvlReq = IdtClimaSceneZoneFanLvlReqKls()


class IdtClimaRspn(SomeIpPayload):

    IdtClimaRspn: Bool

    def __init__(self):

        self.IdtClimaRspn = Bool()
