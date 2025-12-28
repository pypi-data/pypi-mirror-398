from someip_py.codec import *


class IdtFrntVehDist(SomeIpPayload):

    IdtFrntVehDist: Int16

    def __init__(self):

        self.IdtFrntVehDist = Int16()
