from someip_py.codec import *


class IdtClimaSrc(SomeIpPayload):

    IdtClimaSrc: Uint8

    def __init__(self):

        self.IdtClimaSrc = Uint8()


class IdtClimaSceneZoneAirDistbnReqKls(SomeIpPayload):

    _include_struct_len = True

    ClimateZoneID: Uint8

    ClimaAirDistbnReq: Uint8

    def __init__(self):

        self.ClimateZoneID = Uint8()

        self.ClimaAirDistbnReq = Uint8()


class IdtClimaSceneZoneAirDistbnReq(SomeIpPayload):

    IdtClimaSceneZoneAirDistbnReq: IdtClimaSceneZoneAirDistbnReqKls

    def __init__(self):

        self.IdtClimaSceneZoneAirDistbnReq = IdtClimaSceneZoneAirDistbnReqKls()


class IdtClimaRspn(SomeIpPayload):

    IdtClimaRspn: Bool

    def __init__(self):

        self.IdtClimaRspn = Bool()
