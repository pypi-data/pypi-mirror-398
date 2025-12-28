from someip_py.codec import *


class IdtWeatherInforKls(SomeIpPayload):

    _include_struct_len = True

    DataValid: Bool

    AmbientTemperature: Int8

    WindDirection: Uint16

    WindPower: Float64

    AirHumidity: Uint8

    WeatherType: Uint8

    UltravioletRay: Uint8

    Day: Bool

    DewPoint: Int8

    def __init__(self):

        self.DataValid = Bool()

        self.AmbientTemperature = Int8()

        self.WindDirection = Uint16()

        self.WindPower = Float64()

        self.AirHumidity = Uint8()

        self.WeatherType = Uint8()

        self.UltravioletRay = Uint8()

        self.Day = Bool()

        self.DewPoint = Int8()


class IdtWeatherInfor(SomeIpPayload):

    IdtWeatherInfor: IdtWeatherInforKls

    def __init__(self):

        self.IdtWeatherInfor = IdtWeatherInforKls()
