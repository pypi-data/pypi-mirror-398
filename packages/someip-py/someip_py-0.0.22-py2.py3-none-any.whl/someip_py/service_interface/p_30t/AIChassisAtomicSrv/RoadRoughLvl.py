from someip_py.codec import *


class IdtRoadRoughLvl(SomeIpPayload):

    IdtRoadRoughLvl: Uint8

    def __init__(self):

        self.IdtRoadRoughLvl = Uint8()
