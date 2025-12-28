from someip_py.codec import *


class IdtRoadCaseDetn(SomeIpPayload):

    IdtRoadCaseDetn: Uint8

    def __init__(self):

        self.IdtRoadCaseDetn = Uint8()
