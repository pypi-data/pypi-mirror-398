from someip_py.codec import *


class IdtSuspHeiPhySwtst(SomeIpPayload):

    IdtSuspHeiPhySwtst: Uint8

    def __init__(self):

        self.IdtSuspHeiPhySwtst = Uint8()
