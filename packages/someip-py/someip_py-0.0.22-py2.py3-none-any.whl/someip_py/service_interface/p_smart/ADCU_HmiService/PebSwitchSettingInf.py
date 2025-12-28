from someip_py.codec import *


class PebSwitchType(SomeIpPayload):

    PebSwitchType: Uint8

    def __init__(self):

        self.PebSwitchType = Uint8()
