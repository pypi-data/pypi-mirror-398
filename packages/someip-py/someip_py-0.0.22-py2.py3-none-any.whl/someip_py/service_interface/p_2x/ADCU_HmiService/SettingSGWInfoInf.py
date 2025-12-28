from someip_py.codec import *


class OnOff(SomeIpPayload):

    OnOff: Uint8

    def __init__(self):

        self.OnOff = Uint8()
