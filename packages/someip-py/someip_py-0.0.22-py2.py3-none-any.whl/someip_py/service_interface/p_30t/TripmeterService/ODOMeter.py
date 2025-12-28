from someip_py.codec import *


class IdtTripmeterKls(SomeIpPayload):

    _include_struct_len = True

    Value: Uint32

    TripMeterUnit: Uint8

    def __init__(self):

        self.Value = Uint32()

        self.TripMeterUnit = Uint8()


class IdtTripmeter(SomeIpPayload):

    IdtTripmeter: IdtTripmeterKls

    def __init__(self):

        self.IdtTripmeter = IdtTripmeterKls()
