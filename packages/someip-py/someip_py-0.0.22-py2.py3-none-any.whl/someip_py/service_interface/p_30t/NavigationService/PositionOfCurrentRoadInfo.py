from someip_py.codec import *


class IdtPositionOfDestinationKls(SomeIpPayload):

    _include_struct_len = True

    PosnLat: Float64

    PosnLgt: Float64

    Adcode: Uint32

    def __init__(self):

        self.PosnLat = Float64()

        self.PosnLgt = Float64()

        self.Adcode = Uint32()


class IdtPositionOfDestination(SomeIpPayload):

    IdtPositionOfDestination: IdtPositionOfDestinationKls

    def __init__(self):

        self.IdtPositionOfDestination = IdtPositionOfDestinationKls()
