from someip_py.codec import *


class IdtCarModSubtyp(SomeIpPayload):

    IdtCarModSubtyp: Uint8

    def __init__(self):

        self.IdtCarModSubtyp = Uint8()
