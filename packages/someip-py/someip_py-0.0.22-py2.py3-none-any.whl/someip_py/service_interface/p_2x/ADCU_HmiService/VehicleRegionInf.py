from someip_py.codec import *


class IdtVehicleRegion(SomeIpPayload):

    IdtVehicleRegion: Uint8

    def __init__(self):

        self.IdtVehicleRegion = Uint8()
