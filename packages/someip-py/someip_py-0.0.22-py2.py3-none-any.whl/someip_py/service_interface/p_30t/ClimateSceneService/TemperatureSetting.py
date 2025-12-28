from someip_py.codec import *


class IdtClimaSrc(SomeIpPayload):

    IdtClimaSrc: Uint8

    def __init__(self):

        self.IdtClimaSrc = Uint8()


class IdtClimaSceneZoneTReqKls(SomeIpPayload):

    _include_struct_len = True

    ClimateZoneID: Uint8

    ClimaCmptmtTReq: Float32

    def __init__(self):

        self.ClimateZoneID = Uint8()

        self.ClimaCmptmtTReq = Float32()


class IdtClimaSceneZoneTReq(SomeIpPayload):

    IdtClimaSceneZoneTReq: IdtClimaSceneZoneTReqKls

    def __init__(self):

        self.IdtClimaSceneZoneTReq = IdtClimaSceneZoneTReqKls()


class IdtClimaRspn(SomeIpPayload):

    IdtClimaRspn: Bool

    def __init__(self):

        self.IdtClimaRspn = Bool()
