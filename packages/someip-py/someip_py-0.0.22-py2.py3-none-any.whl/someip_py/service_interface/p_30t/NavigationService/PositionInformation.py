from someip_py.codec import *


class IdtPositionInformationKls(SomeIpPayload):

    _include_struct_len = True

    PosnLat: Float64

    PosnLgt: Float64

    DataValid: Uint8

    CoodinateSys: Uint8

    def __init__(self):

        self.PosnLat = Float64()

        self.PosnLgt = Float64()

        self.DataValid = Uint8()

        self.CoodinateSys = Uint8()


class IdtPositionInformation(SomeIpPayload):

    IdtPositionInformation: IdtPositionInformationKls

    def __init__(self):

        self.IdtPositionInformation = IdtPositionInformationKls()
