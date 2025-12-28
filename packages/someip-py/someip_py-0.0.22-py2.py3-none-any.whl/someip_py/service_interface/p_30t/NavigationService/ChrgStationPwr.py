from someip_py.codec import *


class IdtChrgStationPwr(SomeIpPayload):

    IdtChrgStationPwr: Uint16

    def __init__(self):

        self.IdtChrgStationPwr = Uint16()
