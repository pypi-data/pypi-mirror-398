from someip_py.codec import *


class IdtPrkgModIncln(SomeIpPayload):

    IdtPrkgModIncln: Uint8

    def __init__(self):

        self.IdtPrkgModIncln = Uint8()
