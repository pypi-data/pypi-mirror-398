from someip_py.codec import *


class IdtBodyBounceLvl(SomeIpPayload):

    IdtBodyBounceLvl: Uint8

    def __init__(self):

        self.IdtBodyBounceLvl = Uint8()
