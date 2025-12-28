from someip_py.codec import *


class IdtUXCSpeedKls(SomeIpPayload):

    _include_struct_len = True

    UXCSpeedValue: Uint16

    TripMeterUnit: Uint8

    def __init__(self):

        self.UXCSpeedValue = Uint16()

        self.TripMeterUnit = Uint8()


class IdtUXCSpeed(SomeIpPayload):

    IdtUXCSpeed: IdtUXCSpeedKls

    def __init__(self):

        self.IdtUXCSpeed = IdtUXCSpeedKls()
