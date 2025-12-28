from someip_py.codec import *


class IdtEasyLoadingMod(SomeIpPayload):

    IdtEasyLoadingMod: Uint8

    def __init__(self):

        self.IdtEasyLoadingMod = Uint8()
