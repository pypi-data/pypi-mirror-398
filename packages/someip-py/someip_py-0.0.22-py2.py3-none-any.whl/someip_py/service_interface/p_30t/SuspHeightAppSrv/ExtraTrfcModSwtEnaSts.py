from someip_py.codec import *


class IdtAbleDisableSts(SomeIpPayload):

    IdtAbleDisableSts: Uint8

    def __init__(self):

        self.IdtAbleDisableSts = Uint8()
