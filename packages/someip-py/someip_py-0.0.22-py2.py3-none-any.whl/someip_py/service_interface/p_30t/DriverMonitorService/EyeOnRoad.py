from someip_py.codec import *


class IdtEyeOnRoad(SomeIpPayload):

    IdtEyeOnRoad: Uint8

    def __init__(self):

        self.IdtEyeOnRoad = Uint8()
