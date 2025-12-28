from someip_py.codec import *


class IdtClimaHvacRecircCmd(SomeIpPayload):

    IdtClimaHvacRecircCmd: Uint8

    def __init__(self):

        self.IdtClimaHvacRecircCmd = Uint8()
