from someip_py.codec import *


class IdtTripDistanceKls(SomeIpPayload):

    _include_struct_len = True

    Value: Float32

    TripMeterUnit: Uint8

    def __init__(self):

        self.Value = Float32()

        self.TripMeterUnit = Uint8()


class IdtTripDistance(SomeIpPayload):

    IdtTripDistance: IdtTripDistanceKls

    def __init__(self):

        self.IdtTripDistance = IdtTripDistanceKls()
