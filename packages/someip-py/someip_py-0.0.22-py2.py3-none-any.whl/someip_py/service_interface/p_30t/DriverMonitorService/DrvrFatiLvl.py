from someip_py.codec import *


class IdtDrvrFatiLvl(SomeIpPayload):

    IdtDrvrFatiLvl: Uint8

    def __init__(self):

        self.IdtDrvrFatiLvl = Uint8()
