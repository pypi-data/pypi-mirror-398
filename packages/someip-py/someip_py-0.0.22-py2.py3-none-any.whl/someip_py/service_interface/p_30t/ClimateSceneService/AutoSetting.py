from someip_py.codec import *


class IdtClimaSrc(SomeIpPayload):

    IdtClimaSrc: Uint8

    def __init__(self):

        self.IdtClimaSrc = Uint8()


class IdtClimaSceneOnOffKls(SomeIpPayload):

    _include_struct_len = True

    ClimateZoneID: Uint8

    ClimateZoneOnOff: Uint8

    def __init__(self):

        self.ClimateZoneID = Uint8()

        self.ClimateZoneOnOff = Uint8()


class IdtClimaSceneOnOff(SomeIpPayload):

    IdtClimaSceneOnOff: IdtClimaSceneOnOffKls

    def __init__(self):

        self.IdtClimaSceneOnOff = IdtClimaSceneOnOffKls()


class IdtClimaRspn(SomeIpPayload):

    IdtClimaRspn: Bool

    def __init__(self):

        self.IdtClimaRspn = Bool()
