from someip_py.codec import *


class FaultClearState(SomeIpPayload):

    FaultClearState: Uint8

    def __init__(self):

        self.FaultClearState = Uint8()
