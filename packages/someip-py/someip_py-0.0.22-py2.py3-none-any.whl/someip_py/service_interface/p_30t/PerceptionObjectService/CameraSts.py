from someip_py.codec import *


class IdtCameraSts(SomeIpPayload):

    IdtCameraSts: Uint8

    def __init__(self):

        self.IdtCameraSts = Uint8()
